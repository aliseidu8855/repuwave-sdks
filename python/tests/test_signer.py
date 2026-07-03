"""
Repuwave Python SDK — Signer Unit Tests.
"""

import json

import pytest

from repuwave_sdk import generate_keypair
from repuwave_sdk.exceptions import InvalidKeyError, SigningError
from repuwave_sdk.signer import ECDSASigner


class TestKeypairGeneration:
    """Tests for keypair generation."""

    def test_generate_keypair_lengths(self) -> None:
        """Private key is 64 chars, public key is 130 chars."""
        private_key, public_key = generate_keypair()
        assert len(private_key) == 64
        assert len(public_key) == 130

    def test_generate_keypair_uncompressed(self) -> None:
        """Public key starts with '04'."""
        _, public_key = generate_keypair()
        assert public_key.startswith("04")

    def test_generate_keypair_unique(self) -> None:
        """Each call produces a unique keypair."""
        k1 = generate_keypair()
        k2 = generate_keypair()
        assert k1 != k2


class TestCanonicalPayload:
    """Tests for canonical payload construction."""

    def test_deterministic(self) -> None:
        """Same inputs produce the same output."""
        p1 = ECDSASigner.build_canonical_payload("agent-1", 1000.0)
        p2 = ECDSASigner.build_canonical_payload("agent-1", 1000.0)
        assert p1 == p2

    def test_sorted_keys(self) -> None:
        """JSON keys are sorted alphabetically."""
        payload = ECDSASigner.build_canonical_payload("agent-1", 1000.0)
        parsed = json.loads(payload)
        keys = list(parsed.keys())
        assert keys == sorted(keys)

    def test_with_body(self) -> None:
        """Body produces a non-empty body_hash."""
        payload = ECDSASigner.build_canonical_payload(
            "agent-1", 1000.0, b'{"key":"value"}'
        )
        assert '"body_hash":""' not in payload

    def test_without_body(self) -> None:
        """No body produces an empty body_hash."""
        payload = ECDSASigner.build_canonical_payload("agent-1", 1000.0)
        assert '"body_hash":""' in payload


class TestSignVerify:
    """Tests for signing and cross-verification with server."""

    def test_sign_roundtrip(self) -> None:
        """Sign with signer, verify the signature is valid hex."""
        private_key, _ = generate_keypair()
        signer = ECDSASigner(private_key)
        payload = ECDSASigner.build_canonical_payload("agent-1", 1000.0)
        signature = signer.sign(payload)

        # Should be valid hex
        bytes.fromhex(signature)
        assert len(signature) > 0

    def test_signer_exposes_public_key(self) -> None:
        """Signer.public_key matches the generated public key."""
        private_key, public_key = generate_keypair()
        signer = ECDSASigner(private_key)
        assert signer.public_key == public_key

    def test_invalid_private_key(self) -> None:
        """Invalid private key raises InvalidKeyError."""
        with pytest.raises(InvalidKeyError):
            ECDSASigner("not-a-valid-key")

    def test_server_compatible_signature(self) -> None:
        """
        Signature produced by SDK signer can be verified by the
        server's ECDSAService.verify() method (cross-compatibility).
        """
        # This test uses the same ecdsa library and protocol,
        # ensuring the canonical payload + signing are byte-compatible.
        from ecdsa import SECP256k1, VerifyingKey
        from ecdsa.util import sigdecode_der
        import hashlib

        private_key, public_key = generate_keypair()
        signer = ECDSASigner(private_key)

        uaid = "cross-compat-test"
        timestamp = 1715040000.123
        body = b'{"test":"data"}'

        payload = ECDSASigner.build_canonical_payload(uaid, timestamp, body)
        signature_hex = signer.sign(payload)

        # Verify using raw ecdsa (simulating server-side verification)
        key_bytes = bytes.fromhex(public_key[2:])  # Strip "04"
        verifying_key = VerifyingKey.from_string(key_bytes, curve=SECP256k1)
        payload_hash = hashlib.sha256(payload.encode("utf-8")).digest()

        # Should not raise
        verifying_key.verify_digest(
            bytes.fromhex(signature_hex),
            payload_hash,
            sigdecode=sigdecode_der,
        )
