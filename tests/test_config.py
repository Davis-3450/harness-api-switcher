from __future__ import annotations

from pathlib import Path

from harness_api_switcher import config as config_mod, paths
from harness_api_switcher.models import Profile


def test_roundtrip(sandbox: Path) -> None:
    config = config_mod.load()
    config.profiles["work"] = Profile(
        name="work", harnesses={"claude": {"env": {"ANTHROPIC_API_KEY": "sk-ant-xyz"}}}
    )
    config.active_profile = "work"
    config_mod.save(config)

    reloaded = config_mod.load()
    assert reloaded.active_profile == "work"
    assert reloaded.profiles["work"].harnesses["claude"]["env"]["ANTHROPIC_API_KEY"] == "sk-ant-xyz"
    assert paths.config_file().exists()


def test_apply_sets_active(sandbox: Path) -> None:
    from harness_api_switcher import core

    config = config_mod.load()
    config.profiles["a"] = Profile(name="a", harnesses={})
    config_mod.save(config)

    core.apply_profile(config, "a")
    assert config_mod.load().active_profile == "a"
