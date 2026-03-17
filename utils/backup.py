"""
utils/backup.py

Vault backup manager.

Backup destinations are stored in ~/.cryptian_config.json.
Each backup is timestamped, so multiple backups coexist without
overwriting each other.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from core.vault import VAULT_PATH
from ui.colors import Color


# ── Constants ────────────────────────────────────────────────────────────────

CONFIG_PATH = Path.home() / ".cryptian_config.json"


# ── BackupManager class ──────────────────────────────────────────────────────

class BackupManager:
    """
    Manages backup destinations and performs timestamped vault copies.

    Config file schema:
        { "destinations": ["/path/a", "/path/b", ...] }
    """

    def __init__(self, config_path: Path = CONFIG_PATH) -> None:
        self._config_path = config_path
        self._config      = self._load_config()

    # ── Private ──────────────────────────────────────────────────────────────

    def _load_config(self) -> dict:
        if not self._config_path.exists():
            return {"destinations": []}
        with self._config_path.open() as f:
            return json.load(f)

    def _save_config(self) -> None:
        with self._config_path.open("w") as f:
            json.dump(self._config, f, indent=2)
        os.chmod(self._config_path, 0o600)

    @property
    def _destinations(self) -> list[str]:
        return self._config.get("destinations", [])

    @_destinations.setter
    def _destinations(self, value: list[str]) -> None:
        self._config["destinations"] = value
        self._save_config()

    # ── Public API ───────────────────────────────────────────────────────────

    def run(self, progress_callback: Optional[Callable] = None) -> None:
        """
        Copy the vault file to all configured destinations.

        Each backup is named with a timestamp:
            cryptian_backup_YYYYMMDD_HHMMSS.json
        """
        if not VAULT_PATH.exists():
            print(f"  {Color.muted('Vault is empty — nothing to back up.')}")
            return

        destinations = self._destinations
        if not destinations:
            print(f"  {Color.muted('No destinations configured.')}")
            print(f"  {Color.muted('Add a destination first (option 7).')}")
            return

        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"cryptian_backup_{timestamp}.json"
        errors      = 0

        print(f"\n  Backing up to {len(destinations)} destination(s)...\n")

        for dest_raw in destinations:
            dest = Path(dest_raw).expanduser()
            steps = 30
            for step in range(steps + 1):
                if progress_callback:
                    progress_callback(step, steps, label=dest_raw)
                time.sleep(0.02)

            try:
                dest.mkdir(parents=True, exist_ok=True)
                target = dest / backup_name
                shutil.copy2(VAULT_PATH, target)
                os.chmod(target, 0o600)
                print(f"  {Color.success('✓')} {dest_raw}")
            except Exception as exc:
                print(f"  {Color.error('✗')} {dest_raw} — {exc}")
                errors += 1

        if errors == 0:
            print(f"\n  {Color.success('✓ Backup complete:')} {backup_name}")
        else:
            print(f"\n  Backup finished with {errors} error(s).")

    def manage_destinations(self) -> None:
        """Interactive sub-menu to add/remove backup destinations."""
        while True:
            destinations = self._destinations
            print(f"\n{Color.bold('── Backup destinations ──')}")
            if not destinations:
                print(f"  {Color.muted('No destinations configured.')}")
            else:
                for i, d in enumerate(destinations, 1):
                    print(f"  {Color.muted(f'{i}.')}  {d}")

            print("\n  a. Add    r. Remove    b. Back")
            choice = input("\n  Option: ").strip().lower()

            if choice == "a":
                print(f"\n  {Color.muted('Examples:')}")
                print("    /media/my-usb/backup")
                print("    ~/Dropbox/cryptian")
                print("    /mnt/external-hd/passwords")
                new = input("\n  Path: ").strip()
                if new and new not in destinations:
                    destinations.append(new)
                    self._destinations = destinations
                    print(f"  {Color.success('✓')} '{new}' added.")
                elif new in destinations:
                    print("  Destination already exists.")

            elif choice == "r":
                if not destinations:
                    print("  No destinations to remove.")
                    continue
                idx = input("  Number to remove: ").strip()
                try:
                    removed = destinations.pop(int(idx) - 1)
                    self._destinations = destinations
                    print(f"  {Color.success('✓')} '{removed}' removed.")
                except (ValueError, IndexError):
                    print("  Invalid number.")

            elif choice == "b":
                break