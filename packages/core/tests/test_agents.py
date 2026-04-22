"""Agent construction surfaces provider misconfig at init time, not mid-retry."""

from unittest.mock import MagicMock

import pytest


class TestManganizeAgentProviderResolution:
    def test_invalid_env_var_raises_at_construction(self, monkeypatch):
        monkeypatch.setenv("IMAGE_PROVIDER", "azure")

        from manganize_core.agents import ManganizeAgent

        with pytest.raises(ValueError, match="不明な画像プロバイダー"):
            ManganizeAgent(
                researcher_llm=MagicMock(),
                scenario_writer_llm=MagicMock(),
            )
