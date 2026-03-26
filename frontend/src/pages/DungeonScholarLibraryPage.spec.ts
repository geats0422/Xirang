import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarLibraryPage from "./DungeonScholarLibraryPage.vue";
import DungeonScholarModeSelectionPage from "./DungeonScholarModeSelectionPage.vue";

const mocks = vi.hoisted(() => ({
  listDocuments: vi.fn(),
  deleteDocument: vi.fn(),
  uploadAndRefresh: vi.fn(),
  hydrate: vi.fn(),
}));

vi.mock("../api/documents", () => ({
  listDocuments: mocks.listDocuments,
  deleteDocument: mocks.deleteDocument,
}));

vi.mock("../composables/useScholarData", () => ({
  useScholarData: () => ({
    profileName: ref("testuser2"),
    profileLevel: ref("Level 1 Scholar"),
    uploadAndRefresh: mocks.uploadAndRefresh,
    hydrate: mocks.hydrate,
  }),
}));

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarLibraryPage, path: ROUTES.library },
      { component: DungeonScholarModeSelectionPage, path: ROUTES.gameModes },
    ],
  });
}

describe("DungeonScholarLibraryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.hydrate.mockResolvedValue(undefined);
    mocks.uploadAndRefresh.mockResolvedValue(undefined);
    mocks.deleteDocument.mockResolvedValue({ id: "doc-1", deleted: true });
    mocks.listDocuments.mockResolvedValue([
      { id: "doc-1", title: "library-upload-test.pptx", status: "processing" },
    ]);
  });

  it("renders add new scroll card with CTA", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.library);
    await router.isReady();

    const wrapper = mount(DungeonScholarLibraryPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.find(".scroll-card--add").exists()).toBe(true);
    expect(wrapper.find(".scroll-card__add-icon").text()).toContain("＋");
  });

  it("opens confirm modal from edit menu", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.library);
    await router.isReady();

    const wrapper = mount(DungeonScholarLibraryPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    await wrapper.find(".scroll-card__edit").trigger("click");
    await wrapper.find(".scroll-card__menu-action--danger").trigger("click");
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".delete-modal-overlay").exists()).toBe(true);
  });

  it("navigates to game modes when clicking begin study", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.library);
    await router.isReady();

    const wrapper = mount(DungeonScholarLibraryPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    await wrapper.find(".scroll-card__action--begin").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.gameModes);
  });
});
