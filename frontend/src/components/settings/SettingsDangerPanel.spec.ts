import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { i18n } from "../../i18n";
import { ROUTES } from "../../constants/routes";
import SettingsDangerPanel from "./SettingsDangerPanel.vue";

const mockClearGameData = vi.fn().mockResolvedValue(undefined);
const mockDeleteAccount = vi.fn().mockResolvedValue(undefined);
const mockLogoutApi = vi.fn().mockResolvedValue(undefined);
const mockClearAuthSessionStorage = vi.fn();
const mockNavigateTo = vi.fn().mockResolvedValue(undefined);

vi.mock("../../api/settings", () => ({
  clearGameData: (...args: unknown[]) => mockClearGameData(...args),
}));

vi.mock("../../api/auth", () => ({
  clearAuthSessionStorage: (...args: unknown[]) => mockClearAuthSessionStorage(...args),
  deleteAccount: (...args: unknown[]) => mockDeleteAccount(...args),
  logoutApi: (...args: unknown[]) => mockLogoutApi(...args),
}));

vi.mock("../../composables/useRouteNavigation", () => ({
  useRouteNavigation: () => ({
    currentPath: { value: "/settings" },
    navigateTo: mockNavigateTo,
    routingTarget: { value: null },
  }),
}));

describe("SettingsDangerPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockClearGameData.mockResolvedValue(undefined);
    mockDeleteAccount.mockResolvedValue(undefined);
    mockLogoutApi.mockResolvedValue(undefined);
  });

  const createWrapper = async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: ROUTES.settings, component: SettingsDangerPanel }],
    });
    await router.push(ROUTES.settings);
    await router.isReady();
    const wrapper = mount(SettingsDangerPanel, {
      global: { plugins: [router, i18n] },
    });
    return { wrapper, router };
  };

  it("renders danger zone buttons", async () => {
    const { wrapper } = await createWrapper();
    expect(wrapper.text()).toContain("Clear All Data");
    expect(wrapper.text()).toContain("Delete Account");
    expect(wrapper.text()).toContain("Log Out");
  });

  it("shows confirm dialog when clear data button clicked", async () => {
    const { wrapper } = await createWrapper();
    const buttons = wrapper.findAll(".danger-btn");
    await buttons[0].trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[role='dialog']").exists()).toBe(true);
    expect(wrapper.text()).toContain("Clear All Game Data?");
  });

  it("shows confirm dialog when delete account button clicked", async () => {
    const { wrapper } = await createWrapper();
    const buttons = wrapper.findAll(".danger-btn");
    await buttons[1].trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[role='dialog']").exists()).toBe(true);
    expect(wrapper.text()).toContain("Delete Your Account?");
  });

  it("shows confirm dialog when logout button clicked", async () => {
    const { wrapper } = await createWrapper();
    const buttons = wrapper.findAll(".danger-btn");
    await buttons[2].trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[role='dialog']").exists()).toBe(true);
    expect(wrapper.text()).toContain("Log Out?");
  });

  it("closes dialog on cancel", async () => {
    const { wrapper } = await createWrapper();
    const buttons = wrapper.findAll(".danger-btn");
    await buttons[0].trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[role='dialog']").exists()).toBe(true);
    const cancelBtn = wrapper.find(".danger-confirm__btn--cancel");
    await cancelBtn.trigger("click");
    await wrapper.vm.$nextTick();
    expect(wrapper.find("[role='dialog']").exists()).toBe(false);
  });

  it("calls clearGameData on confirm for clear data action", async () => {
    const { wrapper } = await createWrapper();
    const buttons = wrapper.findAll(".danger-btn");
    await buttons[0].trigger("click");
    await wrapper.vm.$nextTick();
    const confirmBtn = wrapper.find(".danger-confirm__btn--warning");
    await confirmBtn.trigger("click");
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
    expect(mockClearGameData).toHaveBeenCalled();
  });

  it("calls deleteAccount and clears session on confirm", async () => {
    const { wrapper } = await createWrapper();
    const buttons = wrapper.findAll(".danger-btn");
    await buttons[1].trigger("click");
    await wrapper.vm.$nextTick();
    const confirmBtn = wrapper.find(".danger-confirm__btn--danger");
    await confirmBtn.trigger("click");
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
    expect(mockDeleteAccount).toHaveBeenCalled();
    expect(mockClearAuthSessionStorage).toHaveBeenCalled();
  });

  it("calls logoutApi and clears session on confirm", async () => {
    const { wrapper } = await createWrapper();
    const buttons = wrapper.findAll(".danger-btn");
    await buttons[2].trigger("click");
    await wrapper.vm.$nextTick();
    const confirmBtn = wrapper.find(".danger-confirm__btn--default");
    await confirmBtn.trigger("click");
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
    expect(mockLogoutApi).toHaveBeenCalled();
    expect(mockClearAuthSessionStorage).toHaveBeenCalled();
  });
});