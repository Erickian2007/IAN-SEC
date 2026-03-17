"""
ui/colors.py

ANSI escape code utilities for terminal styling.
No external dependencies.
"""

from __future__ import annotations


class Color:
    """ANSI escape codes for terminal text formatting."""

    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    CYAN   = "\033[36m"
    WHITE  = "\033[97m"
    GRAY   = "\033[90m"

    @staticmethod
    def rgb(r: int, g: int, b: int, text: str = "") -> str:
        """Wrap text in a 24-bit RGB foreground color escape."""
        return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

    @staticmethod
    def success(text: str) -> str:
        return Color.rgb(80, 255, 160, text)

    @staticmethod
    def error(text: str) -> str:
        return Color.rgb(255, 80, 80, text)

    @staticmethod
    def info(text: str) -> str:
        return Color.rgb(100, 180, 255, text)

    @staticmethod
    def accent(text: str) -> str:
        return Color.rgb(180, 80, 255, text)

    @staticmethod
    def muted(text: str) -> str:
        return f"{Color.GRAY}{text}{Color.RESET}"

    @staticmethod
    def bold(text: str) -> str:
        return f"{Color.BOLD}{text}{Color.RESET}"