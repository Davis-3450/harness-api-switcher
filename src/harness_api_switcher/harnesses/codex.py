from __future__ import annotations

import json
import re
from typing import Any

from .. import paths
from ..backup import write_text
from ..secrets import mask
from .base import Harness

_MODEL_LINE = re.compile(r'^model\s*=\s*".*?"', re.MULTILINE)


class CodexHarness(Harness):
    id = "codex"
    label = "codex"

    def detect(self) -> bool:
        return paths.codex_dir().exists()

    def _read_auth(self) -> dict[str, Any]:
        path = paths.codex_auth()
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def current(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        auth = self._read_auth()
        if auth.get("OPENAI_API_KEY"):
            result["auth"] = {"OPENAI_API_KEY": auth["OPENAI_API_KEY"]}
        config_path = paths.codex_config()
        if config_path.exists():
            match = _MODEL_LINE.search(config_path.read_text(encoding="utf-8"))
            if match:
                result["model"] = match.group(0).split("=", 1)[1].strip().strip('"')
        return result

    def apply(self, cfg: dict[str, Any], dry_run: bool = False) -> list[str]:
        messages: list[str] = []
        auth_updates = {k: str(v) for k, v in (cfg.get("auth") or {}).items() if v is not None}

        if auth_updates:
            auth = self._read_auth()
            for key, value in auth_updates.items():
                auth[key] = value
                messages.append(f"auth.json {key} -> {mask(value)}")
            if not dry_run:
                payload = json.dumps(auth, indent=2, ensure_ascii=False) + "\n"
                write_text(paths.codex_auth(), payload, paths.backup_dir())

        model = cfg.get("model")
        if model:
            config_path = paths.codex_config()
            text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
            messages.append(f"config.toml model -> {model}")
            if not dry_run:
                if _MODEL_LINE.search(text):
                    text = _MODEL_LINE.sub(f'model = "{model}"', text, count=1)
                else:
                    text = f'model = "{model}"\n' + text
                write_text(config_path, text, paths.backup_dir())

        return messages or ["nothing to change"]
