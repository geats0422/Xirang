import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";
import { ROUTES } from "../constants/routes";
import DungeonScholarEndlessAbyssPage from "./DungeonScholarEndlessAbyssPage.vue";

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarEndlessAbyssPage, path: ROUTES.endlessAbyss },
      { component: { template: "<div>Game Modes</div>" }, path: ROUTES.gameModes },
    ],
  });
}

describe("DungeonScholarEndlessAbyssPage", () => {
  it("renders question card with content", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.endlessAbyss);
    await router.isReady();

    const wrapper = mount(DungeonScholarEndlessAbyssPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".question-card").exists()).toBe(true);
    expect(wrapper.find(".question-card h1").exists()).toBe(true);
  });

  it("renders feedback action for reporting errors", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.endlessAbyss);
    await router.isReady();

    const wrapper = mount(DungeonScholarEndlessAbyssPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".feedback-action").exists()).toBe(true);
  });

  it("renders run status notice for reduced reward", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.endlessAbyss);
    await router.isReady();

    const wrapper = mount(DungeonScholarEndlessAbyssPage, {
      global: { plugins: [router] },
    });

    const vm = wrapper.vm as unknown as { setReducedReward: () => void };
    vm.setReducedReward();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".run-status-notice").exists()).toBe(true);
  });

  it("navigates back when clicking return", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.endlessAbyss);
    await router.isReady();

    const wrapper = mount(DungeonScholarEndlessAbyssPage, {
      global: { plugins: [router] },
    });

    await wrapper.find(".return-btn").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.gameModes);
  });
});
