/**
 * Repuwave Node SDK — Error types.
 */

/** Base class for all Repuwave SDK errors. */
export class RepuwaveError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RepuwaveError";
  }
}

/** Raised when signing fails (bad key material, etc.). */
export class SigningError extends RepuwaveError {
  constructor(message: string) {
    super(message);
    this.name = "SigningError";
  }
}

/** Raised when an API request returns a non-2xx response. */
export class ApiError extends RepuwaveError {
  readonly status: number;
  readonly code: string;
  readonly body: unknown;

  constructor(message: string, status: number, code: string, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.body = body;
  }
}
