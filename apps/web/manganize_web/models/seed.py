"""Seed database with default character"""

import asyncio
from pathlib import Path

import yaml

from manganize_web.models.character import Character
from manganize_web.models.database import create_engine, create_session_maker


async def seed_default_character(session) -> None:
    """
    Load and insert the default 'kurage' character from YAML.

    Args:
        session: SQLAlchemy async session
    """
    # Load kurage.yaml
    kurage_file = Path("characters/kurage/kurage.yaml")

    if not kurage_file.exists():
        print(f"Warning: {kurage_file} not found. Skipping seed.")
        return

    with open(kurage_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Extract data from kurage.yaml structure
    display_name = data.get("name", "くらがりくらげ")
    nickname = data.get("nickname", "くらげちゃん")
    attributes = data.get("attributes", [])
    personality = data.get("personality", "")
    speech_style = data.get("speech_style", {})

    # Build reference_images from images section
    images_data = data.get("images", {})
    reference_images = None
    if images_data:
        # Convert relative paths to absolute from project root
        reference_images = {}
        if "portrait" in images_data:
            reference_images["portrait"] = str(
                Path("characters/kurage") / images_data["portrait"]
            )
        if "full_body" in images_data:
            reference_images["full_body"] = str(
                Path("characters/kurage") / images_data["full_body"]
            )

    # Check if character already exists
    existing = await session.get(Character, "kurage")

    if existing:
        print("Character 'kurage' already exists. Skipping.")
        return

    # Create new character
    character = Character(
        name="kurage",
        display_name=display_name,
        nickname=nickname,
        attributes=attributes,
        personality=personality,
        speech_style=speech_style,
        reference_images=reference_images,
        is_default=True,
    )

    session.add(character)
    await session.commit()

    print(
        f"✅ Default character '{character.name}' ({character.display_name}) seeded successfully."
    )


async def main() -> None:
    """Main seed function"""
    # Create engine and session maker for standalone script
    engine = create_engine()
    session_maker = create_session_maker(engine)

    try:
        async with session_maker() as session:
            await seed_default_character(session)
    finally:
        # Properly dispose of the async engine
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
