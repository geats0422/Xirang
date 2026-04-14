import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarLeaderboardPage from "./DungeonScholarLeaderboardPage.vue";

const mocks = vi.hoisted(() => ({
  getLeaderboardSnapshot: vi.fn(),
  hydrate: vi.fn(),
}));

vi.mock("../api/leaderboard", () => ({
  getLeaderboardSnapshot: mocks.getLeaderboardSnapshot,
}));

vi.mock("../composables/useScholarData", () => ({
  useScholarData: () => ({
    profileName: ref("Test Scholar"),
    profileLevel: ref("Level 9 Scholar"),
    hydrate: mocks.hydrate,
  }),
}));

const createSnapshot = (overrides?: Partial<Awaited<ReturnType<typeof mocks.getLeaderboardSnapshot>>>) => ({
  scope: "global",
  limit: 25,
  offset: 0,
  has_more: false,
  entries: [
    {
      user_id: "00000000-0000-0000-0000-000000000001",
      display_name: "Alpha",
      total_xp: 2500,
      rank: 1,
      level: 6,
      energy_points: 0,
      is_current_user: false,
    },
  ],
  viewer: {
    user_id: "00000000-0000-0000-0000-000000000099",
    display_name: "Viewer",
    total_xp: 3450,
    rank: 2,
    level: 7,
    energy_points: 4,
    daily_focus: [
      {
        document_id: "00000000-0000-0000-0000-000000000777",
        title: "Art of War",
        progress_current: 3,
        progress_total: 5,
        progress_text: "3/5",
      },
    ],
  },
  ...overrides,
});

const createTestRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: [{ component: DungeonScholarLeaderboardPage, path: ROUTES.leaderboard }],
  });

describe("DungeonScholarLeaderboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.hydrate.mockResolvedValue(undefined);
    mocks.getLeaderboardSnapshot.mockResolvedValue(createSnapshot());
  });

  it("renders summary and standings from snapshot response", async () => {
    const router = createTestRouter();

    await router.push(ROUTES.leaderboard);
    await router.isReady();

    const wrapper = mount(DungeonScholarLeaderboardPage, {
      global: {
        plugins: [router, i18n],
      },
    });
    await flushPromises();

    expect(wrapper.text()).toContain("Hall of Sages");
    expect(wrapper.text()).toContain("Current Standings");
    expect(wrapper.text()).toContain("DAILY FOCUS");
    expect(wrapper.text()).toContain("Viewer");
    expect(wrapper.text()).toContain("3,450");
    expect(wrapper.text()).toContain("Current Rank #2");
    expect(wrapper.text()).toContain('Practice "Art of War"');
    expect(wrapper.text()).toContain("Art of War");
    expect(wrapper.text()).toContain("Progress: 3/5");
    expect(mocks.getLeaderboardSnapshot).toHaveBeenCalledWith(25, 0);
  });

  it("loads next page when clicking load more", async () => {
    mocks.getLeaderboardSnapshot
      .mockResolvedValueOnce(
        createSnapshot({
          has_more: true,
          entries: [
            {
              user_id: "00000000-0000-0000-0000-000000000001",
              display_name: "Alpha",
              total_xp: 2500,
              rank: 1,
              level: 6,
              energy_points: 0,
              is_current_user: false,
            },
          ],
        }),
      )
      .mockResolvedValueOnce(
        createSnapshot({
          offset: 1,
          has_more: false,
          entries: [
            {
              user_id: "00000000-0000-0000-0000-000000000002",
              display_name: "Beta",
              total_xp: 1800,
              rank: 2,
              level: 4,
              energy_points: 0,
              is_current_user: false,
            },
          ],
        }),
      );

    const router = createTestRouter();
    await router.push(ROUTES.leaderboard);
    await router.isReady();

    const wrapper = mount(DungeonScholarLeaderboardPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    await wrapper.get(".load-more").trigger("click");
    await flushPromises();

    expect(mocks.getLeaderboardSnapshot).toHaveBeenNthCalledWith(1, 25, 0);
    expect(mocks.getLeaderboardSnapshot).toHaveBeenNthCalledWith(2, 25, 1);
    expect(wrapper.text()).toContain("Alpha");
    expect(wrapper.text()).toContain("Beta");
    expect(wrapper.get(".load-more").text()).toContain("All scholars loaded");
  });

  it("displays username when display_name is null", async () => {
    mocks.getLeaderboardSnapshot.mockResolvedValueOnce(
      createSnapshot({
        entries: [
          {
            user_id: "00000000-0000-0000-0000-000000000001",
            display_name: null,
            total_xp: 2500,
            rank: 1,
            level: 6,
            energy_points: 0,
            is_current_user: false,
          },
        ],
      }),
    );

    const router = createTestRouter();
    await router.push(ROUTES.leaderboard);
    await router.isReady();

    const wrapper = mount(DungeonScholarLeaderboardPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.text()).not.toContain("Scholar 000000");
  });
});
