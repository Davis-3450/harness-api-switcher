from __future__ import annotations

from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.text import Text

from .. import config as config_mod
from .. import core, harnesses
from ..models import Config, Profile
from ..secrets import mask
from . import widgets
from .keys import get_key


class Tui:
    def __init__(self, config: Config, console: Console | None = None) -> None:
        self.config = config
        self.console = console or Console()
        self.selected = 0
        self.view = "list"
        self.status: tuple[str, bool] | None = None
        self.pending_changes: list[core.HarnessChange] = []
        self.pending_name: str | None = None
        self.running = True
        self.live: Live | None = None

    # ------------------------------------------------------------------ render
    def render(self) -> RenderableType:
        parts: list[RenderableType] = [widgets.banner()]
        if self.status:
            parts.append(widgets.status_line(*self.status))
        if self.view == "list":
            parts.append(widgets.profile_list(self.config, self.selected))
        elif self.view == "confirm_apply":
            parts.append(widgets.changes_panel(self.pending_changes, "apply preview (dry run)"))
        elif self.view == "confirm_delete" and self.pending_name:
            parts.append(
                widgets.status_line(f"delete profile '{self.pending_name}'? this cannot be undone.", ok=False)
            )
        parts.append(widgets.help_footer(self.view))
        return Group(*parts)

    # ------------------------------------------------------------------- loop
    def run(self) -> None:
        with Live(self.render(), console=self.console, screen=True, auto_refresh=False) as live:
            self.live = live
            while self.running:
                live.update(self.render())
                live.refresh()
                try:
                    key = get_key()
                except KeyboardInterrupt:
                    break
                self.on_key(key)

    # ------------------------------------------------------------------ input
    def _prompt(self, func):
        assert self.live is not None
        self.live.stop()
        try:
            return func()
        finally:
            self.live.start()

    def _ask(self, label: str, password: bool = False, default: str | None = None) -> str:
        def inner() -> str:
            suffix = f" [{mask(default)}]" if default else ""
            value = self.console.input(f"[{widgets.ACCENT}]{label}{suffix}: [/] ", password=password)
            return value.strip() or (default or "")
        return self._prompt(inner)

    def _yesno(self, label: str, default: bool = False) -> bool:
        hint = "Y/n" if default else "y/N"

        def inner() -> bool:
            value = self.console.input(f"[{widgets.ACCENT}]{label} [{hint}]: [/] ").strip().lower()
            if not value:
                return default
            return value.startswith("y")
        return self._prompt(inner)

    # ------------------------------------------------------------------ keys
    def on_key(self, key: str) -> None:
        if self.status:
            self.status = None
        if self.view == "list":
            self._on_list_key(key)
        elif self.view == "confirm_apply":
            self._on_confirm_apply(key)
        elif self.view == "confirm_delete":
            self._on_confirm_delete(key)

    def _on_list_key(self, key: str) -> None:
        names = self.config.profile_names()
        if key in ("up", "k"):
            self.selected = max(0, self.selected - 1)
        elif key in ("down", "j"):
            self.selected = min(max(0, len(names) - 1), self.selected + 1)
        elif key == "q":
            self.running = False
        elif key == "r":
            try:
                self.config = config_mod.load()
                self.selected = min(self.selected, max(0, len(self.config.profile_names()) - 1))
                self.status = ("config reloaded", True)
            except config_mod.ConfigError as exc:
                self.status = (str(exc), False)
        elif key == "enter" and names:
            self._begin_apply(names[self.selected])
        elif key == "n":
            self._new_profile()
        elif key == "e" and names:
            self._edit_profile(names[self.selected])
        elif key == "d" and names:
            self.pending_name = names[self.selected]
            self.view = "confirm_delete"
        elif key == "c":
            self._capture_profile()

    def _on_confirm_apply(self, key: str) -> None:
        if key in ("y", "enter") and self.pending_name:
            name = self.pending_name
            try:
                changes = core.apply_profile(self.config, name, dry_run=False)
                self.status = (f"applied profile '{name}'", True)
            except Exception as exc:  # noqa: BLE001
                changes = self.pending_changes
                self.status = (f"apply failed: {exc}", False)
            self.view = "list"
            self.pending_name = None
            self.pending_changes = changes
        elif key in ("n", "esc"):
            self.view = "list"
            self.pending_name = None
            self.pending_changes = []

    def _on_confirm_delete(self, key: str) -> None:
        if key == "y" and self.pending_name:
            name = self.pending_name
            self.config.profiles.pop(name, None)
            if self.config.active_profile == name:
                self.config.active_profile = None
            config_mod.save(self.config)
            self.selected = min(self.selected, max(0, len(self.config.profile_names()) - 1))
            self.status = (f"deleted profile '{name}'", True)
        self.pending_name = None
        self.view = "list"

    # --------------------------------------------------------------- actions
    def _begin_apply(self, name: str) -> None:
        try:
            self.pending_changes = core.apply_profile(self.config, name, dry_run=True)
            self.pending_name = name
            self.view = "confirm_apply"
        except KeyError as exc:
            self.status = (str(exc.args[0]), False)

    def _new_profile(self) -> None:
        name = self._ask("new profile name")
        if not name:
            return
        if name in self.config.profiles:
            self.status = (f"profile '{name}' already exists", False)
            return
        profile = Profile(name=name)
        self.config.profiles[name] = profile
        self._edit_profile(name)
        config_mod.save(self.config)
        self.status = (f"profile '{name}' saved", True)

    def _capture_profile(self) -> None:
        name = self._ask("capture current setup into profile name")
        if not name:
            return
        overwrite = False
        if name in self.config.profiles:
            overwrite = self._yesno(f"profile '{name}' exists, overwrite?", default=False)
            if not overwrite:
                return
        try:
            core.capture_profile(self.config, name, overwrite=overwrite)
            self.status = (f"captured current credentials into '{name}'", True)
        except KeyError as exc:
            self.status = (str(exc.args[0]), False)

    def _edit_profile(self, name: str) -> None:
        profile = self.config.profiles.get(name)
        if profile is None:
            return
        for harness in harnesses.ALL:
            existing = profile.harnesses.get(harness.id) or {}
            if not self._yesno(f"configure {harness.label}?", default=harness.id in profile.harnesses):
                continue
            cfg = self._edit_harness(harness, existing)
            if cfg:
                profile.harnesses[harness.id] = cfg
            else:
                profile.harnesses.pop(harness.id, None)
        config_mod.save(self.config)

    def _edit_harness(self, harness, existing: dict) -> dict:
        if harness.id == "opencode":
            return self._edit_opencode(existing)
        if harness.id == "hermes":
            return self._edit_hermes(existing)
        if harness.id == "claude":
            return self._edit_claude(existing)
        if harness.id == "codex":
            return self._edit_codex(existing)
        return existing

    def _edit_opencode(self, existing: dict) -> dict:
        providers = dict(existing.get("providers") or {})
        self.console.print(Text("opencode providers (blank name to finish)", style=widgets.MUTED))
        while True:
            name = self._ask("  provider id")
            if not name:
                break
            previous = (providers.get(name) or {}).get("key")
            key = self._ask(f"  {name} api key", password=True, default=previous)
            if key:
                providers[name] = {"type": "api", "key": key}
        return {"providers": providers} if providers else {}

    def _edit_hermes(self, existing: dict) -> dict:
        result: dict = dict(existing)
        provider = self._ask("  model.provider", default=result.get("provider"))
        model = self._ask("  model.default", default=result.get("model"))
        if provider:
            result["provider"] = provider
        if model:
            result["model"] = model
        result["env"] = self._edit_env(existing.get("env") or {})
        return result

    def _edit_claude(self, existing: dict) -> dict:
        return {"env": self._edit_env(existing.get("env") or {})}

    def _edit_codex(self, existing: dict) -> dict:
        result: dict = dict(existing)
        auth = dict(existing.get("auth") or {})
        previous = auth.get("OPENAI_API_KEY")
        key = self._ask("  OPENAI_API_KEY", password=True, default=previous)
        if key:
            auth["OPENAI_API_KEY"] = key
        model = self._ask("  model", default=result.get("model"))
        if auth:
            result["auth"] = auth
        if model:
            result["model"] = model
        return result

    def _edit_env(self, existing: dict) -> dict:
        env = dict(existing)
        self.console.print(Text("env keys (blank name to finish)", style=widgets.MUTED))
        while True:
            key = self._ask("  env KEY")
            if not key:
                break
            value = self._ask(f"  {key} value", password=True, default=env.get(key))
            if value:
                env[key] = value
        return env


def run(config: Config | None = None) -> None:
    run_config = config or config_mod.load()
    Tui(run_config).run()
