from __future__ import annotations

import os
from pathlib import Path


def home() -> Path:
    return Path.home()


def _env_dir(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


def config_dir() -> Path:
    override = os.environ.get("HAS_CONFIG")
    if override:
        return Path(override)
    return home() / ".config" / "harness-api-switcher"


def config_file() -> Path:
    return config_dir() / "config.json"


def backup_dir() -> Path:
    return config_dir() / "backups"


def opencode_auth() -> Path:
    return home() / ".local" / "share" / "opencode" / "auth.json"


def hermes_dir() -> Path:
    if os.name == "nt":
        local = _env_dir("LOCALAPPDATA")
        if local:
            return local / "hermes"
        return home() / "AppData" / "Local" / "hermes"
    xdg = _env_dir("XDG_DATA_HOME")
    if xdg:
        return xdg / "hermes"
    return home() / ".hermes"


def hermes_env() -> Path:
    return hermes_dir() / ".env"


def hermes_config() -> Path:
    return hermes_dir() / "config.yaml"


def claude_dir() -> Path:
    return home() / ".claude"


def claude_settings() -> Path:
    return claude_dir() / "settings.json"


def codex_dir() -> Path:
    return home() / ".codex"


def codex_auth() -> Path:
    return codex_dir() / "auth.json"


def codex_config() -> Path:
    return codex_dir() / "config.toml"
