import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";
import { ROUTES } from "../constants/routes";
import DungeonScholarSpeedSurvivalPage from "./DungeonScholarSpeedSurvivalPage.vue";

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarSpeedSurvivalPage, path: ROUTES.speedSurvival },
      { component: { template: "<div>Game Modes</div>" }, path: ROUTES.gameModes },
    ],
  });
}

describe("DungeonScholarSpeedSurvivalPage", () => {
  it("renders question card with content", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.speedSurvival);
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".survival-card").exists()).toBe(true);
    expect(wrapper.find(".survival-card__body h2").exists()).toBe(true);
  });

  it("renders feedback action for reporting errors", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.speedSurvival);
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".feedback-action").exists()).toBe(true);
  });

  it("renders run status notice for fast answers", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.speedSurvival);
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router] },
    });

    const vm = wrapper.vm as unknown as { setFastAnswer: () => void };
    vm.setFastAnswer();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".run-status-notice").exists()).toBe(true);
  });

  it("navigates back when clicking exit", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.speedSurvival);
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router] },
    });

    await wrapper.find(".exit-btn").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.gameModes);
  });
});
