import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, NetworkError, apiRequest, resolveUrl } from "./http";

const fetchMock = vi.fn();

vi.stubGlobal("fetch", fetchMock);

afterEach(() => {
  fetchMock.mockReset();
  vi.useRealTimers();
});

describe("resolveUrl", () => {
  it("returns relative path when base URL is empty", () => {
    expect(resolveUrl("/api/v1/test", "")).toBe("/api/v1/test");
    expect(resolveUrl("api/v1/test", "")).toBe("/api/v1/test");
  });

  it("prepends base URL when configured", () => {
    expect(resolveUrl("/api/v1/test", "http://localhost:8000")).toBe("http://localhost:8000/api/v1/test");
    expect(resolveUrl("api/v1/test", "http://localhost:8000/")).toBe("http://localhost:8000/api/v1/test");
  });

  it("returns absolute URLs unchanged", () => {
    expect(resolveUrl("http://example.com/api", "http://localhost:8000")).toBe("http://example.com/api");
  });
});

describe("network errors", () => {
  it("throws NetworkError on fetch rejection", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    const requestPromise = apiRequest("/api/v1/test");

    await expect(requestPromise).rejects.toBeInstanceOf(NetworkError);
  });
});

describe("timeout errors", () => {
  it("throws ApiError with status 408 on timeout", async () => {
    vi.useFakeTimers();

    fetchMock.mockImplementationOnce((_url: string, init?: RequestInit) => {
      return new Promise((_, reject) => {
        const abortSignal = init?.signal;
        abortSignal?.addEventListener(
          "abort",
          () => {
            reject(new DOMException("Aborted", "AbortError"));
          },
          { once: true },
        );
      });
    });

    const requestPromise = apiRequest("/api/v1/slow", { timeoutMs: 50 });
    const capturedErrorPromise = requestPromise.catch((err: unknown) => err);

    await vi.advanceTimersByTimeAsync(55);

    const error = await capturedErrorPromise;
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 408,
      detail: null,
    });
  });
});

describe("business errors", () => {
  it("throws ApiError with status and detail on 4xx", async () => {
    const detail = { message: "Invalid input", code: "VALIDATION_ERROR" };

    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 422,
      text: async () => JSON.stringify(detail),
    });

    const requestPromise = apiRequest("/api/v1/auth/register");

    const error = await requestPromise.catch((err: unknown) => err);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 422,
      detail,
    });
  });

  it("throws ApiError with status and detail on 5xx", async () => {
    const detail = { message: "Upstream service unavailable" };

    fetchMock.mockResolvedValueOnce({
      ok: false,
      status: 503,
      text: async () => JSON.stringify(detail),
    });

    const requestPromise = apiRequest("/api/v1/auth/login");

    const error = await requestPromise.catch((err: unknown) => err);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 503,
      detail,
    });
  });
});
