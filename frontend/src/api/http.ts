type RequestMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const DEFAULT_TIMEOUT_MS = 10000;

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

type RequestOptions = {
  method?: RequestMethod;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeoutMs?: number;
};

const resolveUrl = (path: string): string => {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};

export const apiRequest = async <T>(path: string, options: RequestOptions = {}): Promise<T> => {
  const { method = "GET", body, headers = {}, signal, timeoutMs = DEFAULT_TIMEOUT_MS } = options;
  const isFormData = body instanceof FormData;

  const requestHeaders: Record<string, string> = {
    ...headers,
  };
  if (!isFormData) {
    requestHeaders["Content-Type"] = requestHeaders["Content-Type"] ?? "application/json";
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(resolveUrl(path), {
      method,
      headers: requestHeaders,
      body:
        body === undefined
          ? undefined
          : isFormData
            ? (body as FormData)
            : JSON.stringify(body),
      signal: signal ?? controller.signal,
    });

    clearTimeout(timeoutId);

    const text = await response.text();
    let data: unknown = null;
    if (text) {
      try {
        data = JSON.parse(text) as unknown;
      } catch {
        data = text;
      }
    }

    if (!response.ok) {
      throw new ApiError(`Request failed with status ${response.status}`, response.status, data);
    }

    return data as T;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiError(`Request timed out after ${timeoutMs}ms`, 408, null);
    }
    throw error;
  }
};
