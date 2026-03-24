import { afterEach, describe, expect, it, vi } from "vitest";
import { getShopBalance, getShopInventory, listShopItems, purchaseShopItem } from "./shop";

const fetchMock = vi.fn();

vi.stubGlobal("fetch", fetchMock);

describe("shop api", () => {
  afterEach(() => {
    fetchMock.mockReset();
    localStorage.clear();
  });

  it("requests shop items list", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => "[]",
    });

    await listShopItems();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/shop/items",
      expect.objectContaining({
        method: "GET",
      }),
    );
  });

  it("requests balance with auth headers", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ asset_code: "COIN", balance: 20 }),
    });

    await getShopBalance();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/shop/balance",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: expect.stringMatching(/^Bearer\s+/),
          "X-User-Id": expect.any(String),
        }),
      }),
    );
  });

  it("posts purchase payload with offer_id and idempotency_key", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          id: "purchase-1",
          user_id: "00000000-0000-0000-0000-000000000001",
          offer_id: "offer-1",
          item_code: "xp_boost",
          price_asset_code: "COIN",
          price_amount: 200,
          status: "completed",
          purchased_at: "2026-03-19T00:00:00Z",
        }),
    });

    await purchaseShopItem({
      offerId: "offer-1",
      idempotencyKey: "idem-1",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/shop/purchase",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          offer_id: "offer-1",
          idempotency_key: "idem-1",
        }),
      }),
    );
  });

  it("requests inventory list with auth headers", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ items: [] }),
    });

    await getShopInventory();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/shop/inventory",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          Authorization: expect.stringMatching(/^Bearer\s+/),
          "X-User-Id": expect.any(String),
        }),
      }),
    );
  });
});
