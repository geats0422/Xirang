import { mount } from "@vue/test-utils";
import { describe, expect, it, beforeEach, vi } from "vitest";
import { createRouter, createMemoryHistory } from "vue-router";
import { i18n } from "../i18n";
import DungeonScholarShopPage from "./DungeonScholarShopPage.vue";

const mocks = vi.hoisted(() => ({
  getShopBalance: vi.fn(),
  listShopItems: vi.fn(),
  purchaseShopItem: vi.fn(),
  getShopInventory: vi.fn(),
  getActiveEffects: vi.fn(),
  useItem: vi.fn(),
}));

vi.mock("../api/shop", () => ({
  getShopBalance: mocks.getShopBalance,
  listShopItems: mocks.listShopItems,
  purchaseShopItem: mocks.purchaseShopItem,
  getShopInventory: mocks.getShopInventory,
  getActiveEffects: mocks.getActiveEffects,
  useItem: mocks.useItem,
}));

vi.mock("../composables/useInventory", () => ({
  useInventory: () => ({
    inventory: { value: [] },
    refresh: vi.fn(),
    quantityOf: () => 0,
  }),
}));

vi.mock("../composables/useActiveEffects", () => ({
  useActiveEffects: () => ({
    effects: { value: [] },
    activeXpBoost: null,
    activeShield: null,
    refresh: vi.fn(),
  }),
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
    mocks.getShopInventory.mockResolvedValue([]);
    mocks.getActiveEffects.mockResolvedValue({ effects: [] });
    mocks.useItem.mockResolvedValue({ success: true, quantity_remaining: 0 });
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

  it("renders shop item cards", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    const cards = wrapper.findAllComponents({ name: "ShopItemCard" });
    expect(cards.length).toBeGreaterThan(0);
  });

  it("clicking purchase button triggers purchase flow", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    const cards = wrapper.findAllComponents({ name: "ShopItemCard" });
    expect(cards.length).toBeGreaterThan(0);
  });

  it("shows bag modal when clicking bag button", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    const bagButton = wrapper.find(".bag-btn");
    await bagButton.trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".bag-modal").exists()).toBe(true);
  });

  it("bag modal shows empty state when no inventory", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    const bagButton = wrapper.find(".bag-btn");
    await bagButton.trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".bag-modal").exists()).toBe(true);
    expect(wrapper.find(".bag-empty").exists()).toBe(true);
  });
});
