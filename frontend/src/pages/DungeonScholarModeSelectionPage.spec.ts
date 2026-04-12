import { flushPromises, mount } from "@vue/test-utils";
import { describe, it, expect } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
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
        {
          path: ROUTES.levelPath,
          component: { template: "<div>Level Path</div>" },
        },
      ],
    });

    await router.push("/library/game-modes");
    await router.isReady();

    const wrapper = mount(DungeonScholarModeSelectionPage, {
      global: {
        plugins: [router, i18n],
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
        {
          path: ROUTES.levelPath,
          component: { template: "<div>Level Path</div>" },
        },
      ],
    });

    await router.push("/library/game-modes");
    await router.isReady();

    const wrapper = mount(DungeonScholarModeSelectionPage, {
      global: {
        plugins: [router, i18n],
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
        {
          path: ROUTES.levelPath,
          component: { template: "<div>Level Path</div>" },
        },
      ],
    });

    await router.push("/library/game-modes");
    await router.isReady();

    const wrapper = mount(DungeonScholarModeSelectionPage, {
      global: {
        plugins: [router, i18n],
      },
    });

    const modeCards = wrapper.findAll(".mode-card");
    await modeCards[0].trigger("click");

    const primaryButton = wrapper.find(".mode-actions__primary");
    expect(primaryButton.attributes("disabled")).toBeUndefined();
  });

  it("routes to path selection after choosing mode", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: ROUTES.gameModes,
          component: DungeonScholarModeSelectionPage,
        },
        {
          path: ROUTES.levelPath,
          component: { template: "<div>Level Path</div>" },
        },
      ],
    });

    await router.push({ path: ROUTES.gameModes, query: { documentId: "doc-1", title: "bulk-order-07.txt" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarModeSelectionPage, {
      global: {
        plugins: [router, i18n],
      },
    });

    await wrapper.findAll(".mode-card")[1].trigger("click");
    await wrapper.vm.$nextTick();
    await wrapper.find(".mode-actions__primary").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.levelPath);
    expect(router.currentRoute.value.query.mode).toBe("speed-survival");
    expect(router.currentRoute.value.query.documentId).toBe("doc-1");
  });

  it("preselects standalone review when entering review flow", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: ROUTES.gameModes,
          component: DungeonScholarModeSelectionPage,
        },
        {
          path: ROUTES.levelPath,
          component: { template: "<div>Level Path</div>" },
        },
      ],
    });

    await router.push({ path: ROUTES.gameModes, query: { flow: "review", mistakeReview: "true" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarModeSelectionPage, {
      global: {
        plugins: [router, i18n],
      },
    });

    expect(wrapper.findAll(".mode-card")).toHaveLength(4);
    expect(wrapper.findAll(".mode-card")[3].classes()).toContain("mode-card--active");
  });
});
