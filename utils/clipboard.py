"""
utils/clipboard.py

Cross-platform clipboard access without external dependencies.

Supported platforms:
- Linux  : xclip (preferred) or xsel
- macOS  : pbcopy
- Windows: clip
"""

from __future__ import annotations

import subprocess
import sys


def copy_to_clipboard(text: str) -> bool:
    """
    Copy *text* to the system clipboard.

    Returns True on success, False if no clipboard tool is available.
    """
    try:
        if sys.platform.startswith("linux"):
            return _linux(text)
        elif sys.platform == "darwin":
            return _macos(text)
        elif sys.platform == "win32":
            return _windows(text)
    except Exception:
        pass
    return False


# ── Platform implementations ─────────────────────────────────────────────────

def _linux(text: str) -> bool:
    for cmd in (
        ["xclip", "-selection", "clipboard"],
        ["xsel",  "--clipboard", "--input"],
    ):
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
            return proc.returncode == 0
        except FileNotFoundError:
            continue
    return False


def _macos(text: str) -> bool:
    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    proc.communicate(text.encode("utf-8"))
    return proc.returncode == 0


def _windows(text: str) -> bool:
    proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
    proc.communicate(text.encode("utf-8"))
    return proc.returncode == 0