/**
 * Repuwave Node SDK — Agent Client.
 *
 * Signs outgoing requests from an AI agent to the services it calls. The
 * agent holds an Ed25519 private key; every request carries the standard
 * X-Repuwave-* headers so the service (or its Repuwave middleware) can verify
 * the agent's identity. Uses the global fetch (Node 18+) — no dependencies.
 */

import { Ed25519Signer } from "./signer";

export interface RepuwaveClientOptions {
  /** The agent's UAID (issued when the agent was registered). */
  uaid: string;
  /** 64-char hex Ed25519 private key (seed). Never leaves the agent. */
  privateKey: string;
  /** Optional default base URL for relative request paths. */
  baseUrl?: string;
}

export interface SignedHeaders {
  "X-Repuwave-UAID": string;
  "X-Repuwave-Timestamp": string;
  "X-Repuwave-Signature": string;
}

export interface RequestOptions {
  headers?: Record<string, string>;
}

export class RepuwaveClient {
  private readonly uaid: string;
  private readonly privateKey: string;
  private readonly baseUrl?: string;

  constructor(options: RepuwaveClientOptions) {
    this.uaid = options.uaid;
    this.privateKey = options.privateKey;
    this.baseUrl = options.baseUrl;
  }

  /** Generate a fresh Ed25519 keypair (hex-encoded). */
  static generateKeypair(): { privateKey: string; publicKey: string } {
    return Ed25519Signer.generateKeypair();
  }

  /**
   * Produce the signed headers for a request with the given (already
   * serialized) body string. Pass the exact body bytes you will transmit so
   * the signed body_hash matches what the server reconstructs.
   */
  signHeaders(bodyString = ""): SignedHeaders {
    const timestamp = Date.now() / 1000;
    const canonical = Ed25519Signer.buildCanonicalPayload(
      this.uaid,
      timestamp,
      bodyString || undefined,
    );
    const signature = Ed25519Signer.sign(this.privateKey, canonical);
    return {
      "X-Repuwave-UAID": this.uaid,
      "X-Repuwave-Timestamp": Ed25519Signer.formatTimestamp(timestamp),
      "X-Repuwave-Signature": signature,
    };
  }

  private resolve(url: string): string {
    if (/^https?:\/\//.test(url) || !this.baseUrl) return url;
    return `${this.baseUrl.replace(/\/$/, "")}/${url.replace(/^\//, "")}`;
  }

  /** Send a signed GET request to a service. */
  async get(url: string, options: RequestOptions = {}): Promise<Response> {
    return fetch(this.resolve(url), {
      method: "GET",
      headers: { ...this.signHeaders(""), ...(options.headers ?? {}) },
    });
  }

  /**
   * Send a signed POST request to a service. The body is JSON-serialized and
   * that exact string is both signed (via body_hash) and transmitted.
   */
  async post(url: string, body: unknown, options: RequestOptions = {}): Promise<Response> {
    const bodyString = typeof body === "string" ? body : JSON.stringify(body);
    return fetch(this.resolve(url), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.signHeaders(bodyString),
        ...(options.headers ?? {}),
      },
      body: bodyString,
    });
  }
}
