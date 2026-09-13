from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Harness(ABC):
    """A coding harness whose API credentials can be read and written."""

    id: str
    label: str

    @abstractmethod
    def detect(self) -> bool:
        """Return True if this harness is installed / configured on the machine."""

    @abstractmethod
    def current(self) -> dict[str, Any]:
        """Read the harness' active credentials in config shape (may be empty)."""

    @abstractmethod
    def apply(self, cfg: dict[str, Any], dry_run: bool = False) -> list[str]:
        """Write *cfg* into the harness. Returns human-readable change lines."""
