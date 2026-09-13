from __future__ import annotations

import json
from typing import Any

from .. import paths
from ..backup import write_text
from ..secrets import mask
from .base import Harness


class OpencodeHarness(Harness):
    id = "opencode"
    label = "opencode"

    def _path(self):
        return paths.opencode_auth()

    def detect(self) -> bool:
        return self._path().exists()

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
        providers: dict[str, Any] = {}
        for name, entry in self._read().items():
            if isinstance(entry, dict) and entry.get("type") == "api" and entry.get("key"):
                providers[name] = {"type": "api", "key": entry["key"]}
        return {"providers": providers} if providers else {}

    def apply(self, cfg: dict[str, Any], dry_run: bool = False) -> list[str]:
        providers = cfg.get("providers") or {}
        if not providers:
            return ["no providers in profile, skipped"]
        data = self._read()
        messages: list[str] = []
        for name, entry in providers.items():
            if not isinstance(entry, dict):
                continue
            if "key" in entry:
                data[name] = {"type": entry.get("type", "api"), "key": entry["key"]}
                messages.append(f"provider {name} -> {mask(str(entry['key']))}")
            elif "access" in entry or "refresh" in entry:
                data[name] = {k: v for k, v in entry.items()}
                messages.append(f"provider {name} -> oauth token")
        if dry_run:
            return messages or ["nothing to change"]
        payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        write_text(self._path(), payload, paths.backup_dir())
        return messages or ["nothing to change"]
