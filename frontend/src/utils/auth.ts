const AUTH_FLAG_KEY = "xirang:isAuthenticated";
const AUTH_TOKEN_KEYS = ["xirang:token", "xirang:accessToken"] as const;

const decodeJwtPayload = (token: string): Record<string, unknown> | null => {
  const parts = token.split(".");
  if (parts.length !== 3) {
    return null;
  }

  try {
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = payload.padEnd(payload.length + ((4 - (payload.length % 4)) % 4), "=");
    const decoded = window.atob(padded);
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return null;
  }
};

const isTokenUsable = (token: string | null): boolean => {
  if (typeof token !== "string") {
    return false;
  }

  const normalized = token.trim();
  if (normalized.length === 0) {
    return false;
  }
  const payload = decodeJwtPayload(normalized);

  if (payload && typeof payload.exp === "number") {
    return payload.exp * 1000 > Date.now();
  }

  return /^[A-Za-z0-9._-]{24,}$/.test(normalized);
};

export const isAuthenticated = (): boolean => {
  if (typeof window === "undefined") {
    return false;
  }

  const storage = window.localStorage;
  return AUTH_TOKEN_KEYS.some((key) => isTokenUsable(storage.getItem(key)));
};

export const setAuthenticatedFlag = (authenticated: boolean): void => {
  if (typeof window === "undefined") {
    return;
  }

  if (authenticated) {
    window.localStorage.setItem(AUTH_FLAG_KEY, "true");
    return;
  }

  window.localStorage.removeItem(AUTH_FLAG_KEY);
};
