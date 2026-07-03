"""
Repuwave Python SDK — Ed25519 Signer.

Client-side implementation of the Repuwave signing protocol.
Generates Ed25519 keypairs and signs requests for agent authentication.

Ed25519 provides deterministic signatures (no random nonce),
side-channel resistance, and ~5× faster signing than ECDSA.
"""

from __future__ import annotations

import hashlib
import json
import time

from nacl.signing import SigningKey, VerifyKey

from repuwave_sdk.exceptions import InvalidKeyError, SigningError


class Ed25519Signer:
    """
    Client-side Ed25519 signer for Repuwave agent authentication.

    Wraps a private key and provides methods to sign requests
    using the canonical Repuwave protocol.

    Usage:
        signer = Ed25519Signer(private_key_hex)
        payload = Ed25519Signer.build_canonical_payload(uaid, timestamp, body)
        signature = signer.sign(payload)
    """

    def __init__(self, private_key_hex: str) -> None:
        """
        Initialize with a hex-encoded Ed25519 private key (seed).

        Args:
            private_key_hex: 64-character hex string (32 bytes).

        Raises:
            InvalidKeyError: If the private key is malformed.
        """
        try:
            self._signing_key = SigningKey(bytes.fromhex(private_key_hex))
        except Exception as e:
            raise InvalidKeyError(f"Invalid private key: {e}") from e

        self._public_key_hex = self._signing_key.verify_key.encode().hex()

    @property
    def public_key(self) -> str:
        """Return the hex-encoded public key (64 chars, 32 bytes)."""
        return self._public_key_hex

    @staticmethod
    def generate_keypair() -> tuple[str, str]:
        """
        Generate a new Ed25519 keypair.

        Returns:
            Tuple of (private_key_hex, public_key_hex).
            - private_key_hex: 64-character hex (32-byte seed)
            - public_key_hex: 64-character hex (32-byte public key)
        """
        signing_key = SigningKey.generate()

        private_hex = signing_key.encode().hex()
        public_hex = signing_key.verify_key.encode().hex()

        return private_hex, public_hex

    @staticmethod
    def build_canonical_payload(
        uaid: str,
        timestamp: float,
        body: bytes | None = None,
    ) -> str:
        """
        Build the canonical payload string for signing.

        This must produce byte-identical output to the server's
        Ed25519Service.build_canonical_payload() for verification to work.

        Args:
            uaid: The agent's Unique Agent ID.
            timestamp: High-resolution Unix timestamp.
            body: Raw request body bytes (None for bodyless requests).

        Returns:
            Deterministic JSON string with sorted keys, no whitespace.
        """
        body_hash = hashlib.sha256(body).hexdigest() if body else ""

        payload = {
            "uaid": uaid,
            "timestamp": timestamp,
            "body_hash": body_hash,
        }

        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def sign(self, canonical_payload: str) -> str:
        """
        Sign a canonical payload.

        Args:
            canonical_payload: The JSON payload string from build_canonical_payload.

        Returns:
            Hex-encoded 64-byte signature string (128 hex chars).

        Raises:
            SigningError: If signing fails.
        """
        try:
            payload_hash = hashlib.sha256(
                canonical_payload.encode("utf-8")
            ).digest()

            signed = self._signing_key.sign(payload_hash)

            return signed.signature.hex()
        except Exception as e:
            raise SigningError(f"Failed to sign payload: {e}") from e
