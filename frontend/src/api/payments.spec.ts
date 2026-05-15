import { afterEach, describe, expect, it, vi } from "vitest";
import { createCheckout, getRegion, updateRegion } from "./payments";

const fetchMock = vi.fn();
vi.stubGlobal("fetch", fetchMock);

describe("payments api", () => {
  afterEach(() => {
    fetchMock.mockReset();
    localStorage.clear();
  });

  it("posts checkout payload", async () => {
    fetchMock.mockResolvedValueOnce({ ok: true, status: 200, text: async () => JSON.stringify({ checkout_url: "https://c", status: "created" }) });
    await createCheckout({ productType: "subscription", plan: "monthly" });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/payments/checkout",
      expect.objectContaining({ method: "POST", body: JSON.stringify({ product_type: "subscription", plan: "monthly" }) }),
    );
  });

  it("gets region", async () => {
    fetchMock.mockResolvedValueOnce({ ok: true, status: 200, text: async () => JSON.stringify({ region: "standard", prices: {} }) });
    await getRegion();
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/payments/region", expect.objectContaining({ method: "GET" }));
  });

  it("updates region", async () => {
    fetchMock.mockResolvedValueOnce({ ok: true, status: 200, text: async () => JSON.stringify({ region: "premium", prices: {} }) });
    await updateRegion("premium");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/payments/region",
      expect.objectContaining({ method: "PUT", body: JSON.stringify({ region: "premium" }) }),
    );
  });
});
