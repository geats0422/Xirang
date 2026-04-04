import { clearAuthSessionStorage, refreshToken } from "./auth";
import { getAuthHeaders } from "./authHeaders";

type RequestMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
const DEFAULT_TIMEOUT_MS = 10000;

// Shared promise to avoid multiple simultaneous refresh attempts
let refreshingPromise: Promise<string> | null = null;

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NetworkError";
  }
}

type RequestOptions = {
  method?: RequestMethod;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeoutMs?: number;
};

export const resolveUrl = (path: string, baseUrl: string = API_BASE_URL): string => {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const normalizedBaseUrl = baseUrl.replace(/\/+$/, "");
  if (!normalizedBaseUrl) {
    return normalizedPath;
  }
  return `${normalizedBaseUrl}${normalizedPath}`;
};

const parseResponseData = async (response: Response): Promise<unknown> => {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
};

const getNewAccessToken = async (): Promise<string> => {
  if (refreshingPromise) {
    return refreshingPromise;
  }
  refreshingPromise = refreshToken()
    .then((tokens) => {
      refreshingPromise = null;
      return tokens.access_token;
    })
    .catch((err) => {
      refreshingPromise = null;
      clearAuthSessionStorage();
      throw err;
    });
  return refreshingPromise;
};

export const apiRequest = async <T>(path: string, options: RequestOptions = {}): Promise<T> => {
  const { method = "GET", body, headers = {}, signal, timeoutMs = DEFAULT_TIMEOUT_MS } = options;
  const isFormData = body instanceof FormData;

  const authHeaders = getAuthHeaders();
  const requestHeaders: Record<string, string> = { ...authHeaders, ...headers };
  if (!isFormData) {
    requestHeaders["Content-Type"] = requestHeaders["Content-Type"] ?? "application/json";
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  if (signal) {
    if (signal.aborted) {
      controller.abort();
    } else {
      signal.addEventListener("abort", () => controller.abort(), { once: true });
    }
  }

  try {
    const response = await fetch(resolveUrl(path), {
      method,
      headers: requestHeaders,
      body: body === undefined ? undefined : isFormData ? (body as FormData) : JSON.stringify(body),
      signal: controller.signal,
    });

    const data = await parseResponseData(response);

    if (!response.ok) {
      if (response.status === 401) {
        throw new ApiError("Unauthorized - token may be expired", 401, data);
      }
      throw new ApiError(`Request failed with status ${response.status}`, response.status, data);
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        try {
          const newToken = await getNewAccessToken();
          const newAuthHeaders: Record<string, string> = { Authorization: `Bearer ${newToken}` };
          const newRequestHeaders = { ...newAuthHeaders, ...headers };
          if (!isFormData) {
            newRequestHeaders["Content-Type"] = newRequestHeaders["Content-Type"] ?? "application/json";
          }
          const response = await fetch(resolveUrl(path), {
            method,
            headers: newRequestHeaders,
            body: body === undefined ? undefined : isFormData ? (body as FormData) : JSON.stringify(body),
            signal: controller.signal,
          });
          const data = await parseResponseData(response);
          if (!response.ok) {
            throw new ApiError(`Request failed with status ${response.status}`, response.status, data);
          }
          return data as T;
        } catch {
          throw error;
        }
      }
      throw error;
    }
    if (
      (error instanceof Error && error.name === "AbortError")
      || (typeof error === "object" && error !== null && "name" in error && (error as { name: string }).name === "AbortError")
    ) {
      throw new ApiError(`Request timed out after ${timeoutMs}ms`, 408, null);
    }
    if (error instanceof TypeError) {
      throw new NetworkError(
        "Network error: Unable to reach the server. Please check your connection and try again.",
      );
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
};
