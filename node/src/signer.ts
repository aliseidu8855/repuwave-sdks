import { createHash, generateKeyPairSync, sign, verify } from "crypto";

export class Ed25519Signer {
  /**
   * Generate a new Ed25519 keypair.
   * Returns 64-char hex private key (seed) and 64-char hex public key.
   */
  static generateKeypair(): { privateKey: string; publicKey: string } {
    const { publicKey, privateKey } = generateKeyPairSync("ed25519");

    // Export raw key bytes as hex
    const pubRaw = publicKey.export({ type: "spki", format: "der" });
    const privRaw = privateKey.export({ type: "pkcs8", format: "der" });

    // Ed25519 DER-encoded SPKI public key: last 32 bytes are the raw key
    const publicKeyHex = pubRaw.subarray(pubRaw.length - 32).toString("hex");

    // Ed25519 DER-encoded PKCS8 private key: last 32 bytes are the seed
    const privateKeyHex = privRaw.subarray(privRaw.length - 32).toString("hex");

    return { privateKey: privateKeyHex, publicKey: publicKeyHex };
  }

  /**
   * Build the canonical payload string for signing.
   * Must produce byte-identical output to the server's Ed25519Service.
   */
  static buildCanonicalPayload(
    uaid: string,
    timestamp: number,
    body?: any
  ): string {
    let bodyHash = "";
    if (body) {
      const bodyString = typeof body === "string" ? body : JSON.stringify(body);
      bodyHash = createHash("sha256").update(bodyString).digest("hex");
    }

    const payload = {
      body_hash: bodyHash,
      timestamp: timestamp,
      uaid: uaid,
    };

    // Ensure sorted keys for deterministic payload
    const sortedKeys = Object.keys(payload).sort() as (keyof typeof payload)[];
    const orderedPayload: Record<string, any> = {};
    for (const key of sortedKeys) {
      orderedPayload[key] = payload[key];
    }

    return JSON.stringify(orderedPayload);
  }

  /**
   * Sign a canonical payload with an Ed25519 private key.
   * Returns hex-encoded 64-byte signature (128 hex chars).
   */
  static sign(privateKeyHex: string, canonicalPayload: string): string {
    // Reconstruct the PKCS8 DER wrapper for the Ed25519 seed
    const seedBytes = Buffer.from(privateKeyHex, "hex");
    const pkcs8Prefix = Buffer.from(
      "302e020100300506032b657004220420",
      "hex"
    );
    const pkcs8Der = Buffer.concat([pkcs8Prefix, seedBytes]);

    const privateKey = {
      key: pkcs8Der,
      format: "der" as const,
      type: "pkcs8" as const,
    };

    // Hash the canonical payload (SHA-256 digest, matching server protocol)
    const payloadHash = createHash("sha256").update(canonicalPayload).digest();

    // Ed25519 sign the hash (deterministic — no random nonce)
    const signature = sign(null, payloadHash, privateKey);

    return signature.toString("hex");
  }
}
