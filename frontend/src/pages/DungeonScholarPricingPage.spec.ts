import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { i18n } from "../i18n";
import DungeonScholarPricingPage from "./DungeonScholarPricingPage.vue";

const discordInviteUrl = "https://discord.gg/tN8CZGAcdM";

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

  it("市场验证阶段遮住 Pro 方案但保留原方案内容", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/pricing", component: DungeonScholarPricingPage }],
    });
    await router.push("/pricing");
    await router.isReady();
    const wrapper = mount(DungeonScholarPricingPage, { global: { plugins: [i18n, router] } });

    expect(wrapper.text()).toContain("$8");
    expect(wrapper.text()).toContain("Pro Scholar");
    expect(wrapper.find('[data-testid="pro-validation-overlay"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Market validation stage");

    await wrapper.find('[data-testid="pro-subscribe-button"]').trigger("click");

    expect(mocks.createCheckout).not.toHaveBeenCalledWith({ productType: "subscription", plan: "monthly" });
  });

  it("市场验证阶段遮住但不删除高级学者方案", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/pricing", component: DungeonScholarPricingPage }],
    });
    await router.push("/pricing");
    await router.isReady();
    const wrapper = mount(DungeonScholarPricingPage, { global: { plugins: [i18n, router] } });

    expect(wrapper.text()).toContain("Pro Scholar");
    expect(wrapper.text()).toContain("$8");
    expect(wrapper.find('[data-testid="pro-validation-overlay"]').exists()).toBe(true);

    await wrapper.find('[data-testid="pro-validation-overlay"] button').trigger("click");

    expect(mocks.createCheckout).not.toHaveBeenCalledWith({ productType: "subscription", plan: "monthly" });
  });

  it("does not render Creem review risky marketing copy or placeholder links", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/pricing", component: DungeonScholarPricingPage }],
    });
    await router.push("/pricing");
    await router.isReady();
    const wrapper = mount(DungeonScholarPricingPage, { global: { plugins: [i18n, router] } });

    expect(wrapper.findAll('a[href="#"]')).toHaveLength(0);
    expect(wrapper.find(`.site-footer__links a[href="${discordInviteUrl}"]`).exists()).toBe(true);
    expect(wrapper.text()).not.toContain("Community");
    expect(wrapper.text()).not.toMatch(/10,000|10\.000|thousands|WeChat Pay|Alipay/i);
  });
});
