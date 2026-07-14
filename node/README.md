# Repuwave Node.js SDK

> **Official Node.js client for the Repuwave trust network.**
> Node.js 18+ · TypeScript · Ed25519 · zero runtime dependencies

---

## Overview

The Repuwave Node.js SDK provides two TypeScript-first clients:

- **`RepuwaveClient`** (agent side) — automatically signs every outbound
  request with the agent's **Ed25519** private key, attaching the standard
  `X-Repuwave-*` headers.
- **`RepuwaveService`** (service side) — verify an agent's trust score and
  report interaction outcomes back to Repuwave using your service API key.

It uses the built-in `crypto` module and the global `fetch` (Node 18+), so it
has **no runtime dependencies**.

---

## Installation

```bash
npm install @repuwave/node-sdk
```

---

## Quick Start (agent side)

```typescript
import { RepuwaveClient, generateKeypair } from "@repuwave/node-sdk";

// First-time setup: generate a keypair, register publicKey to get your UAID.
const { privateKey, publicKey } = generateKeypair();

const client = new RepuwaveClient({
  uaid: "your-agent-uaid",
  privateKey, // 64-char hex Ed25519 seed — never leaves the agent
});

// All requests are automatically signed with the X-Repuwave-* headers.
const res = await client.get("https://service-api.com/data");

// POST with a body — the exact serialized body is hashed into the signature.
const result = await client.post("https://service-api.com/action", {
  task: "analyze",
  data: [1, 2, 3],
});

// Or just get the signed headers to use with your own HTTP client:
const headers = client.signHeaders(JSON.stringify({ task: "analyze" }));
```

## Quick Start (service side)

```typescript
import { RepuwaveService } from "@repuwave/node-sdk";

const svc = new RepuwaveService({ apiKey: process.env.REPUWAVE_SERVICE_KEY! });

// Verify an incoming agent's trust score.
const verdict = await svc.verify({ uaid: incomingUaid });
if ((verdict.score as number) < 50) {
  // reject the request
}

// Report the outcome of an interaction. Pass the agent's original request
// signature + signed timestamp (from the X-Repuwave-* headers) as proof.
await svc.report({
  uaid: incomingUaid,
  eventType: "TXN_SUCCESS",
  weight: 1.0,
  signature: incomingSignature,      // X-Repuwave-Signature
  agentTimestamp: Number(incomingTs), // X-Repuwave-Timestamp
  body: rawRequestBody,               // hashed into body_hash for you
});
```

---

## Exports

| Export | Type | Description |
|--------|------|-------------|
| `RepuwaveClient` | Class | Agent client; auto-signs `get`/`post`, plus `signHeaders()` |
| `RepuwaveService` | Class | Service client; `verify()` and `report()` |
| `Ed25519Signer` | Class | Low-level signing: canonical payload, SHA-256, Ed25519 sign |
| `generateKeypair()` | Function | Returns `{ privateKey, publicKey }` (hex-encoded Ed25519) |
| `RepuwaveError` | Class | Base error class |
| `SigningError` | Class | Invalid key or signing failure |
| `ApiError` | Class | Non-2xx API response (`status`, `code`, `body`) |

---

## Signed Headers

Every agent request includes:

```
X-Repuwave-UAID:      <agent-uaid>
X-Repuwave-Signature: <128-hex Ed25519 signature>
X-Repuwave-Timestamp: <unix timestamp, e.g. 1700000000.0>
```

The signature is `Ed25519(SHA256(canonical_payload))`, where the canonical
payload is the compact, sorted-key JSON `{"body_hash","timestamp","uaid"}` —
byte-identical to what the Repuwave server reconstructs (the timestamp is
rendered with Python-style float formatting so whole seconds keep their `.0`).

---

## Development

```bash
npm install
npm run build       # Compile TypeScript → dist/
npm test            # Run Jest tests
```
