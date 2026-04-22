"""Tests for image generation dispatch and provider resolution."""

from unittest.mock import MagicMock, patch

import pytest

from manganize_core.image_generation import (
    ImageProvider,
    generate_image,
    resolve_image_provider,
)


class TestResolveImageProvider:
    def test_cli_flag_has_highest_priority(self, monkeypatch):
        monkeypatch.setenv("IMAGE_PROVIDER", "google")
        assert resolve_image_provider(cli_flag="openai") == ImageProvider.OPENAI

    def test_env_var_used_when_cli_flag_absent(self, monkeypatch):
        monkeypatch.setenv("IMAGE_PROVIDER", "openai")
        assert resolve_image_provider() == ImageProvider.OPENAI

    def test_defaults_to_google(self, monkeypatch):
        monkeypatch.delenv("IMAGE_PROVIDER", raising=False)
        assert resolve_image_provider() == ImageProvider.GOOGLE

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.delenv("IMAGE_PROVIDER", raising=False)
        assert resolve_image_provider(cli_flag="OpenAI") == ImageProvider.OPENAI

    def test_unknown_provider_raises_value_error(self, monkeypatch):
        monkeypatch.delenv("IMAGE_PROVIDER", raising=False)
        with pytest.raises(ValueError, match="不明な画像プロバイダー"):
            resolve_image_provider(cli_flag="azure")


class TestGenerateImageDispatch:
    def test_dispatch_to_google(self):
        character = MagicMock()
        with (
            patch(
                "manganize_core.image_generation._generate_google",
                return_value=b"google-bytes",
            ) as mock_google,
            patch("manganize_core.image_generation._generate_openai") as mock_openai,
        ):
            result = generate_image("content", character, ImageProvider.GOOGLE)

        assert result == b"google-bytes"
        mock_google.assert_called_once_with("content", character)
        mock_openai.assert_not_called()

    def test_dispatch_to_openai(self):
        character = MagicMock()
        with (
            patch(
                "manganize_core.image_generation._generate_openai",
                return_value=b"openai-bytes",
            ) as mock_openai,
            patch("manganize_core.image_generation._generate_google") as mock_google,
        ):
            result = generate_image("content", character, ImageProvider.OPENAI)

        assert result == b"openai-bytes"
        mock_openai.assert_called_once_with("content", character)
        mock_google.assert_not_called()
