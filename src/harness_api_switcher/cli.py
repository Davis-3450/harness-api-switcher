from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from rich.console import Console

from . import config as config_mod
from . import core, harnesses, paths
from .backup import backup_file
from .models import Config
from .secrets import mask
from .tui import app as tui_app
from .tui import widgets

console = Console()


def _mask_tree(value):
    if isinstance(value, dict):
        return {k: _mask_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_mask_tree(v) for v in value]
    if isinstance(value, str) and len(value) >= 12:
        return mask(value)
    return value


def _load() -> Config:
    try:
        return config_mod.load()
    except config_mod.ConfigError as exc:
        console.print(f"[bright_red]{exc}[/bright_red]")
        raise SystemExit(1)


def cmd_list(args: argparse.Namespace) -> int:
    config = _load()
    console.print(widgets.profile_list(config, selected=-1))
    console.print(f"[grey62]config: {paths.config_file()}[/grey62]")
    return 0


def cmd_tui(args: argparse.Namespace) -> int:
    tui_app.run(_load())
    return 0


def cmd_use(args: argparse.Namespace) -> int:
    config = _load()
    try:
        changes = core.apply_profile(config, args.profile, dry_run=args.dry_run)
    except KeyError as exc:
        console.print(f"[bright_red]{exc.args[0]}[/bright_red]")
        return 1
    title = "dry run" if args.dry_run else f"applied profile '{args.profile}'"
    console.print(widgets.changes_panel(changes, title))
    return 0


def cmd_current(args: argparse.Namespace) -> int:
    config = _load()
    if not config.active_profile:
        console.print("[grey62]no active profile[/grey62]")
        return 0
    console.print(f"[bold bright_cyan]active profile:[/bold bright_cyan] {config.active_profile}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    config = _load()
    profile = config.get(args.profile)
    if profile is None:
        console.print(f"[bright_red]profile '{args.profile}' not found[/bright_red]")
        return 1
    body = profile.harnesses if args.reveal else _mask_tree(profile.harnesses)
    console.print_json(json.dumps(body, indent=2))
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    config = _load()
    if args.profile in config.profiles and not args.force:
        console.print(
            f"[bright_red]profile '{args.profile}' exists, use --force to overwrite[/bright_red]"
        )
        return 1
    try:
        profile = core.capture_profile(config, args.profile, overwrite=args.force)
    except KeyError as exc:
        console.print(f"[bright_red]{exc.args[0]}[/bright_red]")
        return 1
    console.print(
        f"[green]captured into '{args.profile}':[/green] {', '.join(profile.harnesses) or '(empty)'}"
    )
    return 0


def cmd_edit(args: argparse.Namespace) -> int:
    path = config_mod.save(_load()) if not paths.config_file().exists() else paths.config_file()
    editor = os.environ.get("EDITOR") or ("notepad" if os.name == "nt" else "nano")
    try:
        subprocess.run([editor, str(path)], check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        console.print(f"[bright_red]failed to open editor: {exc}[/bright_red]")
        return 1
    try:
        config_mod.load(path)
    except config_mod.ConfigError as exc:
        console.print(f"[bright_red]config invalid after edit: {exc}[/bright_red]")
        return 1
    console.print(f"[green]saved[/green] {path}")
    return 0


def cmd_path(args: argparse.Namespace) -> int:
    console.print(str(paths.config_file()))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    config = _load()
    console.print(f"[bold]config:[/bold] {paths.config_file()} (exists={paths.config_file().exists()})")
    for harness in harnesses.ALL:
        detected = harness.detect()
        console.print(
            f"  [bold]{harness.label}[/bold]: detected={detected}, "
            f"keys={list(harness.current()) or '-'}"
        )
    console.print(f"[bold]profiles:[/bold] {', '.join(config.profile_names()) or '-'}")
    console.print(f"[bold]active:[/bold] {config.active_profile or '-'}")
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    config_path = paths.config_file()
    if not config_path.exists():
        console.print("[grey62]no config to back up[/grey62]")
        return 0
    backup = backup_file(config_path, paths.backup_dir())
    console.print(f"[green]backup:[/green] {backup}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="has",
        description="Beautiful Rich TUI to switch API keys per profile across coding harnesses.",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="list profiles").set_defaults(func=cmd_list)
    sub.add_parser("tui", help="launch interactive TUI (default)").set_defaults(func=cmd_tui)

    use = sub.add_parser("use", help="apply a profile")
    use.add_argument("profile")
    use.add_argument("--dry-run", action="store_true")
    use.set_defaults(func=cmd_use)

    sub.add_parser("current", help="show active profile").set_defaults(func=cmd_current)

    show = sub.add_parser("show", help="print a profile")
    show.add_argument("profile")
    show.add_argument("--reveal", action="store_true", help="show secrets unmasked")
    show.set_defaults(func=cmd_show)

    capture = sub.add_parser("capture", help="capture current harness credentials into a profile")
    capture.add_argument("profile")
    capture.add_argument("--force", action="store_true")
    capture.set_defaults(func=cmd_capture)

    edit = sub.add_parser("edit", help="open the config in $EDITOR")
    edit.set_defaults(func=cmd_edit)

    sub.add_parser("path", help="print config path").set_defaults(func=cmd_path)
    sub.add_parser("doctor", help="diagnose config and harnesses").set_defaults(func=cmd_doctor)
    sub.add_parser("backup", help="back up the config file").set_defaults(func=cmd_backup)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        argv = ["tui"]
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 0
    return func(args) or 0
