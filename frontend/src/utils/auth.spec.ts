import { afterEach, describe, expect, it } from "vitest";
import { isAuthenticated, setAuthenticatedFlag } from "./auth";

const makeJwt = (payload: Record<string, unknown>) => {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = btoa(JSON.stringify(payload));
  return `${header}.${body}.signature`;
};

afterEach(() => {
  localStorage.clear();
});

describe("auth helpers", () => {
  it("does not authenticate from flag alone", () => {
    setAuthenticatedFlag(true);

    expect(isAuthenticated()).toBe(false);
  });

  it("authenticates with a non-expired controlled token", () => {
    localStorage.setItem(
      "xirang:accessToken",
      makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600 }),
    );

    expect(isAuthenticated()).toBe(true);
  });
});
