from __future__ import annotations

from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..core import HarnessChange
from ..models import Config

ACCENT = "bright_cyan"
ACCENT_2 = "bright_magenta"
MUTED = "grey62"


def banner() -> RenderableType:
    title = Text()
    title.append("harness", style=f"bold {ACCENT}")
    title.append("-api-", style=MUTED)
    title.append("switcher", style=f"bold {ACCENT_2}")
    subtitle = Text("switch API keys per profile across your coding harnesses", style=MUTED)
    return Panel(
        Align.center(Group(title, subtitle)),
        border_style=ACCENT,
        padding=(0, 2),
    )


def profile_list(config: Config, selected: int) -> RenderableType:
    names = config.profile_names()
    table = Table(
        expand=True,
        show_header=True,
        header_style=f"bold {ACCENT}",
        border_style=MUTED,
        pad_edge=False,
    )
    table.add_column("", width=2, justify="center")
    table.add_column("profile", style="bold white", no_wrap=True)
    table.add_column("harnesses", style=MUTED)
    table.add_column("status", justify="right", no_wrap=True)

    if not names:
        return Panel(
            Align.center(Text("no profiles yet — press 'n' to create one", style=MUTED)),
            title="profiles",
            border_style=MUTED,
        )

    for index, name in enumerate(names):
        profile = config.profiles[name]
        is_selected = index == selected
        is_active = name == config.active_profile
        cursor = ">" if is_selected else " "
        chips = "  ".join(profile.harnesses) or "-"
        status = "[green]active[/green]" if is_active else ""
        row_style = f"on {ACCENT}" if is_selected else ""
        table.add_row(cursor, name, chips, status, style=row_style)

    return Panel(table, title="profiles", border_style=ACCENT, padding=(0, 1))


def help_footer(view: str) -> RenderableType:
    if view == "list":
        keys = "↑/↓ move  ·  enter apply  ·  n new  ·  e edit  ·  c capture  ·  d delete  ·  r reload  ·  q quit"
    elif view == "confirm_apply":
        keys = "y confirm  ·  n/esc cancel"
    elif view == "confirm_delete":
        keys = "y delete  ·  n/esc cancel"
    else:
        keys = "esc back  ·  q quit"
    return Align.center(Text(keys, style=MUTED))


def changes_panel(changes: list[HarnessChange], title: str) -> RenderableType:
    table = Table(expand=True, show_header=True, header_style=f"bold {ACCENT_2}", border_style=MUTED)
    table.add_column("harness", style="bold white", no_wrap=True)
    table.add_column("changes", style=MUTED)
    for change in changes:
        body = "\n".join(change.messages) or "-"
        table.add_row(change.label, body)
    return Panel(table, title=title, border_style=ACCENT_2, padding=(0, 1))


def status_line(message: str, ok: bool = True) -> RenderableType:
    style = "green" if ok else "bright_red"
    return Panel(Text(message, style=style), border_style=style)
