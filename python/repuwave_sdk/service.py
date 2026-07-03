"""
Repuwave Python SDK — Service Client.

Client for services to verify agent signatures and report outcomes.
"""

from __future__ import annotations

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
            headers={"Authorization": f"ApiKey {api_key}"},
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
        outcome: str,
        weight: float,
        context: str,
    ) -> bool:
        """
        Report an interaction outcome for an agent.
        """
        response = self._client.post(
            "/report/",
            json={
                "uaid": uaid,
                "outcome": outcome,
                "weight": weight,
                "context": context,
            },
        )
        response.raise_for_status()
        return True

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
