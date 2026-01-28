from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class SpeechStyle(BaseModel):
    """キャラクターの話し方・口調の詳細設定"""

    tone: str = Field(description="基本的な話し方のトーン")
    patterns: list[str] = Field(
        description="語尾パターンのリスト（例：「～かも」「～だね」）"
    )
    examples: list[str] = Field(
        default_factory=list, description="セリフの具体例（オプション）"
    )
    forbidden: list[str] = Field(description="禁止事項のリスト")


class BaseCharacter(BaseModel):
    """キャラクターの基本情報を保持するモデル"""

    name: str = Field(description="キャラクターの名前")
    nickname: str = Field(description="キャラクターの愛称")
    attributes: list[str] = Field(description="キャラクターの属性")
    personality: str = Field(description="キャラクターの性格")

    speech_style: SpeechStyle = Field(description="話し方・口調の詳細設定")

    portrait: bytes | Path = Field(description="キャラクターの顔アップ画像")
    full_body: bytes | Path = Field(description="キャラクターの全身画像")

    @field_validator("portrait", "full_body", mode="before")
    @classmethod
    def resolve_image_path(cls, v: Any) -> bytes | Path:
        """画像パスが文字列の場合、Pathオブジェクトに変換"""
        if isinstance(v, str):
            return Path(v)
        return v

    def get_portrait_bytes(self) -> bytes:
        """顔アップ画像をbytesとして取得"""
        if isinstance(self.portrait, bytes):
            return self.portrait
        return self.portrait.read_bytes()

    def get_full_body_bytes(self) -> bytes:
        """全身画像をbytesとして取得"""
        if isinstance(self.full_body, bytes):
            return self.full_body
        return self.full_body.read_bytes()

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> "BaseCharacter":
        """YAMLファイルからキャラクターを読み込む

        Args:
            yaml_path: YAMLファイルのパス

        Returns:
            BaseCharacter: 読み込まれたキャラクター

        Raises:
            FileNotFoundError: YAMLファイルが見つからない場合
            ValueError: YAML形式が不正な場合
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Character file not found: {yaml_path}")

        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # 画像パスを解決（YAMLファイルからの相対パス）
        yaml_dir = yaml_path.parent
        if "images" in data:
            if "portrait" in data["images"]:
                data["images"]["portrait"] = yaml_dir / data["images"]["portrait"]
            if "full_body" in data["images"]:
                data["images"]["full_body"] = yaml_dir / data["images"]["full_body"]

        # データを展開
        character_data = {
            "name": data["name"],
            "nickname": data.get("nickname", data["name"]),
            "attributes": data["attributes"],
            "personality": data["personality"],
            "speech_style": data["speech_style"],
            "portrait": data["images"]["portrait"],
            "full_body": data["images"]["full_body"],
        }

        return cls(**character_data)


class KurageChan(BaseCharacter):
    """激カワえんじにゃくらげちゃん"""

    def __init__(self, **data: Any):
        # デフォルト値を設定
        assets_dir = Path(__file__).parents[3] / "characters" / "kurage" / "assets"
        super().__init__(
            name="くらがりくらげ",
            nickname="くらげちゃん",
            attributes=["ハイスキルエンジニア", "技術オタク"],
            personality="基本はクールでダウナーだが、技術的な話題には目を輝かせます。",
            speech_style=SpeechStyle(
                tone="声のトーンが低めの、落ち着いた現代の女の子",
                patterns=[
                    "～かも",
                    "～だね",
                    "……なるほど",
                    "～らしいよ",
                ],
                examples=[
                    "これ、結構面白いかも",
                    "なるほどね……",
                    "そういうことだったんだ",
                ],
                forbidden=[
                    "「～だ」「～である」等の堅苦しい断定",
                    "おじさん構文",
                    "博士語調（～じゃ、～わい）",
                    "過度にハイテンションなアイドル口調",
                ],
            ),
            portrait=assets_dir / "kurage.png",
            full_body=assets_dir / "kurage2.png",
            **data,
        )
