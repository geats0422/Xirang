import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarSettingsPage from "./DungeonScholarSettingsPage.vue";

const mocks = vi.hoisted(() => ({
  getSubscription: vi.fn(),
  getRegion: vi.fn(),
  cancelSubscription: vi.fn(),
  updateRegion: vi.fn(),
  createCheckout: vi.fn(),
}));

vi.mock("../api/payments", () => ({
  getSubscription: mocks.getSubscription,
  getRegion: mocks.getRegion,
  cancelSubscription: mocks.cancelSubscription,
  updateRegion: mocks.updateRegion,
  createCheckout: mocks.createCheckout,
}));

describe("DungeonScholarSettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getSubscription.mockResolvedValue({ status: "free", tier: null, expires_at: null });
    mocks.getRegion.mockResolvedValue({ region: "standard", prices: {} });
    mocks.createCheckout.mockResolvedValue({ checkout_url: "https://checkout.local" });
  });

  it("renders extracted settings sections", async () => {
    i18n.global.locale.value = "en";
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ component: DungeonScholarSettingsPage, path: ROUTES.settings }],
    });

    await router.push(ROUTES.settings);
    await router.isReady();

    const wrapper = mount(DungeonScholarSettingsPage, {
      global: {
        plugins: [router, i18n],
      },
    });

    expect(wrapper.text()).toContain("Game Preferences");
    expect(wrapper.text()).toContain("The Forge Engine");
    expect(wrapper.text()).toContain("Danger Zone");
    expect(wrapper.text()).toContain("Subscription Management");
  });

  it("opens subscription modal when clicking manage plan", async () => {
    i18n.global.locale.value = "zh-CN";
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ component: DungeonScholarSettingsPage, path: ROUTES.settings }],
    });

    await router.push(ROUTES.settings);
    await router.isReady();

    const wrapper = mount(DungeonScholarSettingsPage, {
      global: {
        plugins: [router, i18n],
      },
    });
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="subscription-modal"]').exists()).toBe(false);

    const manageButton = wrapper.find(".plan-btn");
    await manageButton.trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="subscription-modal"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="subscription-modal"]').text()).toContain("订阅管理");
  });

  it("pauses Pro subscription checkout during market validation", async () => {
    i18n.global.locale.value = "en";
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ component: DungeonScholarSettingsPage, path: ROUTES.settings }],
    });

    await router.push(ROUTES.settings);
    await router.isReady();

    const wrapper = mount(DungeonScholarSettingsPage, {
      global: {
        plugins: [router, i18n],
      },
    });
    await wrapper.vm.$nextTick();

    await wrapper.find(".plan-btn").trigger("click");
    await wrapper.vm.$nextTick();

    const upgradeButton = wrapper.find('[data-testid="upgrade-pro"]');
    expect(upgradeButton.exists()).toBe(true);
    expect(upgradeButton.attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="subscription-modal"]').text()).toContain("Membership opens later");

    await upgradeButton.trigger("click");

    expect(mocks.createCheckout).not.toHaveBeenCalled();
  });
});
