"""
Repuwave Python SDK — Signer Tests.

Covers Ed25519Signer: keypair generation, canonical payload construction, and
sign/verify.

These were written against the pre-migration ECDSA signer and imported
`ECDSASigner`, which no longer exists — so the file failed at collection and had
not run since the Ed25519 migration. Nothing caught it because CI does not run
the SDK suites. Rewritten against the real API.
"""

from __future__ import annotations

import json

import pytest
from nacl.signing import VerifyKey

from repuwave_sdk import generate_keypair
from repuwave_sdk.exceptions import InvalidKeyError, SigningError
from repuwave_sdk.signer import Ed25519Signer


class TestKeypairGeneration:
    """Keypair generation produces 32-byte hex-encoded keys."""

    def test_generate_keypair_returns_64_char_hex(self):
        private_key, public_key = generate_keypair()

        assert len(private_key) == 64
        assert len(public_key) == 64
        # Both must be valid hex — a stray non-hex character would only surface
        # later, at sign time, as a confusing error.
        bytes.fromhex(private_key)
        bytes.fromhex(public_key)

    def test_generate_keypair_is_unique_per_call(self):
        first, _ = generate_keypair()
        second, _ = generate_keypair()

        assert first != second

    def test_public_key_property_matches_generated_pair(self):
        """
        The signer's public_key must be the one derived from its private key.

        If these disagreed, the agent would register one key and sign with
        another, and every report would fail verification server-side.
        """
        private_key, public_key = generate_keypair()
        signer = Ed25519Signer(private_key)

        assert signer.public_key == public_key


class TestCanonicalPayload:
    """Canonical payloads must be deterministic and match the server's."""

    def test_payload_is_deterministic(self):
        p1 = Ed25519Signer.build_canonical_payload("agent-1", 1000.0)
        p2 = Ed25519Signer.build_canonical_payload("agent-1", 1000.0)

        assert p1 == p2

    def test_payload_has_sorted_keys_and_no_whitespace(self):
        """
        Byte-identical output to the server is required for verification.

        The server builds the same JSON with sorted keys and compact
        separators; any difference in key order or spacing changes the hash and
        the signature fails to verify.
        """
        payload = Ed25519Signer.build_canonical_payload("agent-1", 1000.0)

        assert json.dumps(
            json.loads(payload), sort_keys=True, separators=(",", ":")
        ) == payload
        assert " " not in payload

    def test_payload_includes_uaid_and_timestamp(self):
        payload = Ed25519Signer.build_canonical_payload("agent-42", 1700000000.5)
        parsed = json.loads(payload)

        assert parsed["uaid"] == "agent-42"
        assert parsed["timestamp"] == 1700000000.5

    def test_bodyless_request_has_empty_body_hash(self):
        """No body means an empty hash, not a hash of nothing."""
        parsed = json.loads(
            Ed25519Signer.build_canonical_payload("agent-1", 1000.0)
        )

        assert parsed["body_hash"] == ""

    def test_body_is_hashed_not_embedded(self):
        """
        Only the body *hash* is signed, never the body itself.

        This is what lets a large payload be verified without the signature
        growing with it, and keeps request contents out of the signed material.
        """
        body = b'{"amount": 500}'
        parsed = json.loads(
            Ed25519Signer.build_canonical_payload("agent-1", 1000.0, body)
        )

        assert parsed["body_hash"] != ""
        assert "amount" not in json.dumps(parsed)

    def test_different_bodies_produce_different_payloads(self):
        """The body hash must actually distinguish payloads."""
        p1 = Ed25519Signer.build_canonical_payload("agent-1", 1000.0, b"a")
        p2 = Ed25519Signer.build_canonical_payload("agent-1", 1000.0, b"b")

        assert p1 != p2

    def test_different_timestamps_produce_different_payloads(self):
        p1 = Ed25519Signer.build_canonical_payload("agent-1", 1000.0)
        p2 = Ed25519Signer.build_canonical_payload("agent-1", 1000.1)

        assert p1 != p2


class TestSignVerify:
    """Signatures are valid, deterministic, and verifiable."""

    def test_signature_is_128_hex_chars(self):
        """Ed25519 signatures are 64 bytes — 128 hex characters."""
        private_key, _ = generate_keypair()
        signer = Ed25519Signer(private_key)

        payload = Ed25519Signer.build_canonical_payload("agent-1", 1000.0)
        signature = signer.sign(payload)

        assert len(signature) == 128
        bytes.fromhex(signature)

    def test_signature_verifies_against_the_public_key(self):
        """
        The signature must verify under the registered public key.

        This is the property the whole protocol rests on: the server verifies
        with the public key it holds, never the private key. Verified here with
        PyNaCl directly, independently of the SDK's own code path.
        """
        private_key, public_key = generate_keypair()
        signer = Ed25519Signer(private_key)

        payload = Ed25519Signer.build_canonical_payload("agent-1", 1000.0, b"body")
        signature = signer.sign(payload)

        # The signer signs sha256(payload); verification must apply the same
        # hash rather than the raw payload.
        import hashlib

        payload_hash = hashlib.sha256(payload.encode("utf-8")).digest()
        VerifyKey(bytes.fromhex(public_key)).verify(payload_hash, bytes.fromhex(signature))

    def test_signature_is_deterministic(self):
        """
        Ed25519 is deterministic — the same payload signs to the same bytes.

        Unlike ECDSA, there is no random nonce, so a retry produces an
        identical signature. This is why a retried request is idempotent
        server-side rather than looking like a second distinct request.
        """
        private_key, _ = generate_keypair()
        signer = Ed25519Signer(private_key)

        payload = Ed25519Signer.build_canonical_payload("agent-1", 1000.0)

        assert signer.sign(payload) == signer.sign(payload)

    def test_signature_fails_verification_for_a_modified_payload(self):
        """A tampered payload must not verify — the point of signing it."""
        private_key, public_key = generate_keypair()
        signer = Ed25519Signer(private_key)

        payload = Ed25519Signer.build_canonical_payload("agent-1", 1000.0)
        signature = signer.sign(payload)

        tampered = Ed25519Signer.build_canonical_payload("agent-2", 1000.0)

        import hashlib

        with pytest.raises(Exception):
            VerifyKey(bytes.fromhex(public_key)).verify(
                hashlib.sha256(tampered.encode("utf-8")).digest(),
                bytes.fromhex(signature),
            )

    def test_different_keys_produce_different_signatures(self):
        p1, _ = generate_keypair()
        p2, _ = generate_keypair()

        payload = Ed25519Signer.build_canonical_payload("agent-1", 1000.0)

        assert Ed25519Signer(p1).sign(payload) != Ed25519Signer(p2).sign(payload)


class TestInvalidKeys:
    """Malformed keys fail loudly at construction, not at sign time."""

    def test_invalid_key_raises(self):
        with pytest.raises(InvalidKeyError):
            Ed25519Signer("not-a-valid-key")

    def test_wrong_length_key_raises(self):
        """
        A 16-byte key must be rejected.

        Ed25519 seeds are exactly 32 bytes. A short key would otherwise be
        silently accepted and produce signatures the server rejects, which is a
        far harder failure to diagnose than a constructor error.
        """
        with pytest.raises(InvalidKeyError):
            Ed25519Signer("ab" * 16)

    def test_non_hex_key_raises(self):
        with pytest.raises(InvalidKeyError):
            Ed25519Signer("zz" * 32)
