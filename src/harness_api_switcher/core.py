from __future__ import annotations

from dataclasses import dataclass

from . import config as config_mod
from . import harnesses
from .models import Config, Profile


@dataclass
class HarnessChange:
    harness_id: str
    label: str
    messages: list[str]


def _apply_one(harness_id: str, cfg: dict, dry_run: bool) -> HarnessChange:
    harness = harnesses.get(harness_id)
    if harness is None:
        return HarnessChange(harness_id, harness_id, ["unknown harness, skipped"])
    return HarnessChange(harness_id, harness.label, harness.apply(cfg, dry_run=dry_run))


def apply_profile(config: Config, name: str, dry_run: bool = False) -> list[HarnessChange]:
    profile = config.get(name)
    if profile is None:
        raise KeyError(f"profile '{name}' not found")
    changes = [
        _apply_one(harness_id, cfg, dry_run)
        for harness_id, cfg in profile.harnesses.items()
    ]
    if not dry_run:
        config.active_profile = name
        config_mod.save(config)
    return changes


def capture_profile(config: Config, name: str, overwrite: bool = False) -> Profile:
    if name in config.profiles and not overwrite:
        raise KeyError(f"profile '{name}' already exists")
    data = {}
    for harness in harnesses.ALL:
        if not harness.detect():
            continue
        current = harness.current()
        if current:
            data[harness.id] = current
    profile = Profile(name=name, harnesses=data)
    config.profiles[name] = profile
    config_mod.save(config)
    return profile
