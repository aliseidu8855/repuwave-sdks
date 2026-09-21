"""
Repuwave Python SDK — HTTP Client.

Auto-signing httpx client that injects X-Repuwave-* headers
into every outbound request.

Usage:
    from repuwave_sdk import RepuwaveClient

    client = RepuwaveClient(
        private_key="your_hex_private_key",
        uaid="your-agent-uuid",
        base_url="https://repuwave.fasolink.app/v1",
    )

    # All requests are automatically signed
    response = client.get("/verify/some-uaid/")
"""

from __future__ import annotations

import time

import httpx

from repuwave_sdk.signer import Ed25519Signer


class RepuwaveClient:
    """
    Synchronous HTTP client with automatic Ed25519 request signing.

    Every request sent through this client automatically receives
    X-Repuwave-UAID, X-Repuwave-Timestamp, and X-Repuwave-Signature
    headers via httpx event hooks.
    """

    def __init__(
        self,
        private_key: str,
        uaid: str,
        base_url: str = "https://repuwave.fasolink.app/v1",
        **httpx_kwargs,
    ) -> None:
        self._signer = Ed25519Signer(private_key)
        self._uaid = uaid
        self._client = httpx.Client(
            base_url=base_url,
            event_hooks={"request": [self._sign_request]},
            **httpx_kwargs,
        )

    def _sign_request(self, request: httpx.Request) -> None:
        """Inject X-Repuwave-* headers before every request."""
        timestamp = time.time()
        body = request.content or b""
        payload = Ed25519Signer.build_canonical_payload(
            self._uaid, timestamp, body if body else None
        )
        signature = self._signer.sign(payload)

        request.headers["X-Repuwave-UAID"] = self._uaid
        request.headers["X-Repuwave-Timestamp"] = str(timestamp)
        request.headers["X-Repuwave-Signature"] = signature

    @property
    def public_key(self) -> str:
        """Return the agent's public key."""
        return self._signer.public_key

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self._client.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self._client.post(url, **kwargs)

    def patch(self, url: str, **kwargs) -> httpx.Response:
        return self._client.patch(url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        return self._client.delete(url, **kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class RepuwaveAsyncClient:
    """
    Asynchronous HTTP client with automatic Ed25519 request signing.

    Same as RepuwaveClient but uses httpx.AsyncClient for async/await.
    """

    def __init__(
        self,
        private_key: str,
        uaid: str,
        base_url: str = "https://repuwave.fasolink.app/v1",
        **httpx_kwargs,
    ) -> None:
        self._signer = Ed25519Signer(private_key)
        self._uaid = uaid
        self._client = httpx.AsyncClient(
            base_url=base_url,
            event_hooks={"request": [self._sign_request]},
            **httpx_kwargs,
        )

    async def _sign_request(self, request: httpx.Request) -> None:
        """Inject X-Repuwave-* headers before every request."""
        timestamp = time.time()
        body = request.content or b""
        payload = Ed25519Signer.build_canonical_payload(
            self._uaid, timestamp, body if body else None
        )
        signature = self._signer.sign(payload)

        request.headers["X-Repuwave-UAID"] = self._uaid
        request.headers["X-Repuwave-Timestamp"] = str(timestamp)
        request.headers["X-Repuwave-Signature"] = signature

    @property
    def public_key(self) -> str:
        return self._signer.public_key

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self._client.post(url, **kwargs)

    async def patch(self, url: str, **kwargs) -> httpx.Response:
        return await self._client.patch(url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        return await self._client.delete(url, **kwargs)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()
