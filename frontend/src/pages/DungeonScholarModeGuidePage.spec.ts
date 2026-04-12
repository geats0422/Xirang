import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarLevelPathPage from "./DungeonScholarLevelPathPage.vue";
import DungeonScholarModeGuidePage from "./DungeonScholarModeGuidePage.vue";

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarModeGuidePage, path: ROUTES.modeGuide },
      { component: DungeonScholarLevelPathPage, path: ROUTES.levelPath },
    ],
  });
}

describe("DungeonScholarModeGuidePage", () => {
  it("renders speed survival guide copy", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.modeGuide, query: { mode: "speed-survival" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarModeGuidePage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.text()).toContain("Speed Survival Guide");
    expect(wrapper.text()).toContain("How It Works");
  });

  it("renders review guide copy", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.modeGuide, query: { mode: "review" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarModeGuidePage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.text()).toContain("Mistake Review Guide");
    expect(wrapper.text()).toContain("Back to Path");
  });
});
