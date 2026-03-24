import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";
import { ROUTES } from "../constants/routes";
import DungeonScholarHomePage from "./DungeonScholarHomePage.vue";

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarHomePage, path: ROUTES.home },
      { component: { template: "<div>Shop</div>" }, path: ROUTES.shop },
    ],
  });
}

describe("DungeonScholarHomePage", () => {
  it("clicking coin button navigates to shop", async () => {
    const router = createTestRouter();

    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: {
        plugins: [router],
      },
    });

    await wrapper.get(".status-pill--coin").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.shop);
  });

  it("renders upload disclaimer for beta/free tier", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".hero-upload__disclaimer").exists()).toBe(true);
    expect(wrapper.find(".hero-upload__disclaimer").text()).toContain("BETA");
  });

  it("renders upload idle state by default", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router] },
    });

    expect(wrapper.find(".hero-upload--idle").exists()).toBe(true);
    expect(wrapper.find(".browse-btn").exists()).toBe(true);
  });

  it("renders upload loading state when uploading", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router] },
    });

    await wrapper.find(".browse-btn").trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".hero-upload--loading").exists()).toBe(true);
    expect(wrapper.find(".hero-upload__spinner").exists()).toBe(true);
  });

  it("renders upload success state", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router] },
    });

    await wrapper.find(".browse-btn").trigger("click");
    await wrapper.vm.$nextTick();

    await new Promise((resolve) => window.setTimeout(resolve, 1600));
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".hero-upload--success").exists()).toBe(true);
  });

  it("renders upload failure state with retry option", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router] },
    });

    const vm = wrapper.vm as unknown as { setUploadFailure: () => void };
    vm.setUploadFailure();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".hero-upload--failure").exists()).toBe(true);
    expect(wrapper.find(".hero-upload__retry").exists()).toBe(true);
  });
});
