from __future__ import annotations

from pathlib import Path

from harness_api_switcher import paths
from harness_api_switcher.harnesses.hermes import HermesHarness


def test_hermes_env_preserves_comments(sandbox: Path) -> None:
    env_path = paths.hermes_env()
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(
        "# my keys\nOPENCODE_GO_API_KEY=old-value\n\nTERMINAL_TIMEOUT=180\n",
        encoding="utf-8",
    )
    harness = HermesHarness()
    harness.apply({"env": {"OPENCODE_GO_API_KEY": "new-value", "GEMINI_API_KEY": "abc123"}})

    text = env_path.read_text(encoding="utf-8")
    assert "# my keys" in text
    assert "OPENCODE_GO_API_KEY=new-value" in text
    assert "GEMINI_API_KEY=abc123" in text
    assert "TERMINAL_TIMEOUT=180" in text
    assert "old-value" not in text


def test_hermes_config_model(sandbox: Path) -> None:
    config_path = paths.hermes_config()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "model:\n  default: old-model\n  provider: old-provider\n  api_mode: chat\n",
        encoding="utf-8",
    )
    harness = HermesHarness()
    harness.apply({"provider": "opencode-go", "model": "deepseek-v4-flash"})

    text = config_path.read_text(encoding="utf-8")
    assert "provider: opencode-go" in text
    assert "default: deepseek-v4-flash" in text
    assert "api_mode: chat" in text


def test_hermes_capture_filters_secrets(sandbox: Path) -> None:
    env_path = paths.hermes_env()
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(
        "OPENCODE_GO_API_KEY=secret123\nTERMINAL_TIMEOUT=180\n", encoding="utf-8"
    )
    current = HermesHarness().current()
    assert current["env"] == {"OPENCODE_GO_API_KEY": "secret123"}
