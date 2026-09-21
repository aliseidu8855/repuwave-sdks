/**
 * Repuwave Node SDK — Service Client.
 *
 * For services that receive requests from Repuwave-authenticated agents:
 * verify an agent's trust score and report interaction outcomes back to
 * Repuwave. Authenticates with the service API key via the X-Service-API-Key
 * header. Uses the global fetch (Node 18+) — no dependencies.
 */

import { createHash } from "crypto";
import { ApiError } from "./errors";

export interface RepuwaveServiceOptions {
  /** The service's API key (X-Service-API-Key). */
  apiKey: string;
  baseUrl?: string;
}

export interface VerifyParams {
  uaid: string;
  /**
   * The agent's signature from the incoming request.
   *
   * Required. The server checks it against the agent's registered public key
   * and refuses without it -- a UAID alone proves nothing, because UAIDs are
   * public, listed in the key directory. This was typed optional and described
   * as "optional context" while the endpoint ignored it entirely.
   */
  signature: string;
  /** The timestamp the agent signed. Valid 15s either side of server time. */
  timestamp: string | number;
  /**
   * sha256 of the body the agent sent you, if its request had one. The agent
   * signed that hash and only you saw the body, so without it the signature
   * cannot be reconstructed.
   */
  bodyHash?: string;
}

export type EventType =
  | "TXN_SUCCESS"
  | "TXN_HV_SUCCESS"
  | "TXN_NEUTRAL"
  | "TXN_FAIL_MINOR"
  | "TXN_FAIL_MAJOR"
  | "TXN_MALICIOUS"
  | "TXN_CHARGEBACK";

export interface ReportParams {
  uaid: string;
  eventType: EventType;
  weight: number;
  /** The agent's signature from its original request (proof of interaction). */
  signature: string;
  /** The Unix timestamp the agent signed (X-Repuwave-Timestamp). */
  agentTimestamp: number;
  /** Raw request body the agent signed (hashed for you), or a precomputed hash. */
  body?: string;
  bodyHash?: string;
}

export class RepuwaveService {
  private readonly apiKey: string;
  private readonly baseUrl: string;

  constructor(options: RepuwaveServiceOptions) {
    this.apiKey = options.apiKey;
    this.baseUrl = (options.baseUrl || "https://repuwave.fasolink.app/v1").replace(/\/$/, "");
  }

  private headers(extra: Record<string, string> = {}): Record<string, string> {
    return { "X-Service-API-Key": this.apiKey, ...extra };
  }

  private async parseError(response: Response): Promise<never> {
    let code = "unknown_error";
    let message = response.statusText;
    let body: unknown = null;
    try {
      body = await response.json();
      const err = (body as { error?: { code?: string; message?: string } }).error;
      if (err) {
        code = err.code ?? code;
        message = err.message ?? message;
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(message, response.status, code, body);
  }

  /**
   * Verify an agent's identity and fetch their current trust score.
   * Returns a not-verified result for unknown agents (404) rather than throwing.
   */
  async verify(params: VerifyParams): Promise<Record<string, unknown>> {
    const headers = this.headers();
    if (params.signature) headers["X-Repuwave-Signature"] = params.signature;
    if (params.timestamp !== undefined) {
      headers["X-Repuwave-Timestamp"] = params.timestamp.toString();
    }
    if (params.bodyHash) headers["X-Repuwave-Body-Hash"] = params.bodyHash;

    const response = await fetch(`${this.baseUrl}/verify/${params.uaid}/`, {
      method: "GET",
      headers,
    });

    if (response.status === 404) {
      return { verified: false, score: 0, trust_level: "UNKNOWN", uaid: params.uaid };
    }
    if (!response.ok) return this.parseError(response);
    return response.json() as Promise<Record<string, unknown>>;
  }

  /**
   * Report an interaction outcome for an agent. Must include the agent's
   * original request signature and signed timestamp as proof of interaction.
   */
  async report(params: ReportParams): Promise<Record<string, unknown>> {
    let bodyHash = params.bodyHash ?? "";
    if (params.body && !bodyHash) {
      bodyHash = createHash("sha256").update(params.body).digest("hex");
    }

    const response = await fetch(`${this.baseUrl}/report/`, {
      method: "POST",
      headers: this.headers({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        uaid: params.uaid,
        event_type: params.eventType,
        weight: params.weight,
        signature: params.signature,
        agent_timestamp: params.agentTimestamp,
        body_hash: bodyHash,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) return this.parseError(response);
    return response.json() as Promise<Record<string, unknown>>;
  }
}
