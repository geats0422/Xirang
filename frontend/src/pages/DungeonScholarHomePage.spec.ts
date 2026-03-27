import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarHomePage from "./DungeonScholarHomePage.vue";

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarHomePage, path: ROUTES.home },
      { component: { template: "<div>Shop</div>" }, path: ROUTES.shop },
      { component: { template: "<div>Modes</div>" }, path: ROUTES.gameModes },
      { component: { template: "<div>Library</div>" }, path: ROUTES.library },
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
        plugins: [router, i18n],
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
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.find(".hero-upload__disclaimer").exists()).toBe(true);
    expect(wrapper.find(".hero-upload__disclaimer").text()).toContain("BETA");
  });

  it("renders upload idle state by default", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.find(".hero-upload--idle").exists()).toBe(true);
    expect(wrapper.find(".browse-btn").exists()).toBe(true);
  });

  it("renders upload loading state when uploading", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router, i18n] },
    });

    const vm = wrapper.vm as unknown as { uploadState: "idle" | "loading" | "success" | "failure" };
    vm.uploadState = "loading";
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".hero-upload--loading").exists()).toBe(true);
    expect(wrapper.find(".hero-upload__spinner").exists()).toBe(true);
  });

  it("renders upload success state", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router, i18n] },
    });

    const vm = wrapper.vm as unknown as { uploadState: "idle" | "loading" | "success" | "failure" };
    vm.uploadState = "success";
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".hero-upload--success").exists()).toBe(true);
  });

  it("renders upload failure state with retry option", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router, i18n] },
    });

    const vm = wrapper.vm as unknown as { setUploadFailure: () => void };
    vm.setUploadFailure();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".hero-upload--failure").exists()).toBe(true);
    expect(wrapper.find(".hero-upload__retry").exists()).toBe(true);
  });
  it("navigates to mode selection from ready home card", async () => {
    const router = createTestRouter();

    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router, i18n] },
    });

    const vm = wrapper.vm as unknown as {
      documents: Array<{
        id: string;
        title: string;
        createdAt: string;
        lastVisited: string;
        progress: number;
        icon: string;
        status: "ready" | "processing" | "failed";
        actionLabel: string;
      }>;
    };

    vm.documents = [
      {
        id: "doc-ready",
        title: "ready.md",
        createdAt: "",
        lastVisited: "Just now",
        progress: 0,
        icon: "📖",
        status: "ready",
        actionLabel: "Begin Study",
      },
    ];
    await wrapper.vm.$nextTick();

    await wrapper.find(".dungeon-card__action").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.gameModes);
    expect(router.currentRoute.value.query.documentId).toBe("doc-ready");
  });

  it("shows notice and stays on home for processing home card", async () => {
    const router = createTestRouter();

    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router, i18n] },
    });

    const vm = wrapper.vm as unknown as {
      documents: Array<{
        id: string;
        title: string;
        createdAt: string;
        lastVisited: string;
        progress: number;
        icon: string;
        status: "ready" | "processing" | "failed";
        actionLabel: string;
      }>;
    };

    vm.documents = [
      {
        id: "doc-processing",
        title: "processing.md",
        createdAt: "",
        lastVisited: "Just now",
        progress: 0,
        icon: "📖",
        status: "processing",
        actionLabel: "Processing...",
      },
    ];
    await wrapper.vm.$nextTick();

    await wrapper.find(".dungeon-card__action").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.home);
    expect(wrapper.find(".recent-section__notice").text()).toContain("still processing");
  });

  it("navigates to library for failed home card", async () => {
    const router = createTestRouter();

    await router.push(ROUTES.home);
    await router.isReady();

    const wrapper = mount(DungeonScholarHomePage, {
      global: { plugins: [router, i18n] },
    });

    const vm = wrapper.vm as unknown as {
      documents: Array<{
        id: string;
        title: string;
        createdAt: string;
        lastVisited: string;
        progress: number;
        icon: string;
        status: "ready" | "processing" | "failed";
        actionLabel: string;
      }>;
    };

    vm.documents = [
      {
        id: "doc-failed",
        title: "failed.md",
        createdAt: "",
        lastVisited: "Just now",
        progress: 0,
        icon: "📖",
        status: "failed",
        actionLabel: "Go to Library",
      },
    ];
    await wrapper.vm.$nextTick();

    await wrapper.find(".dungeon-card__action").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.library);
  });

});
