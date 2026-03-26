import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarSettingsPage from "./DungeonScholarSettingsPage.vue";

describe("DungeonScholarSettingsPage", () => {
  it("renders extracted settings sections", async () => {
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
  });
});
