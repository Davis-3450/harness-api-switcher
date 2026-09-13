from __future__ import annotations

from typing import Any


def mask(value: str, show: int = 4) -> str:
    if not value:
        return "(empty)"
    text = str(value)
    if len(text) <= show:
        return "*" * len(text)
    return f"{text[:show]}...{text[-2:]}(len={len(text)})"


def mask_mapping(data: dict[str, Any]) -> dict[str, str]:
    return {key: mask(str(value)) for key, value in data.items()}
