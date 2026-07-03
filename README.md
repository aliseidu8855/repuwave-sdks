# Repuwave SDKs — Client Libraries

> **Official SDK mono-repo for integrating with the Repuwave trust network.**  
> Python · Node.js

---

## Overview

`repuwave-sdks` contains official client libraries that enable AI agents to **automatically sign outbound requests** with their Ed25519 private keys. SDKs handle the cryptographic complexity so agent developers can focus on business logic.

### What the SDKs Do

1. **Generate Ed25519 keypairs** (32-byte seed) for agent identity
2. **Automatically sign** every outbound HTTP request with the agent's private key
3. **Attach Repuwave headers** (`X-Repuwave-UAID`, `X-Repuwave-Signature`, `X-Repuwave-Timestamp`)
4. **Handle key rotation** seamlessly when rotating to a new keypair
5. **Provide typed responses** for all Repuwave API interactions

### Header Protocol

Every request signed by an SDK includes:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Repuwave-UAID` | `agent-uaid` | Identifies the agent |
| `X-Repuwave-Signature` | `hex(Ed25519_Sign(privkey, SHA256(payload)))` | Proves identity |
| `X-Repuwave-Timestamp` | `1715040000.123456` | Prevents replay attacks (±15s window) |

### Signing Protocol

```
canonical_payload = JSON({
    "uaid": agent_uaid,
    "timestamp": high_resolution_unix_time,
    "body_hash": SHA256(request_body)  // empty string if no body
})

signature = Ed25519_Sign(private_key, SHA256(canonical_payload))
```

---

## Packages

### `python/` — Python SDK

**Target:** Python 3.10+ agents using `httpx` for HTTP.

```
python/
├── repuwave_sdk/
│   └── __init__.py      # Package init + version
├── tests/               # pytest test suite
├── pyproject.toml       # Package config + dependencies
└── README.md            # Python-specific usage guide
```

**Dependencies:** `httpx` (async HTTP), `PyNaCl` (Ed25519 signing)

**Usage (Section C implementation):**

```python
from repuwave_sdk import RepuwaveClient

# Initialize with agent credentials
client = RepuwaveClient(
    private_key="hex-encoded-private-key",
    uaid="agent-uaid-string",
)

# All requests are automatically signed
response = client.get("https://vendor-api.com/data")
# Headers X-Repuwave-UAID, X-Repuwave-Signature, X-Repuwave-Timestamp
# are injected automatically

# Async support
async with RepuwaveAsyncClient(private_key="...", uaid="...") as client:
    response = await client.post("https://vendor-api.com/action", json={"key": "value"})
```

**Key Classes (Section C):**

| Class | Purpose |
|-------|---------|
| `RepuwaveClient` | Synchronous HTTP client wrapping `httpx.Client` |
| `RepuwaveAsyncClient` | Async HTTP client wrapping `httpx.AsyncClient` |
| `Ed25519Signer` | Handles keypair generation, payload signing, signature encoding |
| `RepuwaveError` | Base exception for SDK errors |

---

### `node/` — Node.js SDK

**Target:** Node.js 18+ agents and services using TypeScript.

```
node/
├── src/
│   └── index.ts         # Entry point + exports
├── tests/               # Jest test suite
├── package.json         # Package config + dependencies
└── tsconfig.json        # TypeScript configuration
```

**Dependencies:** `elliptic` (secp256k1), `node-fetch` (HTTP)

**Usage (Section C implementation):**

```typescript
import { RepuwaveClient } from "@repuwave/node-sdk";

const client = new RepuwaveClient({
  privateKey: "hex-encoded-private-key",
  uaid: "agent-uaid-string",
});

// Automatically signed request
const response = await client.get("https://vendor-api.com/data");

// With body
const result = await client.post("https://vendor-api.com/action", {
  body: { key: "value" },
});
```

**Key Exports (Section C):**

| Export | Purpose |
|--------|---------|
| `RepuwaveClient` | HTTP client with auto-signing |
| `Ed25519Signer` | Keypair generation + signing utilities |
| `generateKeypair()` | Helper to create new Ed25519 keypair |
| `RepuwaveError` | Base error class |

---

## Development

### Python SDK

```bash
cd python
pip install -e ".[dev]"    # Install with dev dependencies
pytest                      # Run tests
```

### Node SDK

```bash
cd node
npm install                 # Install dependencies
npm run build               # Compile TypeScript
npm test                    # Run Jest tests
```

---

## Testing Strategy

| Layer | Tool | Coverage |
|-------|------|---------|
| Unit (signing) | pytest / Jest | Keypair generation, signature creation/verification, canonical payload construction |
| Unit (HTTP) | respx / nock | Header injection, timestamp generation, error handling |
| Integration | Live API | Full sign → send → verify round-trip against test Repuwave instance |
