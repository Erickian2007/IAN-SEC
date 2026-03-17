"""
core/vault.py

Vault persistence layer.

Stores encrypted entries as a JSON file at ~/.cryptian.json.
Each entry maps a service name to a base64url-encoded CipherPacket.

File permissions are locked to 600 (owner read/write only).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from core.crypto import CipherPacket, DecryptionError, decrypt, encrypt


# ── Constants ────────────────────────────────────────────────────────────────

VAULT_PATH = Path.home() / ".cryptian.json"


# ── Exceptions ───────────────────────────────────────────────────────────────

class EntryNotFoundError(Exception):
    """Raised when a requested entry does not exist in the vault."""


# ── Vault class ──────────────────────────────────────────────────────────────

class Vault:
    """
    Manages a local encrypted password store.

    All secrets are encrypted at rest with AES-256-GCM.
    The vault file is never written without proper permissions (600).
    """

    def __init__(self, path: Path = VAULT_PATH) -> None:
        self._path = path
        self._data: dict[str, str] = self._load()

    # ── Private ──────────────────────────────────────────────────────────────

    def _load(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        with self._path.open() as f:
            return json.load(f)

    def _save(self) -> None:
        with self._path.open("w") as f:
            json.dump(self._data, f, indent=2)
        os.chmod(self._path, 0o600)

    # ── Public API ───────────────────────────────────────────────────────────

    @property
    def entries(self) -> list[str]:
        """Sorted list of service names in the vault."""
        return sorted(self._data.keys())

    @property
    def is_empty(self) -> bool:
        return len(self._data) == 0

    def exists(self, name: str) -> bool:
        return name in self._data

    def add(self, name: str, password: str, master_password: str) -> None:
        """Encrypt and store a password. Overwrites silently if name exists."""
        packet = encrypt(password, master_password)
        self._data[name] = packet.encode()
        self._save()

    def get(self, name: str, master_password: str) -> str:
        """
        Retrieve and decrypt a stored password.

        Raises EntryNotFoundError or DecryptionError on failure.
        """
        if name not in self._data:
            raise EntryNotFoundError(f"No entry found for '{name}'.")
        packet = CipherPacket.decode(self._data[name])
        return decrypt(packet, master_password)

    def delete(self, name: str, master_password: str) -> None:
        """
        Delete an entry after verifying the master password.

        Raises EntryNotFoundError or DecryptionError on failure.
        """
        if name not in self._data:
            raise EntryNotFoundError(f"No entry found for '{name}'.")
        # verify master password before destructive operation
        packet = CipherPacket.decode(self._data[name])
        decrypt(packet, master_password)
        del self._data[name]
        self._save()

    def resolve(self, query: str) -> Optional[str]:
        """
        Resolve a query to an entry name.

        Accepts either the entry name directly or a 1-based index
        from the sorted entries list.
        """
        if query.isdigit():
            idx = int(query) - 1
            entries = self.entries
            if 0 <= idx < len(entries):
                return entries[idx]
            return None
        return query if query in self._data else None