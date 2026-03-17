#!/usr/bin/env python3
"""
cryptian.py — entry point

Run with:
    python cryptian.py
"""

import sys


def _check_dependencies() -> None:
    try:
        import cryptography  # noqa: F401
    except ImportError:
        print("Missing dependency. Install with:")
        print("    pip install cryptography")
        sys.exit(1)


if __name__ == "__main__":
    _check_dependencies()
    from ui.menu import run
    run()