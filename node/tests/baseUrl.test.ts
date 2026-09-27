/**
 * The API host comes from REPUWAVE_API_URL when the caller does not pass one.
 * The planned public host does not answer yet, so defaulting to it outright
 * made code that followed the README fail on its first call.
 */
import { RepuwaveService } from "../src/service";

describe("RepuwaveService base URL", () => {
  const original = process.env.REPUWAVE_API_URL;
  let seen: string[] = [];

  beforeEach(() => {
    seen = [];
    global.fetch = jest.fn(async (url: string | URL | Request) => {
      seen.push(String(url));
      return new Response(JSON.stringify({ score: 50 }), { status: 200 });
    }) as unknown as typeof fetch;
  });
  afterEach(() => {
    if (original === undefined) delete process.env.REPUWAVE_API_URL;
    else process.env.REPUWAVE_API_URL = original;
  });

  const check = (service: RepuwaveService) => service.verify({ uaid: "u", signature: "s", timestamp: "1" });

  it("uses REPUWAVE_API_URL", async () => {
    process.env.REPUWAVE_API_URL = "http://repuwave.test/v1/";
    await check(new RepuwaveService({ apiKey: "k" }));
    expect(seen[0]).toBe("http://repuwave.test/v1/verify/u/");
  });

  it("lets an explicit baseUrl win", async () => {
    process.env.REPUWAVE_API_URL = "http://repuwave.test/v1";
    await check(new RepuwaveService({ apiKey: "k", baseUrl: "http://other.test/v1" }));
    expect(seen[0]).toBe("http://other.test/v1/verify/u/");
  });
});
