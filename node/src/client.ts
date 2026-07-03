import fetch from "node-fetch";
import { Ed25519Signer } from "./signer";

export interface RepuwaveClientOptions {
  apiKey: string;
  baseUrl?: string;
}

export interface RegisterAgentParams {
  displayName: string;
  publicKey: string;
}

export interface SignRequestParams {
  uaid: string;
  privateKey: string;
  body?: any;
}

export class RepuwaveClient {
  private apiKey: string;
  private baseUrl: string;

  constructor(options: RepuwaveClientOptions) {
    this.apiKey = options.apiKey;
    this.baseUrl = options.baseUrl || "https://api.repuwave.com/v1";
  }

  generateKeypair() {
    return Ed25519Signer.generateKeypair();
  }

  async registerAgent(params: RegisterAgentParams) {
    const response = await fetch(`${this.baseUrl}/agents/`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        display_name: params.displayName,
        public_key: params.publicKey,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to register agent: ${response.statusText}`);
    }

    return response.json();
  }

  signRequest(params: SignRequestParams) {
    const timestamp = Date.now() / 1000;
    const payload = Ed25519Signer.buildCanonicalPayload(params.uaid, timestamp, params.body);
    const signature = Ed25519Signer.sign(params.privateKey, payload);

    return {
      "X-Repuwave-UAID": params.uaid,
      "X-Repuwave-Timestamp": timestamp.toString(),
      "X-Repuwave-Signature": signature,
    };
  }
}
