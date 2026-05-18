import { afterEach, describe, expect, it, vi } from "vitest";
import { AUTH_SESSION_CLEARED_EVENT, clearAuthSessionStorage, isAuthenticated, setAuthenticatedFlag } from "./auth";

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

  it("notifies listeners when auth session storage is cleared", () => {
    localStorage.setItem("xirang:accessToken", "token");
    const listener = vi.fn();
    window.addEventListener(AUTH_SESSION_CLEARED_EVENT, listener);

    clearAuthSessionStorage();

    expect(localStorage.getItem("xirang:accessToken")).toBeNull();
    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener(AUTH_SESSION_CLEARED_EVENT, listener);
  });
});
