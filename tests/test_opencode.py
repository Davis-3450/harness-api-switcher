from __future__ import annotations

import json
from pathlib import Path

from harness_api_switcher import paths
from harness_api_switcher.harnesses.opencode import OpencodeHarness


def test_opencode_apply_preserves_oauth(sandbox: Path, write_json) -> None:
    write_json(
        paths.opencode_auth(),
        {
            "github-copilot": {"type": "oauth", "refresh": "gho_xxx", "access": "gho_yyy"},
            "opencode-go": {"type": "api", "key": "old"},
        },
    )
    harness = OpencodeHarness()
    messages = harness.apply({"providers": {"opencode-go": {"type": "api", "key": "new-key-value"}}})

    data = json.loads(paths.opencode_auth().read_text(encoding="utf-8"))
    assert data["github-copilot"]["refresh"] == "gho_xxx"
    assert data["opencode-go"]["key"] == "new-key-value"
    assert messages and "opencode-go" in messages[0]


def test_opencode_capture_skips_oauth(sandbox: Path, write_json) -> None:
    write_json(
        paths.opencode_auth(),
        {
            "github-copilot": {"type": "oauth", "refresh": "gho_xxx"},
            "opencode-go": {"type": "api", "key": "secret-key"},
        },
    )
    current = OpencodeHarness().current()
    assert current == {"providers": {"opencode-go": {"type": "api", "key": "secret-key"}}}


def test_opencode_apply_creates_backup(sandbox: Path, write_json) -> None:
    write_json(paths.opencode_auth(), {"opencode-go": {"type": "api", "key": "old"}})
    OpencodeHarness().apply({"providers": {"opencode-go": {"type": "api", "key": "new"}}})
    backups = list(paths.backup_dir().glob("auth.json.bak.*"))
    assert backups, "expected a backup of the previous auth.json"
