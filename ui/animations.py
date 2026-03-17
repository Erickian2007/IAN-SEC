"""
ui/animations.py

Terminal animations for Cryptian:
- Opening screen  : logo reveal with color gradient
- Spinner         : animated indicator for long-running operations
- Progress bar    : animated bar for multi-step operations
"""

from __future__ import annotations

import sys
import time
import threading
from typing import Callable, TypeVar

from ui.colors import Color


T = TypeVar("T")


# ── Cursor helpers ───────────────────────────────────────────────────────────

def hide_cursor() -> None:
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor() -> None:
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


# ── Opening animation ────────────────────────────────────────────────────────

_LOGO = [
    " ██████╗██████╗ ██╗   ██╗██████╗ ████████╗██╗ █████╗ ███╗   ██╗",
    "██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██║██╔══██╗████╗  ██║",
    "██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║███████║██╔██╗ ██║",
    "██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║██╔══██║██║╚██╗██║",
    "╚██████╗██║  ██║   ██║   ██║        ██║   ██║██║  ██║██║ ╚████║",
    " ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝   ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝",
]

_SUBTITLE = "Personal Password Vault  •  AES-256-GCM  •  PBKDF2"

_GRADIENT = [
    (180,  80, 255),
    (150, 110, 255),
    ( 90, 160, 255),
    ( 40, 210, 255),
    (  0, 240, 220),
    ( 20, 255, 190),
]


def play_opening() -> None:
    """Animate the Cryptian logo on startup."""
    hide_cursor()
    try:
        # logo lines revealed one by one
        for i, line in enumerate(_LOGO):
            r, g, b = _GRADIENT[i % len(_GRADIENT)]
            print(Color.rgb(r, g, b, line))
            time.sleep(0.07)

        # subtitle typed character by character
        print()
        sys.stdout.write("  ")
        for ch in _SUBTITLE:
            sys.stdout.write(Color.rgb(100, 180, 255, ch))
            sys.stdout.flush()
            time.sleep(0.022)
        print()

        # separator drawn left to right
        print()
        sys.stdout.write("  ")
        for ch in "─" * 66:
            sys.stdout.write(Color.rgb(60, 180, 255, ch))
            sys.stdout.flush()
            time.sleep(0.008)
        print("\n")
        time.sleep(0.3)
    finally:
        show_cursor()


# ── Spinner ──────────────────────────────────────────────────────────────────

_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def with_spinner(func: Callable[..., T], *args, label: str = "Processing", **kwargs) -> T:
    """
    Run *func* in a background thread while displaying an animated spinner.

    Returns the function's return value, or re-raises any exception it throws.

    Example:
        key = with_spinner(derive_key, password, salt, label="Deriving key")
    """
    result:    list       = [None]
    exception: list       = [None]

    def _run() -> None:
        try:
            result[0] = func(*args, **kwargs)
        except Exception as exc:
            exception[0] = exc

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    hide_cursor()
    try:
        i = 0
        while thread.is_alive():
            frame    = _SPINNER_FRAMES[i % len(_SPINNER_FRAMES)]
            bar_len  = 24
            filled   = i % (bar_len + 1)
            bar      = (
                Color.rgb(60, 160, 255, "█" * filled)
                + Color.GRAY + "░" * (bar_len - filled)
                + Color.RESET
            )
            sys.stdout.write(
                f"\r  {Color.rgb(100, 200, 255, frame)} "
                f"{Color.BOLD}{label}...{Color.RESET}  {bar}"
            )
            sys.stdout.flush()
            time.sleep(0.05)
            i += 1
    finally:
        thread.join()
        show_cursor()

    if exception[0] is not None:
        sys.stdout.write(
            f"\r  {Color.error('✗')} {label} failed."
            + " " * 40 + "\n"
        )
        sys.stdout.flush()
        raise exception[0]

    sys.stdout.write(
        f"\r  {Color.success('✓')} "
        f"{Color.BOLD}{label}{Color.RESET} "
        f"{Color.success('done!')}  "
        + " " * 30 + "\n"
    )
    sys.stdout.flush()
    return result[0]


# ── Progress bar ─────────────────────────────────────────────────────────────

def progress_bar(current: int, total: int, width: int = 36, label: str = "") -> None:
    """
    Print an animated progress bar on the current line.

    Color transitions from blue (0%) to green (100%).
    Call with current == total to finalize.
    """
    pct    = current / total
    filled = int(width * pct)
    empty  = width - filled

    if pct < 0.5:
        r, g, b = 40, 140 + int(pct * 220), 255
    else:
        r, g, b = 40, 255, int(255 - pct * 200)

    bar   = Color.rgb(r, g, b, "█" * filled) + Color.GRAY + "░" * empty + Color.RESET
    pct_s = Color.BOLD + f"{int(pct * 100):>3}%" + Color.RESET
    lbl   = Color.muted(label[-40:]) if label else ""

    sys.stdout.write(f"\r  [{bar}] {pct_s}  {lbl}  ")
    sys.stdout.flush()