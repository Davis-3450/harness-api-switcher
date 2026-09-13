from __future__ import annotations

import re
from typing import Any

from .. import paths
from ..backup import write_text
from ..secrets import mask
from .base import Harness
from .envfile import read_env, upsert_env

_MODEL_PROVIDER = re.compile(r"^(\s+)provider:\s*(.*)$")
_MODEL_DEFAULT = re.compile(r"^(\s+)default:\s*(.*)$")


def _looks_secret(key: str) -> bool:
    upper = key.upper()
    return upper.endswith("_API_KEY") or upper.endswith("_TOKEN") or upper.endswith("_KEY")


def _read_model_config(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    in_model = False
    for line in text.splitlines():
        if line.startswith("model:"):
            in_model = True
            continue
        if in_model:
            if line and not line[0].isspace():
                break
            match = _MODEL_PROVIDER.match(line)
            if match:
                result["provider"] = match.group(2).strip().strip('"').strip("'")
                continue
            match = _MODEL_DEFAULT.match(line)
            if match:
                result["model"] = match.group(2).strip().strip('"').strip("'")
    return result


def _set_model_scalar(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    pattern = _MODEL_PROVIDER if key == "provider" else _MODEL_DEFAULT
    model_index = next((i for i, line in enumerate(lines) if line.startswith("model:")), None)

    if model_index is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("model:")
        lines.append(f"  {key}: {value}")
        return "\n".join(lines) + "\n"

    end = len(lines)
    for i in range(model_index + 1, len(lines)):
        if lines[i] and not lines[i][0].isspace():
            end = i
            break

    for i in range(model_index + 1, end):
        match = pattern.match(lines[i])
        if match:
            indent = match.group(1)
            suffix = ""
            if " #" in lines[i]:
                _, comment = lines[i].split(" #", 1)
                suffix = f" #{comment}"
            lines[i] = f"{indent}{key}: {value}{suffix}"
            return "\n".join(lines) + "\n"

    lines.insert(model_index + 1, f"  {key}: {value}")
    return "\n".join(lines) + "\n"


class HermesHarness(Harness):
    id = "hermes"
    label = "hermes"

    def detect(self) -> bool:
        return paths.hermes_env().exists() or paths.hermes_config().exists()

    def current(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        env_path = paths.hermes_env()
        if env_path.exists():
            env = {k: v for k, v in read_env(env_path).items() if v and _looks_secret(k)}
            if env:
                result["env"] = env
        config_path = paths.hermes_config()
        if config_path.exists():
            result.update(_read_model_config(config_path.read_text(encoding="utf-8")))
        return result

    def apply(self, cfg: dict[str, Any], dry_run: bool = False) -> list[str]:
        messages: list[str] = []
        env_updates = {k: v for k, v in (cfg.get("env") or {}).items() if v is not None}
        config_text: str | None = None
        config_path = paths.hermes_config()
        if config_path.exists():
            config_text = config_path.read_text(encoding="utf-8")

        if env_updates:
            env_path = paths.hermes_env()
            for key, value in env_updates.items():
                messages.append(f"env {key} -> {mask(str(value))}")
            if not dry_run:
                text = upsert_env(env_path, {k: str(v) for k, v in env_updates.items()})
                write_text(env_path, text, paths.backup_dir())

        for key in ("provider", "model"):
            value = cfg.get(key)
            if not value:
                continue
            yaml_key = "provider" if key == "provider" else "default"
            messages.append(f"config model.{key} -> {value}")
            if dry_run:
                continue
            if config_text is None:
                config_text = ""
            config_text = _set_model_scalar(config_text, yaml_key, str(value))

        if config_text is not None and not dry_run:
            write_text(config_path, config_text, paths.backup_dir())

        return messages or ["nothing to change"]
