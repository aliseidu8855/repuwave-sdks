import { createHash, verify as cryptoVerify } from "crypto";
import { Ed25519Signer } from "../src/signer";
import { generateKeypair, RepuwaveClient } from "../src";
import { SigningError } from "../src/errors";

describe("Ed25519Signer", () => {
  it("generates 64-hex-char keypairs", () => {
    const { privateKey, publicKey } = Ed25519Signer.generateKeypair();
    expect(privateKey).toHaveLength(64);
    expect(publicKey).toHaveLength(64);
    expect(privateKey).toMatch(/^[0-9a-f]{64}$/);
  });

  describe("formatTimestamp (Python float-repr parity)", () => {
    it("appends .0 to whole-second timestamps", () => {
      expect(Ed25519Signer.formatTimestamp(1700000000)).toBe("1700000000.0");
    });
    it("leaves fractional timestamps unchanged", () => {
      expect(Ed25519Signer.formatTimestamp(1700000000.123)).toBe("1700000000.123");
    });
  });

  describe("buildCanonicalPayload", () => {
    it("matches the server's compact sorted-key JSON for a whole second", () => {
      // This is exactly what Python's json.dumps(..., sort_keys=True,
      // separators=(",",":")) produces for the same inputs.
      const canonical = Ed25519Signer.buildCanonicalPayload("agent-123", 1700000000);
      expect(canonical).toBe(
        '{"body_hash":"","timestamp":1700000000.0,"uaid":"agent-123"}',
      );
    });

    it("hashes the body into body_hash", () => {
      const body = '{"amount":100}';
      const expectedHash = createHash("sha256").update(body).digest("hex");
      const canonical = Ed25519Signer.buildCanonicalPayload("a", 1700000000.5, body);
      expect(canonical).toContain(`"body_hash":"${expectedHash}"`);
      expect(canonical).toContain('"timestamp":1700000000.5');
    });
  });

  it("produces a signature that verifies against its own public key", () => {
    const { privateKey, publicKey } = Ed25519Signer.generateKeypair();
    const canonical = Ed25519Signer.buildCanonicalPayload("agent-x", 1700000000);
    const sigHex = Ed25519Signer.sign(privateKey, canonical);

    // Reconstruct the SPKI DER public key the way the server middleware does.
    const spkiDer = Buffer.concat([
      Buffer.from("302a300506032b6570032100", "hex"),
      Buffer.from(publicKey, "hex"),
    ]);
    const payloadHash = createHash("sha256").update(canonical).digest();
    const ok = cryptoVerify(
      null,
      payloadHash,
      { key: spkiDer, format: "der", type: "spki" },
      Buffer.from(sigHex, "hex"),
    );
    expect(ok).toBe(true);
    expect(sigHex).toHaveLength(128);
  });

  it("throws SigningError on a malformed private key", () => {
    expect(() => Ed25519Signer.sign("deadbeef", "payload")).toThrow(SigningError);
  });
});

describe("public exports", () => {
  it("exposes a top-level generateKeypair", () => {
    expect(generateKeypair().publicKey).toHaveLength(64);
  });

  it("RepuwaveClient.signHeaders returns the three Repuwave headers", () => {
    const { privateKey } = generateKeypair();
    const client = new RepuwaveClient({ uaid: "u-1", privateKey });
    const headers = client.signHeaders("");
    expect(headers["X-Repuwave-UAID"]).toBe("u-1");
    expect(headers["X-Repuwave-Signature"]).toMatch(/^[0-9a-f]{128}$/);
    expect(headers["X-Repuwave-Timestamp"]).toMatch(/\./); // Python-style float
  });
});
