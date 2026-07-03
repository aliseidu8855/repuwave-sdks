import fetch from "node-fetch";

export interface RepuwaveServiceOptions {
  apiKey: string;
  baseUrl?: string;
}

export interface VerifyParams {
  uaid: string;
  signature: string;
  timestamp: string | number;
}

export interface ReportParams {
  uaid: string;
  outcome: string;
  weight: number;
  context: string;
}

export class RepuwaveService {
  private apiKey: string;
  private baseUrl: string;

  constructor(options: RepuwaveServiceOptions) {
    this.apiKey = options.apiKey;
    this.baseUrl = options.baseUrl || "https://api.repuwave.com/v1";
  }

  async verify(params: VerifyParams) {
    const response = await fetch(`${this.baseUrl}/verify/${params.uaid}/`, {
      method: "GET",
      headers: {
        "Authorization": `ApiKey ${this.apiKey}`,
        "X-Repuwave-Signature": params.signature,
        "X-Repuwave-Timestamp": params.timestamp.toString(),
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return { verified: false, score: 0, trust_level: "UNKNOWN", uaid: params.uaid };
      }
      throw new Error(`Failed to verify agent: ${response.statusText}`);
    }

    return response.json();
  }

  async report(params: ReportParams) {
    const response = await fetch(`${this.baseUrl}/report/`, {
      method: "POST",
      headers: {
        "Authorization": `ApiKey ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        uaid: params.uaid,
        outcome: params.outcome,
        weight: params.weight,
        context: params.context,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to report outcome: ${response.statusText}`);
    }

    return true;
  }
}
