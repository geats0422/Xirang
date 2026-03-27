import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  getCurrentAuthUser: vi.fn(),
  getMyProfile: vi.fn(),
  getShopBalance: vi.fn(),
  listDocuments: vi.fn(),
  listRuns: vi.fn(),
  getSettings: vi.fn(),
  getAiConfig: vi.fn(),
  getLeaderboard: vi.fn(),
}));

vi.mock("../api/auth", () => ({
  getCurrentAuthUser: mocks.getCurrentAuthUser,
}));

vi.mock("../api/profile", () => ({
  getMyProfile: mocks.getMyProfile,
}));

vi.mock("../api/shop", () => ({
  getShopBalance: mocks.getShopBalance,
}));

vi.mock("../api/documents", () => ({
  listDocuments: mocks.listDocuments,
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
  batchDeleteDocuments: vi.fn(),
}));

vi.mock("../api/runs", () => ({
  listRuns: mocks.listRuns,
}));

vi.mock("../api/settings", () => ({
  getSettings: mocks.getSettings,
  getAiConfig: mocks.getAiConfig,
  updateSettings: vi.fn(),
}));

vi.mock("../api/leaderboard", () => ({
  getLeaderboard: mocks.getLeaderboard,
}));

import { useScholarData } from "./useScholarData";

const buildProfile = (displayName: string | null) => ({
  user_id: "user-1",
  display_name: displayName,
  avatar_url: null,
  bio: null,
  verified_badge: false,
  tier_label: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
});

describe("useScholarData profile name priority", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();

    mocks.getShopBalance.mockResolvedValue({ asset_code: "COIN", balance: 0 });
    mocks.listDocuments.mockResolvedValue([]);
    mocks.listRuns.mockResolvedValue([]);
    mocks.getCurrentAuthUser.mockResolvedValue({
      id: "user-1",
      username: "testuser2",
      email: "briannr.an.g.el.286@gmail.com",
      status: "active",
    });
    mocks.getSettings.mockResolvedValue({
      theme_key: "system",
      language_code: "en",
      sound_enabled: true,
      haptic_enabled: true,
      daily_reminder_enabled: false,
    });
    mocks.getAiConfig.mockResolvedValue({
      provider: "openai-compatible",
      base_url: "https://integrate.api.nvidia.com/v1",
      model: "nvidia/nemotron-3-nano-30b-a3b",
      configured: true,
    });
    mocks.getLeaderboard.mockResolvedValue([]);
  });

  it("uses display_name first when available", async () => {
    window.localStorage.setItem("xirang:isAuthenticated", "true");
    window.localStorage.setItem("xirang:username", "testuser2");
    mocks.getMyProfile.mockResolvedValue(buildProfile("Scholar Display"));

    const state = useScholarData();
    await state.hydrate();

    expect(state.profileName.value).toBe("Scholar Display");
  });

  it("falls back to username when display_name is empty", async () => {
    window.localStorage.setItem("xirang:isAuthenticated", "true");
    window.localStorage.setItem("xirang:username", "testuser2");
    mocks.getMyProfile.mockResolvedValue(buildProfile(null));

    const state = useScholarData();
    await state.hydrate();

    expect(state.profileName.value).toBe("testuser2");
  });

  it("falls back to Default user when unauthenticated", async () => {
    window.localStorage.setItem("xirang:isAuthenticated", "false");
    window.localStorage.setItem("xirang:username", "testuser2");
    mocks.getMyProfile.mockResolvedValue(buildProfile(null));

    const state = useScholarData();
    await state.hydrate();

    expect(state.profileName.value).toBe("Default user");
  });

  it("hydrates linked email from auth me", async () => {
    window.localStorage.setItem("xirang:isAuthenticated", "true");
    window.localStorage.setItem("xirang:email", "cached@example.com");
    mocks.getMyProfile.mockResolvedValue(buildProfile(null));
    mocks.getCurrentAuthUser.mockResolvedValue({
      id: "user-1",
      username: "testuser2",
      email: "briannr.an.g.el.286@gmail.com",
      status: "active",
    });

    const state = useScholarData();
    await state.hydrate();

    expect(state.linkedEmail.value).toBe("briannr.an.g.el.286@gmail.com");
  });
});
