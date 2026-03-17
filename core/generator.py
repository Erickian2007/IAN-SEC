"""
core/generator.py

Deterministic password generator.

Derives a strong password from a human-memorable secret and a service name
using PBKDF2-HMAC-SHA256. The service name acts as the salt, guaranteeing
that the same secret produces a unique password per service.

Key property: stateless — nothing is stored. The same inputs always
produce the same output, on any machine, at any time.
"""

from __future__ import annotations

import hashlib

from core.crypto import PBKDF2_HASH, PBKDF2_ITERATIONS


# ── Constants ────────────────────────────────────────────────────────────────

# Character set accepted by most websites
_CHARSET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "!@#$%&*"
)

DEFAULT_LENGTH = 20
MAX_LENGTH     = 64


# ── Generator class ──────────────────────────────────────────────────────────

class PasswordGenerator:
    """
    Generates deterministic passwords from a master secret and a service name.

    Usage:
        gen = PasswordGenerator()
        password = gen.generate("my_secret", "github", length=24)
    """

    def generate(
        self,
        master_secret: str,
        service: str,
        length: int = DEFAULT_LENGTH,
    ) -> str:
        """
        Derive a strong password for a given service.

        Args:
            master_secret: The human-memorable secret (never stored).
            service:       The service name, used as the PBKDF2 salt.
            length:        Desired password length (1–64).

        Returns:
            A deterministic password of `length` characters.
        """
        length = max(1, min(length, MAX_LENGTH))
        salt   = service.lower().strip().encode("utf-8")

        key = hashlib.pbkdf2_hmac(
            PBKDF2_HASH,
            master_secret.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS,
            64,
        )

        return "".join(_CHARSET[b % len(_CHARSET)] for b in key)[:length]