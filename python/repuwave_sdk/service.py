"""
Repuwave Python SDK — Service Client.

Client for services to verify agent signatures and report outcomes.
"""

from __future__ import annotations

import hashlib
import time

import httpx


class RepuwaveService:
    """
    Client for services receiving requests from Repuwave-authenticated agents.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.repuwave.io/v1",
        **httpx_kwargs,
    ) -> None:
        self._api_key = api_key
        self._client = httpx.Client(
            base_url=base_url,
            headers={"X-Service-API-Key": api_key},
            **httpx_kwargs,
        )

    def verify(
        self,
        uaid: str,
        signature: str,
        timestamp: str | float,
    ) -> dict:
        """
        Verify an agent's signature and retrieve their current trust score.
        """
        response = self._client.get(
            f"/verify/{uaid}/",
            headers={
                "X-Repuwave-Signature": signature,
                "X-Repuwave-Timestamp": str(timestamp),
            },
        )
        if response.status_code == 404:
            return {"verified": False, "score": 0, "trust_level": "UNKNOWN", "uaid": uaid}

        response.raise_for_status()
        return response.json()

    def report(
        self,
        uaid: str,
        event_type: str,
        weight: float,
        signature: str,
        agent_timestamp: float,
        body: bytes | None = None,
        body_hash: str = "",
    ) -> dict:
        """
        Report an interaction outcome for an agent.

        Every report must carry proof of interaction — the Ed25519 signature
        the agent sent with its original request (X-Repuwave-Signature),
        together with the signed timestamp (X-Repuwave-Timestamp) and the
        SHA-256 hash of the raw request body the agent signed.

        Args:
            uaid: The agent's UAID.
            event_type: One of TXN_SUCCESS, TXN_HV_SUCCESS, TXN_NEUTRAL,
                TXN_FAIL_MINOR, TXN_FAIL_MAJOR, TXN_MALICIOUS, TXN_CHARGEBACK.
            weight: Contextual weight of the interaction (0.1–10.0).
            signature: The agent's signature from the original request.
            agent_timestamp: The Unix timestamp the agent signed.
            body: Raw request body bytes the agent signed (hashed for you).
            body_hash: Precomputed SHA-256 hex of the body (alternative to
                `body`; leave both empty for bodyless requests).

        Returns:
            The API response, e.g. {"accepted": True, "event_id": "..."}.
        """
        if body and not body_hash:
            body_hash = hashlib.sha256(body).hexdigest()

        response = self._client.post(
            "/report/",
            json={
                "uaid": uaid,
                "event_type": event_type,
                "weight": weight,
                "signature": signature,
                "agent_timestamp": agent_timestamp,
                "body_hash": body_hash,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
