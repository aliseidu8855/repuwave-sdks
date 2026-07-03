# Repuwave Node.js SDK

> **Official Node.js client for AI agents on the Repuwave trust network.**  
> Node.js 18+ · TypeScript · elliptic (secp256k1)

---

## Overview

The Repuwave Node.js SDK provides a TypeScript-first HTTP client that **automatically signs every outbound request** with the agent's ECDSA private key. It also exports a utility class for keypair generation and signature verification.

---

## Installation

```bash
npm install @repuwave/node-sdk
```

---

## Quick Start

```typescript
import { RepuwaveClient, generateKeypair } from "@repuwave/node-sdk";

// Generate a new keypair (first time setup)
const { privateKey, publicKey } = generateKeypair();
// Register publicKey with Repuwave API to get your UAID

// Initialize client with agent credentials
const client = new RepuwaveClient({
  privateKey: "hex-encoded-private-key",
  uaid: "your-agent-uaid",
});

// All requests are automatically signed
const response = await client.get("https://vendor-api.com/data");

// POST with body — body hash included in signature
const result = await client.post("https://vendor-api.com/action", {
  body: { task: "analyze", data: [1, 2, 3] },
});
```

---

## Exports (Section C)

| Export | Type | Description |
|--------|------|-------------|
| `RepuwaveClient` | Class | HTTP client with auto-signing for all methods |
| `ECDSASigner` | Class | Low-level signing: canonical payload, SHA-256, ECDSA sign/verify |
| `generateKeypair()` | Function | Returns `{ privateKey, publicKey }` (hex-encoded secp256k1) |
| `RepuwaveError` | Class | Base error class for all SDK errors |
| `SigningError` | Class | Invalid key or signing failure |

---

## Signed Headers

Every request includes:

```
X-Repuwave-UAID: <agent-uaid>
X-Repuwave-Signature: <hex-ecdsa-signature>
X-Repuwave-Timestamp: <unix-timestamp-with-microseconds>
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `elliptic` | `^6.5.5` | ECDSA signing (secp256k1 curve) |
| `node-fetch` | `^3.3.0` | HTTP client |

---

## Development

```bash
npm install
npm run build       # Compile TypeScript → dist/
npm test            # Run Jest tests
```
