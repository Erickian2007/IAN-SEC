"""
ui/menu.py

Terminal interface for IAN-SEC.

All user interaction lives here. Business logic is delegated to
the core layer — this module only handles input/output.
"""

from __future__ import annotations

import getpass
import os
import sys

from core.crypto import DecryptionError, derive_key
from core.generator import PasswordGenerator, DEFAULT_LENGTH
from core.vault import EntryNotFoundError, Vault
from ui.animations import play_opening, with_spinner, progress_bar, hide_cursor, show_cursor
from ui.colors import Color
from utils.backup import BackupManager
from utils.clipboard import copy_to_clipboard


# ── Helpers ──────────────────────────────────────────────────────────────────

def _clear() -> None:
    os.system("clear")


def _section(title: str) -> None:
    bar = "─" * (42 - len(title))
    print(f"\n{Color.rgb(60,180,255,'────')} {Color.bold(title)} {Color.rgb(60,180,255, bar)}")


def _prompt_master(action: str = "continue") -> str:
    return getpass.getpass(f"  Master password to {action}: ")


def _print_entries(vault: Vault) -> list[str]:
    """Display entries and return sorted list of names."""
    entries = vault.entries
    if not entries:
        print(f"  {Color.muted('Vault is empty.')}")
        return []
    print(f"  {Color.info(str(len(entries)) + ' entry/entries saved:')}\n")
    for i, name in enumerate(entries, 1):
        print(f"  {Color.muted(f'{i:>2}.')}  {name}")
    return entries


def _menu_border(text: str) -> str:
    return Color.rgb(60, 140, 255, text)


# ── Menu ─────────────────────────────────────────────────────────────────────

_MENU_ITEMS = [
    ("1", "Add password"),
    ("2", "Get password"),
    ("3", "List entries"),
    ("4", "Delete entry"),
    ("5", "Generate password for site"),
    ("6", "Backup vault"),
    ("7", "Manage backup destinations"),
    ("8", "Quit"),
]


def _draw_menu() -> None:
    print(_menu_border("╔════════════════════════════════╗"))
    print(
        _menu_border("║") +
        f"  {Color.accent('🔐  I A N - S E C')}              " +
        _menu_border("║")
    )
    print(_menu_border("╠════════════════════════════════╣"))
    for num, label in _MENU_ITEMS:
        n = Color.info(num)
        print(
            _menu_border("║") +
            f"  {n}{Color.muted('.')} {label:<28}" +
            _menu_border("║")
        )
    print(_menu_border("╚════════════════════════════════╝"))


# ── Action handlers ──────────────────────────────────────────────────────────

def _handle_add(vault: Vault) -> None:
    _section("Add password")
    name = input("  Service name (e.g. github, gmail): ").strip()
    if not name:
        print(f"  {Color.error('✗')} Name cannot be empty.")
        return
    if vault.exists(name):
        confirm = input(f"  '{name}' already exists. Overwrite? (y/N): ").strip().lower()
        if confirm != "y":
            print("  Cancelled.")
            return

    password = getpass.getpass("  Password to store: ")
    master   = _prompt_master("save")

    def _encrypt_op():
        from core.crypto import encrypt
        return encrypt(password, master)

    try:
        packet = with_spinner(_encrypt_op, label="Encrypting")
        from core.crypto import CipherPacket
        vault._data[name] = packet.encode()
        vault._save()
        print(f"  {Color.success('✓')} '{name}' saved successfully.")
    except Exception:
        print(f"  {Color.error('✗')} Failed to save entry.")


def _handle_get(vault: Vault) -> None:
    _section("Get password")
    entries = _print_entries(vault)
    if not entries:
        return

    query  = input("\n  Name or number: ").strip()
    name   = vault.resolve(query)
    if not name:
        print(f"  {Color.error('✗')} Entry not found.")
        return

    master = _prompt_master("retrieve")

    try:
        value = with_spinner(vault.get, name, master, label="Decrypting")
        if copy_to_clipboard(value):
            print(f"  {Color.success('✓')} Password for '{name}' copied to clipboard!")
        else:
            print(f"  🔑 {name}: {Color.bold(value)}")
            print(f"  {Color.muted('(install xclip for automatic clipboard: sudo pacman -S xclip)')}")
    except DecryptionError:
        print(f"  {Color.error('✗')} Wrong master password.")
    except EntryNotFoundError:
        print(f"  {Color.error('✗')} Entry not found.")


def _handle_list(vault: Vault) -> None:
    _section("Saved entries")
    _print_entries(vault)


def _handle_delete(vault: Vault) -> None:
    _section("Delete entry")
    entries = _print_entries(vault)
    if not entries:
        return

    query = input("\n  Name or number to delete: ").strip()
    name  = vault.resolve(query)
    if not name:
        print(f"  {Color.error('✗')} Entry not found.")
        return

    confirm = input(f"  Delete '{name}'? This cannot be undone. (y/N): ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return

    master = _prompt_master("delete")

    try:
        with_spinner(vault.delete, name, master, label="Verifying & deleting")
        print(f"  {Color.success('✓')} '{name}' deleted.")
    except DecryptionError:
        print(f"  {Color.error('✗')} Wrong master password.")
    except EntryNotFoundError:
        print(f"  {Color.error('✗')} Entry not found.")


def _handle_generate() -> None:
    _section("Generate password for site")
    print(f"  {Color.muted('Same inputs always produce the same output. Nothing is stored.')}\n")

    service = input("  Service (e.g. google, github): ").strip().lower()
    if not service:
        print(f"  {Color.error('✗')} Service name cannot be empty.")
        return

    secret  = getpass.getpass("  Your master secret: ")
    len_raw = input(f"  Length [{DEFAULT_LENGTH}]: ").strip()
    length  = int(len_raw) if len_raw.isdigit() else DEFAULT_LENGTH

    gen = PasswordGenerator()

    try:
        password = with_spinner(gen.generate, secret, service, length, label="Generating password")
        if copy_to_clipboard(password):
            print(f"  {Color.success('✓')} Password for '{service}' copied to clipboard!")
        else:
            print(f"  🔑 {service}: {Color.bold(password)}")
        print(f"  {Color.muted(f'({length} characters)')}")
    except Exception:
        print(f"  {Color.error('✗')} Generation failed.")


def _handle_backup(backup_manager: BackupManager) -> None:
    _section("Backup vault")
    backup_manager.run(progress_bar)


def _handle_destinations(backup_manager: BackupManager) -> None:
    backup_manager.manage_destinations()


# ── Main loop ────────────────────────────────────────────────────────────────

def run() -> None:
    """Entry point for the IAN-SEC UI."""
    _clear()
    play_opening()

    vault          = Vault()
    backup_manager = BackupManager()

    handlers = {
        "1": lambda: _handle_add(vault),
        "2": lambda: _handle_get(vault),
        "3": lambda: _handle_list(vault),
        "4": lambda: _handle_delete(vault),
        "5": lambda: _handle_generate(),
        "6": lambda: _handle_backup(backup_manager),
        "7": lambda: _handle_destinations(backup_manager),
    }

    while True:
        _draw_menu()
        choice = input(f"\n  {Color.info('›')} Option: ").strip()

        if choice == "8":
            print(f"\n  {Color.accent('IAN-SEC closed.')} {Color.rgb(60,140,255,'🔒')}\n")
            break

        handler = handlers.get(choice)
        if handler:
            handler()
        else:
            print(f"  {Color.muted('Invalid option.')}")

        input(f"\n  {Color.muted('[Enter to continue]')}")