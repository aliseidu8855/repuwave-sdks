/**
 * Repuwave Node.js SDK
 *
 * Auto-signing HTTP client (agents) and verification/reporting client
 * (services) for the Repuwave Trust & Reputation API.
 */

import { Ed25519Signer } from "./signer";

export { RepuwaveClient } from "./client";
export type { RepuwaveClientOptions, SignedHeaders, RequestOptions } from "./client";
export { RepuwaveService } from "./service";
export type {
  RepuwaveServiceOptions,
  VerifyParams,
  ReportParams,
  EventType,
} from "./service";
export { Ed25519Signer } from "./signer";
export { RepuwaveError, SigningError, ApiError } from "./errors";

/** Convenience: generate a fresh Ed25519 keypair (hex-encoded). */
export function generateKeypair(): { privateKey: string; publicKey: string } {
  return Ed25519Signer.generateKeypair();
}

export const VERSION = "0.1.0";
