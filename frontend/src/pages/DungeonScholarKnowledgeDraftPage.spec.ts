import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";
import { ROUTES } from "../constants/routes";
import DungeonScholarKnowledgeDraftPage from "./DungeonScholarKnowledgeDraftPage.vue";

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarKnowledgeDraftPage, path: ROUTES.knowledgeDraft },
      { component: { template: "<div>Game Modes</div>" }, path: ROUTES.gameModes },
    ],
  });
}

describe("DungeonScholarKnowledgeDraftPage", () => {
  it("renders scroll card with content", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.knowledgeDraft);
    await router.isReady();

    const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".scroll-card").exists()).toBe(true);
    expect(wrapper.find(".scroll-paper h2").exists()).toBe(true);
  });

  it("renders feedback action for reporting errors", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.knowledgeDraft);
    await router.isReady();

    const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".feedback-action").exists()).toBe(true);
  });

  it("renders run status notice", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.knowledgeDraft);
    await router.isReady();

    const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
      global: { plugins: [router] },
    });

    const vm = wrapper.vm as unknown as { setShowNotice: () => void };
    vm.setShowNotice();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".run-status-notice").exists()).toBe(true);
  });

  it("navigates back when clicking back button", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.knowledgeDraft);
    await router.isReady();

    const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
      global: { plugins: [router] },
    });

    await wrapper.find(".draft-title__back").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.gameModes);
  });
});
