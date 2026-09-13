from __future__ import annotations

import os

_ESCAPE_MAP = {"A": "up", "B": "down", "C": "right", "D": "left"}


def _get_key_windows() -> str:
    import msvcrt

    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):
        code = msvcrt.getwch()
        return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(code, "")
    if ch == "\r":
        return "enter"
    if ch == "\x1b":
        return "esc"
    if ch == "\x03":
        raise KeyboardInterrupt
    if ch in ("\x08", "\x7f"):
        return "backspace"
    if ch == " ":
        return "space"
    return ch


def _get_key_posix() -> str:
    import select
    import sys
    import termios
    import tty

    tcgetattr = getattr(termios, "tcgetattr")
    tcsetattr = getattr(termios, "tcsetattr")
    tcsadrain = getattr(termios, "TCSADRAIN")
    setraw = getattr(tty, "setraw")

    fd = sys.stdin.fileno()
    old = tcgetattr(fd)
    try:
        setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = ""
            while True:
                ready, _, _ = select.select([sys.stdin], [], [], 0.02)
                if not ready:
                    break
                nxt = sys.stdin.read(1)
                if not nxt:
                    break
                seq += nxt
                if nxt.isalpha() or nxt == "~":
                    break
            return _ESCAPE_MAP.get(seq[-1], "esc")
    finally:
        tcsetattr(fd, tcsadrain, old)
    if ch == "\r" or ch == "\n":
        return "enter"
    if ch == "\x03":
        raise KeyboardInterrupt
    if ch in ("\x08", "\x7f"):
        return "backspace"
    if ch == " ":
        return "space"
    return ch


def get_key() -> str:
    if os.name == "nt":
        return _get_key_windows()
    return _get_key_posix()
