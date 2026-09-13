from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CONFIG_VERSION = 1


@dataclass
class Profile:
    name: str
    harnesses: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class Config:
    version: int = CONFIG_VERSION
    active_profile: str | None = None
    profiles: dict[str, Profile] = field(default_factory=dict)

    def profile_names(self) -> list[str]:
        return sorted(self.profiles)

    def get(self, name: str) -> Profile | None:
        return self.profiles.get(name)
