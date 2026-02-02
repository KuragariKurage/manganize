"""汎用キャラクターseedスクリプト

characters/ ディレクトリ内の全キャラクターをデータベースに登録/更新します。
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.web.manganize_web.models.character import Character
from apps.web.manganize_web.models.database import create_engine, create_session_maker


class CharacterSeedError(Exception):
    """キャラクターseed処理の基底例外"""
    pass


class CharacterYAMLError(CharacterSeedError):
    """YAML読み込みエラー"""
    pass


class CharacterValidationError(CharacterSeedError):
    """キャラクターデータ検証エラー"""
    pass


logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """ログ設定

    Args:
        verbose: 詳細ログ出力を有効にする
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def discover_characters(characters_dir: Path) -> list[str]:
    """characters/ ディレクトリをスキャンし、有効なキャラクターディレクトリを返す

    Args:
        characters_dir: charactersディレクトリのパス

    Returns:
        有効なキャラクター名のリスト（アルファベット順）
    """
    if not characters_dir.exists():
        logger.warning(f"Characters directory not found: {characters_dir}")
        return []

    valid_characters = []

    # characters/ 直下のディレクトリを列挙
    for item in characters_dir.iterdir():
        if not item.is_dir():
            continue

        character_name = item.name
        yaml_file = item / f"{character_name}.yaml"

        # YAML ファイルの存在チェック
        if not yaml_file.exists():
            logger.debug(f"Skipping '{character_name}': YAML file not found")
            continue

        # YAML 読み込み可能性チェック
        try:
            with open(yaml_file, encoding="utf-8") as f:
                yaml.safe_load(f)
            valid_characters.append(character_name)
        except yaml.YAMLError as e:
            logger.warning(f"Skipping '{character_name}': Invalid YAML - {e}")
            continue

    # アルファベット順にソート（処理の再現性のため）
    valid_characters.sort()

    logger.debug(f"Discovered {len(valid_characters)} valid characters: {valid_characters}")
    return valid_characters


def load_character_yaml(character_name: str, base_dir: Path) -> dict:
    """指定したキャラクターのYAMLファイルを読み込む

    Args:
        character_name: キャラクター名
        base_dir: charactersディレクトリのパス

    Returns:
        YAMLデータ（dict）

    Raises:
        FileNotFoundError: YAMLファイルが見つからない
        yaml.YAMLError: YAML解析エラー
    """
    yaml_file = base_dir / character_name / f"{character_name}.yaml"

    if not yaml_file.exists():
        raise FileNotFoundError(f"YAML file not found: {yaml_file}")

    logger.debug(f"Loading YAML: {yaml_file}")

    with open(yaml_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data


def validate_character_yaml(yaml_data: dict, character_name: str) -> None:
    """YAML必須フィールドの検証

    Args:
        yaml_data: YAMLデータ
        character_name: キャラクター名

    Raises:
        CharacterValidationError: 必須フィールド欠損
    """
    required_fields = ["name", "personality", "speech_style"]
    missing = [f for f in required_fields if f not in yaml_data]

    if missing:
        raise CharacterValidationError(
            f"Missing required fields: {', '.join(missing)}"
        )

    # speech_style の構造検証
    if not isinstance(yaml_data["speech_style"], dict):
        raise CharacterValidationError("speech_style must be a dict")

    # nickname のデフォルト値設定
    if "nickname" not in yaml_data:
        logger.warning(
            f"Character '{character_name}': 'nickname' not found, using display name"
        )
        yaml_data["nickname"] = yaml_data["name"]

    # attributes のデフォルト値設定
    if "attributes" not in yaml_data:
        logger.warning(
            f"Character '{character_name}': 'attributes' not found, using empty list"
        )
        yaml_data["attributes"] = []


def build_reference_images(
    character_name: str, images_data: dict, base_dir: Path
) -> dict | None:
    """YAMLのimagesセクションから reference_images を構築

    Args:
        character_name: キャラクター名
        images_data: YAMLのimagesセクション
        base_dir: charactersディレクトリのパス

    Returns:
        reference_images dict（portrait, full_body）または None
    """
    if not images_data:
        logger.warning(f"Character '{character_name}': No images section in YAML")
        return None

    reference_images = {}

    # portrait 画像
    if "portrait" in images_data:
        portrait_rel_path = Path(images_data["portrait"])
        portrait_abs_path = base_dir / character_name / portrait_rel_path

        if portrait_abs_path.exists():
            # プロジェクトルートからの相対パスに変換
            reference_images["portrait"] = str(
                Path("characters") / character_name / portrait_rel_path
            )
            logger.debug(f"Portrait image: {reference_images['portrait']}")
        else:
            logger.warning(
                f"Character '{character_name}': Portrait image not found - {portrait_abs_path}"
            )

    # full_body 画像
    if "full_body" in images_data:
        full_body_rel_path = Path(images_data["full_body"])
        full_body_abs_path = base_dir / character_name / full_body_rel_path

        if full_body_abs_path.exists():
            # プロジェクトルートからの相対パスに変換
            reference_images["full_body"] = str(
                Path("characters") / character_name / full_body_rel_path
            )
            logger.debug(f"Full body image: {reference_images['full_body']}")
        else:
            logger.warning(
                f"Character '{character_name}': Full body image not found - {full_body_abs_path}"
            )

    if not reference_images:
        logger.warning(f"Character '{character_name}': No valid images found")
        return None

    return reference_images


async def upsert_character(
    session,
    character_name: str,
    yaml_data: dict,
    is_default: bool = False,
    force_update: bool = False,
) -> tuple[Character, bool]:
    """キャラクターをDBにinsertまたはupdate

    Args:
        session: データベースセッション
        character_name: キャラクター名（DB primary key）
        yaml_data: YAMLデータ
        is_default: デフォルトキャラクターに設定するか
        force_update: 既存キャラクターを強制更新するか

    Returns:
        (Character, created: bool) - createdはTrueなら新規作成、Falseなら更新
    """
    existing = await session.get(Character, character_name)

    if existing:
        # 既存キャラクターの更新
        logger.debug(f"Character '{character_name}' exists, updating")

        # is_default の扱い: 既存がデフォルトなら維持（明示的に指定されない限り）
        if existing.is_default and not is_default:
            is_default = existing.is_default

        # フィールド更新
        existing.display_name = yaml_data["name"]
        existing.nickname = yaml_data.get("nickname", yaml_data["name"])
        existing.attributes = yaml_data.get("attributes", [])
        existing.personality = yaml_data["personality"]
        existing.speech_style = yaml_data["speech_style"]
        existing.reference_images = yaml_data.get("reference_images")
        existing.is_default = is_default

        return existing, False

    else:
        # 新規作成
        logger.debug(f"Character '{character_name}' does not exist, creating")

        character = Character(
            name=character_name,
            display_name=yaml_data["name"],
            nickname=yaml_data.get("nickname", yaml_data["name"]),
            attributes=yaml_data.get("attributes", []),
            personality=yaml_data["personality"],
            speech_style=yaml_data["speech_style"],
            reference_images=yaml_data.get("reference_images"),
            is_default=is_default,
        )

        session.add(character)
        return character, True


async def seed_character(
    session,
    character_name: str,
    characters_dir: Path,
    force_update: bool = False,
    default_character: str | None = None,
    dry_run: bool = False,
) -> bool:
    """単一キャラクターをseed

    Args:
        session: データベースセッション
        character_name: キャラクター名
        characters_dir: charactersディレクトリのパス
        force_update: 既存キャラクターを強制更新するか
        default_character: デフォルトキャラクターに設定するキャラクター名
        dry_run: dry-runモード（DB変更なし）

    Returns:
        成功時 True、失敗時 False
    """
    logger.info(f"Processing character '{character_name}'")

    try:
        # YAML読み込み
        yaml_data = load_character_yaml(character_name, characters_dir)

        # データ検証
        validate_character_yaml(yaml_data, character_name)

        # 画像パス構築
        images_data = yaml_data.get("images", {})
        reference_images = build_reference_images(
            character_name, images_data, characters_dir
        )
        yaml_data["reference_images"] = reference_images

        # デフォルトキャラクターの判定
        is_default = character_name == default_character

        if dry_run:
            # Dry-runモード: プレビューのみ
            logger.info(f"[DRY RUN] Would create/update character '{character_name}':")
            logger.info(f"  Display Name: {yaml_data['name']}")
            logger.info(f"  Nickname: {yaml_data.get('nickname', yaml_data['name'])}")
            logger.info(f"  Attributes: {yaml_data.get('attributes', [])}")
            logger.info(f"  Images: {reference_images}")
            logger.info(f"  Default: {is_default}")
            return True

        # DB upsert
        character, created = await upsert_character(
            session,
            character_name,
            yaml_data,
            is_default=is_default,
            force_update=force_update,
        )

        action = "created" if created else "updated"
        logger.info(f"✅ Character '{character_name}' {action} successfully")
        return True

    except FileNotFoundError:
        logger.error(f"❌ Character '{character_name}': YAML file not found")
        return False
    except yaml.YAMLError as e:
        logger.error(f"❌ Character '{character_name}': Invalid YAML - {e}")
        return False
    except CharacterValidationError as e:
        logger.error(f"❌ Character '{character_name}': Validation error - {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Character '{character_name}': Unexpected error - {e}")
        return False


async def seed_all_characters(
    session,
    character_names: list[str] | None,
    characters_dir: Path,
    force_update: bool = False,
    default_character: str | None = None,
    dry_run: bool = False,
) -> dict:
    """複数キャラクターをバッチseed

    Args:
        session: データベースセッション
        character_names: キャラクター名リスト（None の場合は全キャラクター自動検出）
        characters_dir: charactersディレクトリのパス
        force_update: 既存キャラクターを強制更新するか
        default_character: デフォルトキャラクターに設定するキャラクター名
        dry_run: dry-runモード（DB変更なし）

    Returns:
        統計情報 dict: {"created": [...], "updated": [...], "failed": [...]}
    """
    # 自動検出
    if character_names is None:
        character_names = discover_characters(characters_dir)
        logger.info(f"Discovered {len(character_names)} characters: {', '.join(character_names)}")

    if not character_names:
        logger.warning("No characters to process")
        return {"created": [], "updated": [], "failed": []}

    results = {"created": [], "updated": [], "failed": []}

    for character_name in character_names:
        try:
            # 処理前の状態確認
            existing = await session.get(Character, character_name)
            is_update = existing is not None

            # キャラクターseed
            success = await seed_character(
                session,
                character_name,
                characters_dir,
                force_update=force_update,
                default_character=default_character,
                dry_run=dry_run,
            )

            if success:
                if dry_run:
                    # Dry-runモードでは統計をスキップ
                    continue

                if is_update:
                    results["updated"].append(character_name)
                else:
                    results["created"].append(character_name)
            else:
                results["failed"].append(character_name)

        except Exception as e:
            logger.error(f"❌ Unexpected error for '{character_name}': {e}")
            results["failed"].append(character_name)
            continue

    # コミット（dry-runモードではスキップ）
    if not dry_run:
        await session.commit()
        logger.debug("Database changes committed")

    return results


async def set_default_character(session, character_name: str) -> None:
    """指定したキャラクターをデフォルトに設定

    Args:
        session: データベースセッション
        character_name: デフォルトに設定するキャラクター名

    Raises:
        ValueError: キャラクターが存在しない場合
    """
    from sqlalchemy import select

    logger.info(f"Setting default character to '{character_name}'")

    # 全キャラクターをFalseに
    result = await session.execute(select(Character))
    for char in result.scalars():
        char.is_default = False

    # 指定キャラクターをTrueに
    target = await session.get(Character, character_name)
    if not target:
        raise ValueError(f"Character '{character_name}' not found")

    target.is_default = True
    await session.commit()

    logger.info(f"✅ Character '{character_name}' is now the default")


def print_summary(results: dict, dry_run: bool = False) -> None:
    """統計サマリーを出力

    Args:
        results: 統計情報 dict
        dry_run: dry-runモード
    """
    if dry_run:
        logger.info("\n=== Dry Run Complete ===")
        logger.info("No changes were made to the database")
        return

    logger.info("\n=== Seed Summary ===")

    if results["created"]:
        logger.info(f"Created: {len(results['created'])} ({', '.join(results['created'])})")
    else:
        logger.info("Created: 0")

    if results["updated"]:
        logger.info(f"Updated: {len(results['updated'])} ({', '.join(results['updated'])})")
    else:
        logger.info("Updated: 0")

    if results["failed"]:
        logger.info(f"Failed: {len(results['failed'])} ({', '.join(results['failed'])})")
    else:
        logger.info("Failed: 0")

    total = len(results["created"]) + len(results["updated"]) + len(results["failed"])
    logger.info(f"Total: {total}")


async def main() -> None:
    """メインエントリポイント"""
    # 引数パース
    parser = argparse.ArgumentParser(
        description="汎用キャラクターseedスクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "characters",
        nargs="*",
        help="キャラクター名（指定しない場合は全キャラクター）",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="既存キャラクターを強制更新",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細ログ出力",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の変更なしでプレビュー",
    )

    parser.add_argument(
        "--default",
        metavar="CHARACTER",
        help="デフォルトキャラクターを変更",
    )

    args = parser.parse_args()

    # ログ設定
    setup_logging(verbose=args.verbose)

    logger.info("Starting character seed process")

    # charactersディレクトリ
    characters_dir = Path("characters")

    if not characters_dir.exists():
        logger.error(f"Characters directory not found: {characters_dir}")
        sys.exit(1)

    # DB接続
    engine = create_engine()
    session_maker = create_session_maker(engine)

    try:
        async with session_maker() as session:
            # キャラクター名リスト（引数で指定されていない場合はNone）
            character_names = args.characters if args.characters else None

            # デフォルトキャラクター変更（--default オプション使用時）
            if args.default:
                await set_default_character(session, args.default)
                # デフォルト変更のみの場合は終了
                if not character_names:
                    return

            # キャラクターseed
            results = await seed_all_characters(
                session,
                character_names,
                characters_dir,
                force_update=args.force,
                default_character=args.default,
                dry_run=args.dry_run,
            )

            # サマリー出力
            print_summary(results, dry_run=args.dry_run)

            # エラーがあれば終了コード1
            if results["failed"]:
                sys.exit(1)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
