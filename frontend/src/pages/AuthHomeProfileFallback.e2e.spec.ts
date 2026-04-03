import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent } from "vue";
import { createMemoryHistory, createRouter, RouterView } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarHomePage from "./DungeonScholarHomePage.vue";
import DungeonScholarLoginPage from "./DungeonScholarLoginPage.vue";

const mocks = vi.hoisted(() => ({
  loginWithPassword: vi.fn(),
  registerWithPassword: vi.fn(),
  getAuthErrorMessage: vi.fn(),
  getCurrentAuthUser: vi.fn(),
  getMyProfile: vi.fn(),
  getShopBalance: vi.fn(),
  listDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
  batchDeleteDocuments: vi.fn(),
  listRuns: vi.fn(),
  getSettings: vi.fn(),
  updateSettings: vi.fn(),
  getLeaderboard: vi.fn(),
}));

vi.mock("../api/auth", () => ({
  loginWithPassword: mocks.loginWithPassword,
  registerWithPassword: mocks.registerWithPassword,
  getCurrentAuthUser: mocks.getCurrentAuthUser,
  getAuthErrorMessage: mocks.getAuthErrorMessage,
  persistAuthSession: (payload: {
    user: { id: string; username: string; email: string };
    tokens: { access_token: string; refresh_token: string };
  }) => {
    window.localStorage.setItem("xirang:accessToken", payload.tokens.access_token);
    window.localStorage.setItem("xirang:token", payload.tokens.access_token);
    window.localStorage.setItem("xirang:refreshToken", payload.tokens.refresh_token);
    window.localStorage.setItem("xirang:userId", payload.user.id);
    window.localStorage.setItem("xirang:username", payload.user.username);
    window.localStorage.setItem("xirang:email", payload.user.email);
    window.localStorage.setItem("xirang:isAuthenticated", "true");
  },
}));

vi.mock("../api/profile", () => ({
  getMyProfile: mocks.getMyProfile,
}));

vi.mock("../api/shop", () => ({
  getShopBalance: mocks.getShopBalance,
}));

vi.mock("../api/documents", () => ({
  listDocuments: mocks.listDocuments,
  uploadDocument: mocks.uploadDocument,
  deleteDocument: mocks.deleteDocument,
  batchDeleteDocuments: mocks.batchDeleteDocuments,
}));

vi.mock("../api/runs", () => ({
  listRuns: mocks.listRuns,
}));

vi.mock("../api/settings", () => ({
  getSettings: mocks.getSettings,
  updateSettings: mocks.updateSettings,
}));

vi.mock("../api/leaderboard", () => ({
  getLeaderboard: mocks.getLeaderboard,
  getLeaderboardSnapshot: vi.fn(),
}));

const RootRouterView = defineComponent({
  components: { RouterView },
  template: "<RouterView />",
});

describe("Auth->Home profile fallback e2e", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();

    mocks.loginWithPassword.mockResolvedValue({
      user: {
        id: "user-1",
        username: "real-user",
        email: "real@example.com",
      },
      tokens: {
        access_token: "access-token",
        refresh_token: "refresh-token",
        token_type: "bearer",
        expires_in: 900,
      },
    });
    mocks.registerWithPassword.mockResolvedValue(undefined);
    mocks.getAuthErrorMessage.mockReturnValue("auth failed");
    mocks.getCurrentAuthUser.mockResolvedValue({
      id: "user-1",
      username: "real-user",
      email: "real@example.com",
      status: "active",
    });
    mocks.getMyProfile.mockRejectedValue(Object.assign(new Error("profile not found"), { status: 404 }));
    mocks.getShopBalance.mockResolvedValue({ asset_code: "COIN", balance: 0 });
    mocks.listDocuments.mockResolvedValue([]);
    mocks.listRuns.mockResolvedValue([]);
    mocks.getSettings.mockResolvedValue({
      theme_key: "system",
      language_code: "en",
      sound_enabled: true,
      haptic_enabled: true,
      daily_reminder_enabled: false,
    });
    mocks.updateSettings.mockResolvedValue(undefined);
    mocks.getLeaderboard.mockResolvedValue([]);
  });

  it("keeps logged-in username on Home when profile API returns 404", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { component: DungeonScholarLoginPage, path: ROUTES.login },
        { component: DungeonScholarHomePage, path: ROUTES.home },
      ],
    });

    await router.push(ROUTES.login);
    await router.isReady();

    const wrapper = mount(RootRouterView, {
      global: {
        plugins: [router, i18n],
      },
    });

    await wrapper.get('input[autocomplete="email"]').setValue("real@example.com");
    await wrapper.get('input[autocomplete="current-password"]').setValue("Password123!");
    await wrapper.get("form.email-form").trigger("submit.prevent");
    await flushPromises();
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.home);
    expect(window.localStorage.getItem("xirang:username")).toBe("real-user");
    expect(wrapper.find(".profile-name").text()).toBe("real-user");
    expect(wrapper.text()).not.toContain("Default user");
  });
});
