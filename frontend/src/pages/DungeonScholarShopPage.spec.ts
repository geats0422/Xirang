import { mount } from "@vue/test-utils";
import { describe, expect, it, beforeEach, vi } from "vitest";
import { createRouter, createMemoryHistory } from "vue-router";
import { i18n } from "../i18n";
import DungeonScholarShopPage from "./DungeonScholarShopPage.vue";

const mocks = vi.hoisted(() => ({
  getShopBalance: vi.fn(),
  listShopItems: vi.fn(),
  purchaseShopItem: vi.fn(),
}));

vi.mock("../api/shop", () => ({
  getShopBalance: mocks.getShopBalance,
  listShopItems: mocks.listShopItems,
  purchaseShopItem: mocks.purchaseShopItem,
}));

const createTestRouter = async () => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/shop", component: { template: "<div />" } }],
  });
  await router.push("/shop");
  await router.isReady();
  return router;
};

describe("DungeonScholarShopPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mocks.getShopBalance.mockResolvedValue({ asset_code: "COIN", balance: 3450 });
    mocks.listShopItems.mockResolvedValue([
      { id: "offer-1", item_code: "streak_freeze", rarity: "common", price_amount: 120 },
      { id: "offer-2", item_code: "xp_boost", rarity: "uncommon", price_amount: 260 },
      { id: "offer-3", item_code: "revival", rarity: "rare", price_amount: 800 },
    ]);
    mocks.purchaseShopItem.mockResolvedValue({});
  });

  it("renders top-up entry card", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".shop-card--topup").exists()).toBe(true);
    expect(wrapper.find(".shop-card--topup h2").text()).toContain("Coin Pack");
    expect(wrapper.find(".price-tag--usd").exists()).toBe(true);
    expect(wrapper.find(".price-tag--usd").text()).toContain("$1.99");
  });

  it("renders wallet balance", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".wallet-pill strong").text()).toBe("3,450");
  });

  it("clicking purchase with insufficient balance shows modal", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    // Find the Abyss Revive Token (800 coins, balance is 3450)
    const purchaseButtons = wrapper.findAll(".purchase-btn");
    const reviveButton = purchaseButtons[2]; // Third item is Abyss Revive Token
    
    await reviveButton.trigger("click");
    await wrapper.vm.$nextTick();

    // Should not show modal since we have enough balance
    expect(wrapper.find(".insufficient-modal").exists()).toBe(false);
  });

  it("clicking top-up triggers purchase request", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    // Click the top-up button
    const topUpButton = wrapper.find(".purchase-btn--amber");
    await topUpButton.trigger("click");
    await wrapper.vm.$nextTick();

    expect(mocks.purchaseShopItem).toHaveBeenCalledTimes(1);
    expect(mocks.purchaseShopItem).toHaveBeenCalledWith(
      expect.objectContaining({
        offerId: "top_up",
      }),
    );
  });

  it("insufficient balance modal has rescue pack option", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    // Set balance low and trigger purchase
    wrapper.vm.walletBalance = 100;
    await wrapper.vm.$nextTick();
    
    // Click purchase on expensive item
    const purchaseButtons = wrapper.findAll(".purchase-btn");
    await purchaseButtons[2].trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".insufficient-modal").exists()).toBe(true);
    expect(wrapper.find(".rescue-btn").exists()).toBe(true);
    expect(wrapper.find(".rescue-btn").text()).toContain("$1.99");
  });
});
