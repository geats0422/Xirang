import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import DungeonScholarModeSelectionPage from "./DungeonScholarModeSelectionPage.vue";

describe("DungeonScholarModeSelectionPage", () => {
  it("should have no mode selected by default", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: "/library/game-modes",
          component: DungeonScholarModeSelectionPage,
        },
      ],
    });

    await router.push("/library/game-modes");
    await router.isReady();

    const wrapper = mount(DungeonScholarModeSelectionPage, {
      global: {
        plugins: [router],
      },
    });

    const selectedModeId = (wrapper.vm as unknown as { selectedModeId: string | null }).selectedModeId;
    expect(selectedModeId).toBeNull();
  });

  it("should have primary action disabled when no mode is selected", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: "/library/game-modes",
          component: DungeonScholarModeSelectionPage,
        },
      ],
    });

    await router.push("/library/game-modes");
    await router.isReady();

    const wrapper = mount(DungeonScholarModeSelectionPage, {
      global: {
        plugins: [router],
      },
    });

    const primaryButton = wrapper.find(".mode-actions__primary");
    expect(primaryButton.attributes("disabled")).toBeDefined();
  });

  it("should enable primary action when a mode is selected", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: "/library/game-modes",
          component: DungeonScholarModeSelectionPage,
        },
      ],
    });

    await router.push("/library/game-modes");
    await router.isReady();

    const wrapper = mount(DungeonScholarModeSelectionPage, {
      global: {
        plugins: [router],
      },
    });

    const modeCards = wrapper.findAll(".mode-card");
    await modeCards[0].trigger("click");

    const primaryButton = wrapper.find(".mode-actions__primary");
    expect(primaryButton.attributes("disabled")).toBeUndefined();
  });
});
