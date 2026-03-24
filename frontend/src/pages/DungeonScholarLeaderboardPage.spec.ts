import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";
import { ROUTES } from "../constants/routes";
import DungeonScholarLeaderboardPage from "./DungeonScholarLeaderboardPage.vue";

describe("DungeonScholarLeaderboardPage", () => {
  it("renders extracted summary and standings sections", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ component: DungeonScholarLeaderboardPage, path: ROUTES.leaderboard }],
    });

    await router.push(ROUTES.leaderboard);
    await router.isReady();

    const wrapper = mount(DungeonScholarLeaderboardPage, {
      global: {
        plugins: [router],
      },
    });

    expect(wrapper.text()).toContain("Hall of Sages");
    expect(wrapper.text()).toContain("Current Standings");
    expect(wrapper.text()).toContain("DAILY FOCUS");
  });
});
