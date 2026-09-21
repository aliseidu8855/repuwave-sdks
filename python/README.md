# Repuwave Python SDK

> **Official Python client for AI agents on the Repuwave trust network.**  
> Python 3.10+ · httpx · Ed25519

---

## Overview

The Repuwave Python SDK has two sides, because an interaction has two.

- **`RepuwaveClient`** (agent side) — wraps `httpx` and **automatically signs
  every outbound request** with the agent's Ed25519 private key, attaching the
  standard `X-Repuwave-*` headers.
- **`RepuwaveService`** (service side) — checks the agent that just called you,
  and reports back what it did.

If you are the one receiving agent traffic, the service side is the half you
need.

### How It Works

1. Agent initializes `RepuwaveClient` with their private key and UAID
2. Every HTTP request (GET, POST, PATCH, DELETE) is intercepted before sending
3. The SDK constructs a canonical payload: `{uaid, timestamp, body_hash}`
4. Signs the payload with Ed25519 and attaches headers
5. Vendor receives the request with `X-Repuwave-UAID`, `X-Repuwave-Signature`, `X-Repuwave-Timestamp`

### Security Guarantees

| Property | Mechanism |
|----------|-----------|
| **Identity** | Ed25519 signature proves possession of the registered private key |
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
# private_key: hex-encoded Ed25519 private key (keep secret!)
# public_key:  hex-encoded public key (register with Repuwave)
```

### Quick Start (service side)

You are a service. An agent has just called you, carrying `X-Repuwave-Signature`
and `X-Repuwave-Timestamp`. Two questions follow: should you act on this, and
what happened when you did.

```python
import os
from repuwave_sdk import RepuwaveService

svc = RepuwaveService(api_key=os.environ["REPUWAVE_SERVICE_KEY"])

# 1. Who is this, and can they be trusted?
result = svc.verify(
    uaid=request.headers["X-Repuwave-UAID"],
    signature=request.headers["X-Repuwave-Signature"],
    timestamp=request.headers["X-Repuwave-Timestamp"],
)

if result["score"] < 50:
    return reject()

# 2. Afterwards, say what happened.
svc.report(
    uaid=result["uaid"],
    event_type="TXN_SUCCESS",
    weight=1.0,
    signature=request.headers["X-Repuwave-Signature"],
    agent_timestamp=float(request.headers["X-Repuwave-Timestamp"]),
)
```

**Pass the agent's own signature to both calls.** It is not a formality. The
server checks it against the agent's registered public key, and refuses without
it — a UAID alone buys nothing, which matters because UAIDs are public, listed
in the key directory. The same applies to the report: one without a signature is
refused outright, which is what stops anyone rating an agent they never met. So
keep the signature between the two steps rather than discarding it after the
check.

**If the agent's request had a body, forward it.** The agent signed a hash of
that body and only you saw it, so pass `body=` (or `body_hash=`) to `verify` or
the signature cannot be reconstructed:

```python
result = svc.verify(
    uaid=..., signature=..., timestamp=..., body=request.body,
)
```

**`base_url` defaults to production.** Point it elsewhere for a local stack, and
include the `/v1` prefix:

```python
svc = RepuwaveService(api_key="...", base_url="http://localhost:8000/v1")
```

**An unknown agent comes back as `{"verified": False, "score": 0,
"trust_level": "UNKNOWN"}`** rather than raising. Read `trust_level` rather than
the score if you want to tell *unknown* apart from *badly behaved* — the zero is
a placeholder, not a measurement. Any other error raises.

---

---

## API Reference (Section C)

### Classes

| Class | Description |
|-------|-------------|
| `RepuwaveClient` | Synchronous HTTP client. Wraps `httpx.Client`. All methods (`get`, `post`, `patch`, `delete`) auto-sign requests. |
| `RepuwaveAsyncClient` | Async HTTP client. Wraps `httpx.AsyncClient`. Context manager support. |
| `Ed25519Signer` | Low-level signing utility. Handles canonical payload construction, SHA-256 hashing, Ed25519 signing. |
| `RepuwaveService` | Service-side client. `verify(uaid, signature, timestamp)` checks an agent; `report(uaid, event_type, weight, signature, agent_timestamp, body=..., body_hash=...)` records what happened. Both take the agent's own signature as proof of interaction. |

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
| `InvalidKeyError` | Provided key is not a valid Ed25519 key |

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | `>=0.27,<1.0` | Modern async-capable HTTP client |
| `pynacl` | `>=1.5,<2.0` | Ed25519 signing (libsodium bindings) |

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
