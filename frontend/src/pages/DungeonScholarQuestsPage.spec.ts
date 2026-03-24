import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarQuestsPage from "./DungeonScholarQuestsPage.vue";

const getShopBalanceMock = vi.fn();

vi.mock("../api/shop", () => ({
  getShopBalance: (...args: unknown[]) => getShopBalanceMock(...args),
}));

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarQuestsPage, path: ROUTES.quests },
      { component: { template: "<div>Shop</div>" }, path: ROUTES.shop },
    ],
  });
}

describe("DungeonScholarQuestsPage", () => {
  beforeEach(() => {
    getShopBalanceMock.mockReset();
    getShopBalanceMock.mockResolvedValue({ asset_code: "COIN", balance: 1280 });
  });

  it("renders runtime coin balance from backend", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.quests);
    await router.isReady();

    const wrapper = mount(DungeonScholarQuestsPage, {
      global: { plugins: [router, i18n] },
    });

    await flushPromises();

    expect(wrapper.find(".status-pill--coins").text()).toContain("1,280 Coins");
  });

  it("shows fallback placeholder when backend balance request fails", async () => {
    getShopBalanceMock.mockRejectedValueOnce(new Error("network failed"));

    const router = createTestRouter();
    await router.push(ROUTES.quests);
    await router.isReady();

    const wrapper = mount(DungeonScholarQuestsPage, {
      global: { plugins: [router, i18n] },
    });

    await flushPromises();

    expect(wrapper.find(".status-pill--coins").text()).toContain("-- Coins");
  });
});
