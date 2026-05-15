import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { i18n } from "../i18n";
import DungeonScholarPricingPage from "./DungeonScholarPricingPage.vue";

const mocks = vi.hoisted(() => ({
  getRegion: vi.fn(),
  updateRegion: vi.fn(),
  createCheckout: vi.fn(),
}));

vi.mock("../api/payments", () => ({
  getRegion: mocks.getRegion,
  updateRegion: mocks.updateRegion,
  createCheckout: mocks.createCheckout,
}));

describe("DungeonScholarPricingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getRegion.mockResolvedValue({ region: "standard", prices: {} });
    mocks.createCheckout.mockResolvedValue({ checkout_url: "https://checkout.local", status: "created" });
  });

  it("不渲染内部地区调试控件", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/pricing", component: DungeonScholarPricingPage }],
    });
    await router.push("/pricing");
    await router.isReady();
    const wrapper = mount(DungeonScholarPricingPage, { global: { plugins: [i18n, router] } });

    expect(wrapper.find('[data-testid="region-banner"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain("Region: standard");
  });

  it("使用 Creem 统一后的订阅与代币价格", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/pricing", component: DungeonScholarPricingPage }],
    });
    await router.push("/pricing");
    await router.isReady();
    const wrapper = mount(DungeonScholarPricingPage, { global: { plugins: [i18n, router] } });

    expect(wrapper.text()).toContain("$8");
    expect(wrapper.text()).toContain("60");
    expect(wrapper.text()).toContain("300");
    expect(wrapper.text()).toContain("680");
    expect(wrapper.text()).toContain("1500");
    expect(wrapper.text()).toContain("3500");
  });

  it("点击代币包直接创建 Creem checkout", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/pricing", component: DungeonScholarPricingPage }],
    });
    await router.push("/pricing");
    await router.isReady();
    const wrapper = mount(DungeonScholarPricingPage, { global: { plugins: [i18n, router] } });

    await wrapper.findAll(".coin-card button")[0].trigger("click");

    expect(mocks.createCheckout).toHaveBeenCalledWith({ productType: "coin", plan: "60" });
  });
});
