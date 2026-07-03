# Repuwave Python SDK

> **Official Python client for AI agents on the Repuwave trust network.**  
> Python 3.10+ · httpx · ECDSA secp256k1

---

## Overview

The Repuwave Python SDK wraps `httpx` to provide an HTTP client that **automatically signs every outbound request** with the agent's ECDSA private key. Vendors receiving these requests can verify the agent's identity and reputation score through the Repuwave API.

### How It Works

1. Agent initializes `RepuwaveClient` with their private key and UAID
2. Every HTTP request (GET, POST, PATCH, DELETE) is intercepted before sending
3. The SDK constructs a canonical payload: `{uaid, timestamp, body_hash}`
4. Signs the payload with ECDSA (secp256k1) and attaches headers
5. Vendor receives the request with `X-Repuwave-UAID`, `X-Repuwave-Signature`, `X-Repuwave-Timestamp`

### Security Guarantees

| Property | Mechanism |
|----------|-----------|
| **Identity** | ECDSA signature proves possession of the registered private key |
| **Integrity** | `body_hash` in signed payload ensures body hasn't been tampered |
| **Freshness** | High-resolution timestamp prevents replay attacks (±15s window) |
| **Non-repudiation** | Signature is verifiable by any party with the agent's public key |

---

## Installation

```bash
pip install repuwave-sdk
```

Or from source:

```bash
cd repuwave-sdks/python
pip install -e ".[dev]"
```

---

## Quick Start

```python
from repuwave_sdk import RepuwaveClient

# Initialize with your agent credentials
client = RepuwaveClient(
    private_key="your-hex-encoded-private-key",
    uaid="your-agent-uaid",
)

# Make signed requests — headers are injected automatically
response = client.get("https://vendor-api.com/data")
print(response.json())

# POST with body — body hash is included in the signature
response = client.post(
    "https://vendor-api.com/action",
    json={"task": "analyze", "data": [1, 2, 3]},
)
```

### Async Usage

```python
from repuwave_sdk import RepuwaveAsyncClient

async with RepuwaveAsyncClient(private_key="...", uaid="...") as client:
    response = await client.get("https://vendor-api.com/data")
    result = await client.post("https://vendor-api.com/action", json={"key": "value"})
```

### Key Generation

```python
from repuwave_sdk import generate_keypair

private_key, public_key = generate_keypair()
# private_key: hex-encoded secp256k1 private key (keep secret!)
# public_key:  hex-encoded public key (register with Repuwave)
```

---

## API Reference (Section C)

### Classes

| Class | Description |
|-------|-------------|
| `RepuwaveClient` | Synchronous HTTP client. Wraps `httpx.Client`. All methods (`get`, `post`, `patch`, `delete`) auto-sign requests. |
| `RepuwaveAsyncClient` | Async HTTP client. Wraps `httpx.AsyncClient`. Context manager support. |
| `ECDSASigner` | Low-level signing utility. Handles canonical payload construction, SHA-256 hashing, ECDSA signing/verification. |

### Functions

| Function | Description |
|----------|-------------|
| `generate_keypair()` | Returns `(private_key_hex, public_key_hex)` tuple |
| `verify_signature(public_key, payload, signature)` | Verifies a signature (useful for testing) |

### Exceptions

| Exception | When |
|-----------|------|
| `RepuwaveError` | Base exception for all SDK errors |
| `SigningError` | Private key is invalid or signing fails |
| `InvalidKeyError` | Provided key is not a valid secp256k1 key |

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | `>=0.27,<1.0` | Modern async-capable HTTP client |
| `ecdsa` | `>=0.19,<1.0` | ECDSA signing with secp256k1 curve |

### Dev Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |
| `respx` | Mock httpx requests |

---

## Testing

```bash
pip install -e ".[dev]"
pytest
pytest --cov=repuwave_sdk
```
