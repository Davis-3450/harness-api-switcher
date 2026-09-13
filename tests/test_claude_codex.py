from __future__ import annotations

import json
from pathlib import Path

from harness_api_switcher import paths
from harness_api_switcher.harnesses.claude import ClaudeHarness
from harness_api_switcher.harnesses.codex import CodexHarness


def test_claude_apply_merges_env(sandbox: Path, write_json) -> None:
    write_json(paths.claude_settings(), {"model": "opus[1m]", "env": {"FOO": "bar"}})
    ClaudeHarness().apply({"env": {"ANTHROPIC_API_KEY": "sk-ant-1234567890"}})

    data = json.loads(paths.claude_settings().read_text(encoding="utf-8"))
    assert data["model"] == "opus[1m]"
    assert data["env"]["FOO"] == "bar"
    assert data["env"]["ANTHROPIC_API_KEY"] == "sk-ant-1234567890"


def test_codex_apply_preserves_tokens(sandbox: Path, write_json) -> None:
    write_json(paths.codex_auth(), {"OPENAI_API_KEY": "", "tokens": {"access_token": "tok"}})
    paths.codex_config().write_text('model = "old"\nother = true\n', encoding="utf-8")

    CodexHarness().apply({"auth": {"OPENAI_API_KEY": "sk-new-123456"}, "model": "gpt-5.6-luna"})

    data = json.loads(paths.codex_auth().read_text(encoding="utf-8"))
    assert data["OPENAI_API_KEY"] == "sk-new-123456"
    assert data["tokens"]["access_token"] == "tok"
    assert 'model = "gpt-5.6-luna"' in paths.codex_config().read_text(encoding="utf-8")
