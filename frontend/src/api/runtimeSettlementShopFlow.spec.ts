import { afterEach, describe, expect, it, vi } from "vitest";
import { submitAnswer } from "./runs";
import { getShopBalance, getShopInventory, purchaseShopItem } from "./shop";

const fetchMock = vi.fn();

vi.stubGlobal("fetch", fetchMock);

describe("runtime settlement to shop flow", () => {
  afterEach(() => {
    fetchMock.mockReset();
    localStorage.clear();
  });

  it("keeps balance and inventory consistent from settlement to purchase", async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () =>
          JSON.stringify({
            is_correct: true,
            settlement: {
              run_id: "run-1",
              xp_earned: 120,
              coins_earned: 50,
              combo_max: 1,
              accuracy: 1,
              correct_count: 1,
              total_count: 1,
            },
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ asset_code: "COIN", balance: 50 }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () =>
          JSON.stringify({
            id: "purchase-1",
            user_id: "00000000-0000-0000-0000-000000000001",
            offer_id: "offer-xp",
            item_code: "xp_boost_potion",
            price_asset_code: "COIN",
            price_amount: 20,
            status: "completed",
            purchased_at: "2026-03-19T00:00:00Z",
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ asset_code: "COIN", balance: 30 }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () =>
          JSON.stringify({
            items: [
              {
                user_id: "00000000-0000-0000-0000-000000000001",
                item_code: "xp_boost_potion",
                quantity: 1,
                updated_at: "2026-03-19T00:00:00Z",
              },
            ],
          }),
      });

    const settlementResult = await submitAnswer("run-1", "question-1", ["option-1"]);
    const balanceAfterSettlement = await getShopBalance();
    const purchase = await purchaseShopItem({
      offerId: "offer-xp",
      idempotencyKey: "idem-flow-1",
    });
    const balanceAfterPurchase = await getShopBalance();
    const inventory = await getShopInventory();

    expect(settlementResult.settlement?.coins_earned).toBe(50);
    expect(balanceAfterSettlement.balance).toBe(50);
    expect(purchase.status).toBe("completed");
    expect(balanceAfterPurchase.balance).toBe(30);
    expect(inventory[0]?.item_code).toBe("xp_boost_potion");
    expect(inventory[0]?.quantity).toBe(1);

    const calledPaths = fetchMock.mock.calls.map((args) => args[0]);
    expect(calledPaths).toEqual([
      "/api/v1/runs/run-1/answers",
      "/api/v1/shop/balance",
      "/api/v1/shop/purchase",
      "/api/v1/shop/balance",
      "/api/v1/shop/inventory",
    ]);
  });
});
