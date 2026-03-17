"""
core/crypto.py

Cryptographic primitives for Cryptian.
- Key derivation : PBKDF2-HMAC-SHA256  (600 000 iterations)
- Encryption     : AES-256-GCM
- Wire format    : base64url( salt[16] | nonce[12] | ciphertext )
"""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ── Constants ────────────────────────────────────────────────────────────────

PBKDF2_ITERATIONS = 600_000
PBKDF2_HASH       = "sha256"
KEY_LENGTH        = 32   # 256 bits
SALT_LENGTH       = 16   # 128 bits
NONCE_LENGTH      = 12   #  96 bits  (GCM standard)


# ── Exceptions ───────────────────────────────────────────────────────────────

class DecryptionError(Exception):
    """Raised when decryption fails (wrong master password or corrupted data)."""


# ── Data container ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CipherPacket:
    """Immutable container for an encrypted value ready to be stored."""
    salt:       bytes
    nonce:      bytes
    ciphertext: bytes

    def encode(self) -> str:
        """Serialize to a base64url string safe for JSON storage."""
        return base64.urlsafe_b64encode(
            self.salt + self.nonce + self.ciphertext
        ).decode()

    @classmethod
    def decode(cls, raw: str) -> "CipherPacket":
        """Deserialize from a base64url string."""
        data       = base64.urlsafe_b64decode(raw)
        salt       = data[:SALT_LENGTH]
        nonce      = data[SALT_LENGTH : SALT_LENGTH + NONCE_LENGTH]
        ciphertext = data[SALT_LENGTH + NONCE_LENGTH :]
        return cls(salt=salt, nonce=nonce, ciphertext=ciphertext)


# ── Core functions ───────────────────────────────────────────────────────────

def derive_key(master_password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit key from a master password and salt using PBKDF2.

    The high iteration count makes brute-force attacks computationally
    expensive: ~0.5 s per attempt on a modern CPU.
    """
    return hashlib.pbkdf2_hmac(
        PBKDF2_HASH,
        master_password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        KEY_LENGTH,
    )


def encrypt(plaintext: str, master_password: str) -> CipherPacket:
    """
    Encrypt a plaintext string under the master password.

    A fresh random salt and nonce are generated for every call,
    ensuring that encrypting the same value twice yields different output.
    """
    salt  = os.urandom(SALT_LENGTH)
    nonce = os.urandom(NONCE_LENGTH)
    key   = derive_key(master_password, salt)

    ciphertext = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    return CipherPacket(salt=salt, nonce=nonce, ciphertext=ciphertext)


def decrypt(packet: CipherPacket, master_password: str) -> str:
    """
    Decrypt a CipherPacket.

    Raises DecryptionError if the master password is wrong or the
    data has been tampered with (GCM authentication tag mismatch).
    """
    key = derive_key(master_password, packet.salt)
    try:
        return AESGCM(key).decrypt(packet.nonce, packet.ciphertext, None).decode("utf-8")
    except Exception as exc:
        raise DecryptionError("Decryption failed — wrong password or corrupted data.") from exc