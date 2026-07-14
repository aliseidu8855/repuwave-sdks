import { createHash, generateKeyPairSync, sign } from "crypto";
import { SigningError } from "./errors";

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
   * Format a Unix timestamp to match Python's float repr.
   *
   * The server serializes the timestamp with Python's json.dumps, which
   * always renders a float with a decimal point (e.g. 1700000000.0).
   * JavaScript's Number#toString drops the trailing ".0" for whole numbers,
   * so a whole-second timestamp would produce a different canonical string
   * and the signature would fail to verify. Appending ".0" when no decimal
   * (or exponent) is present makes the two representations identical.
   */
  static formatTimestamp(timestamp: number): string {
    const s = timestamp.toString();
    return /[.eE]/.test(s) ? s : `${s}.0`;
  }

  /**
   * Build the canonical payload string for signing.
   * Must produce byte-identical output to the server's Ed25519Service:
   * a compact, sorted-key JSON object {body_hash, timestamp, uaid} with the
   * timestamp rendered exactly as Python would.
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

    // Built manually (not via JSON.stringify) so the timestamp keeps its
    // Python-compatible ".0". Keys are in sorted order; JSON.stringify is
    // used only to escape the string values.
    return (
      `{"body_hash":${JSON.stringify(bodyHash)},` +
      `"timestamp":${Ed25519Signer.formatTimestamp(timestamp)},` +
      `"uaid":${JSON.stringify(uaid)}}`
    );
  }

  /**
   * Sign a canonical payload with an Ed25519 private key.
   * Returns hex-encoded 64-byte signature (128 hex chars).
   */
  static sign(privateKeyHex: string, canonicalPayload: string): string {
    try {
      // Reconstruct the PKCS8 DER wrapper for the Ed25519 seed
      const seedBytes = Buffer.from(privateKeyHex, "hex");
      if (seedBytes.length !== 32) {
        throw new SigningError(
          `Ed25519 private key must be 32 bytes (64 hex chars), got ${seedBytes.length}.`,
        );
      }
      const pkcs8Prefix = Buffer.from("302e020100300506032b657004220420", "hex");
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
    } catch (err) {
      if (err instanceof SigningError) throw err;
      throw new SigningError(`Failed to sign payload: ${(err as Error).message}`);
    }
  }
}
