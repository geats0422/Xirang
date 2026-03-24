import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";
import { ROUTES } from "../constants/routes";
import DungeonScholarLibraryPage from "./DungeonScholarLibraryPage.vue";

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarLibraryPage, path: ROUTES.library },
      { component: { template: "<div>Game Modes</div>" }, path: ROUTES.gameModes },
    ],
  });
}

describe("DungeonScholarLibraryPage", () => {
  it("renders upload button in toolbar", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.library);
    await router.isReady();

    const wrapper = mount(DungeonScholarLibraryPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".upload-icon-btn").exists()).toBe(true);
  });

  it("renders add new scroll card with CTA", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.library);
    await router.isReady();

    const wrapper = mount(DungeonScholarLibraryPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".scroll-card--add").exists()).toBe(true);
    expect(wrapper.find(".scroll-card__add-icon").text()).toContain("＋");
  });

  it("renders upload disclaimer on add card", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.library);
    await router.isReady();

    const wrapper = mount(DungeonScholarLibraryPage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".scroll-card__add-disclaimer").exists()).toBe(true);
  });

  it("shows upload loading state when triggered", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.library);
    await router.isReady();

    const wrapper = mount(DungeonScholarLibraryPage, {
      global: { plugins: [router] },
    });

    const vm = wrapper.vm as unknown as { triggerUpload: () => void };
    vm.triggerUpload();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".scroll-card--add--loading").exists()).toBe(true);
  });

  it("navigates to game modes when clicking begin study", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.library);
    await router.isReady();

    const wrapper = mount(DungeonScholarLibraryPage, {
      global: { plugins: [router] },
    });

    const beginButton = wrapper.find(".scroll-card__action--begin");
    await beginButton.trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.gameModes);
  });
});
