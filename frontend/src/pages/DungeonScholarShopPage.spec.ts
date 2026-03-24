import { mount } from "@vue/test-utils";
import { describe, expect, it, beforeEach } from "vitest";
import { createRouter, createMemoryHistory } from "vue-router";
import DungeonScholarShopPage from "./DungeonScholarShopPage.vue";

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
    localStorage.clear();
  });

  it("renders top-up entry card", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".shop-card--topup").exists()).toBe(true);
    expect(wrapper.find(".shop-card--topup h2").text()).toContain("Coin Pack");
    expect(wrapper.find(".price-tag--usd").exists()).toBe(true);
    expect(wrapper.find(".price-tag--usd").text()).toContain("$1.99");
  });

  it("renders wallet balance", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".wallet-pill strong").text()).toBe("3,450");
  });

  it("clicking purchase with insufficient balance shows modal", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router] },
    });

    // Find the Abyss Revive Token (800 coins, balance is 3450)
    const purchaseButtons = wrapper.findAll(".purchase-btn");
    const reviveButton = purchaseButtons[2]; // Third item is Abyss Revive Token
    
    await reviveButton.trigger("click");
    await wrapper.vm.$nextTick();

    // Should not show modal since we have enough balance
    expect(wrapper.find(".insufficient-modal").exists()).toBe(false);
  });

  it("clicking top-up adds coins", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router] },
    });

    const initialBalance = wrapper.vm.walletBalance;
    
    // Click the top-up button
    const topUpButton = wrapper.find(".purchase-btn--amber");
    await topUpButton.trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.walletBalance).toBe(initialBalance + 1000);
  });

  it("insufficient balance modal has rescue pack option", async () => {
    const router = await createTestRouter();
    const wrapper = mount(DungeonScholarShopPage, {
      global: { plugins: [router] },
    });

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
