from __future__ import annotations

import json
from typing import Any

from .. import paths
from ..backup import write_text
from ..secrets import mask
from .base import Harness


class ClaudeHarness(Harness):
    id = "claude"
    label = "claude code"

    def _path(self):
        return paths.claude_settings()

    def detect(self) -> bool:
        return paths.claude_dir().exists()

    def _read(self) -> dict[str, Any]:
        path = self._path()
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def current(self) -> dict[str, Any]:
        env = self._read().get("env")
        return {"env": env} if isinstance(env, dict) and env else {}

    def apply(self, cfg: dict[str, Any], dry_run: bool = False) -> list[str]:
        updates = {k: str(v) for k, v in (cfg.get("env") or {}).items() if v is not None}
        if not updates:
            return ["no env in profile, skipped"]
        data = self._read()
        env = data.get("env")
        if not isinstance(env, dict):
            env = {}
        messages = []
        for key, value in updates.items():
            env[key] = value
            messages.append(f"settings.env {key} -> {mask(value)}")
        if dry_run:
            return messages
        data["env"] = env
        payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        write_text(self._path(), payload, paths.backup_dir())
        return messages
