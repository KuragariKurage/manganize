"""CLI flag handling — provider validation surfaces before the pipeline starts."""

from unittest.mock import patch

from typer.testing import CliRunner

from manganize_core.cli import app


class TestTopicCommandImageProvider:
    def test_invalid_image_provider_exits_with_japanese_error(self, monkeypatch):
        monkeypatch.delenv("IMAGE_PROVIDER", raising=False)
        runner = CliRunner()

        result = runner.invoke(app, ["topic", "test", "--image-provider", "azure"])

        assert result.exit_code == 1
        assert "不明な画像プロバイダー" in result.stderr

    def test_openai_emits_warning_before_pipeline_runs(self, monkeypatch):
        monkeypatch.delenv("IMAGE_PROVIDER", raising=False)
        runner = CliRunner()

        # Short-circuit the pipeline: return None so the command exits with code 1
        # after the warning has already been emitted.
        with patch("manganize_core.cli._run_generation", return_value=None):
            result = runner.invoke(app, ["topic", "test", "--image-provider", "openai"])

        assert "OpenAI 画像プロバイダー選択中" in result.stderr
