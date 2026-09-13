from __future__ import annotations

from .base import Harness
from .claude import ClaudeHarness
from .codex import CodexHarness
from .hermes import HermesHarness
from .opencode import OpencodeHarness

ALL: list[Harness] = [
    OpencodeHarness(),
    HermesHarness(),
    ClaudeHarness(),
    CodexHarness(),
]

_BY_ID = {harness.id: harness for harness in ALL}


def get(harness_id: str) -> Harness | None:
    return _BY_ID.get(harness_id)
