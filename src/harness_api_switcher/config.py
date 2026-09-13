from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from . import paths
from .backup import backup_file, harden_permissions
from .models import CONFIG_VERSION, Config, Profile


class ConfigError(Exception):
    pass


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass


def config_to_dict(config: Config) -> dict[str, Any]:
    return {
        "version": CONFIG_VERSION,
        "active_profile": config.active_profile,
        "profiles": {
            name: {"harnesses": profile.harnesses}
            for name, profile in config.profiles.items()
        },
    }


def dict_to_config(data: dict[str, Any]) -> Config:
    if not isinstance(data, dict):
        raise ConfigError("config root must be a JSON object")
    profiles: dict[str, Profile] = {}
    raw_profiles = data.get("profiles") or {}
    if not isinstance(raw_profiles, dict):
        raise ConfigError("'profiles' must be an object")
    for name, body in raw_profiles.items():
        if not isinstance(body, dict):
            raise ConfigError(f"profile '{name}' must be an object")
        harnesses = body.get("harnesses") or {}
        if not isinstance(harnesses, dict):
            raise ConfigError(f"profile '{name}'.harnesses must be an object")
        profiles[name] = Profile(name=name, harnesses=harnesses)
    active = data.get("active_profile")
    if active is not None and not isinstance(active, str):
        raise ConfigError("'active_profile' must be a string or null")
    return Config(
        version=int(data.get("version", CONFIG_VERSION)),
        active_profile=active,
        profiles=profiles,
    )


def load(path: Path | None = None) -> Config:
    path = path or paths.config_file()
    if not path.exists():
        return Config()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {path}: {exc}") from exc
    return dict_to_config(raw)


def save(config: Config, path: Path | None = None) -> Path:
    path = path or paths.config_file()
    _ensure_dir(path.parent)
    payload = json.dumps(config_to_dict(config), indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        backup_file(path, paths.backup_dir())
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)
    harden_permissions(path)
    return path
