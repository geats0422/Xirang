import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarLevelPathPage from "./DungeonScholarLevelPathPage.vue";

const mocks = vi.hoisted(() => ({
  listRunPathOptions: vi.fn(),
}));

vi.mock("../api/runs", () => ({
  listRunPathOptions: mocks.listRunPathOptions,
}));

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarLevelPathPage, path: ROUTES.levelPath },
      { component: { template: "<div>ModeSelection</div>" }, path: ROUTES.gameModes },
      { component: { template: "<div>Endless</div>" }, path: ROUTES.endlessAbyss },
      { component: { template: "<div>Speed</div>" }, path: ROUTES.speedSurvival },
      { component: { template: "<div>Draft</div>" }, path: ROUTES.knowledgeDraft },
      { component: { template: "<div>Review</div>" }, path: ROUTES.review },
    ],
  });
}

describe("DungeonScholarLevelPathPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.global.locale.value = "en";
    mocks.listRunPathOptions.mockResolvedValue({
      mode: "endless",
      options: [
        { path_id: "F1", label: "F1", kind: "floor", description: "Warm-up floor", goal_total: 10 },
        { path_id: "F2", label: "F2", kind: "floor", description: "Steady learning", goal_total: 10 },
      ],
    });
  });

  it("renders path nodes", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.findAll(".path-node").length).toBeGreaterThan(0);
  });

  it("goes to endless mode with selected floor", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1", mode: "endless-abyss" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    await wrapper.find(".path-start").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.path).toBe(ROUTES.endlessAbyss);
    expect(router.currentRoute.value.query.documentId).toBe("doc-1");
    expect(router.currentRoute.value.query.floor).toBe("1");
  });

  it("goes to speed mode without floor query", async () => {
    mocks.listRunPathOptions.mockResolvedValue({
      mode: "speed",
      options: [
        { path_id: "speed-route-focus", label: "R1", kind: "checkpoint", description: "Focus", goal_total: 8 },
      ],
    });
    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1", mode: "speed-survival" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    await wrapper.find(".path-start").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.speedSurvival);
    expect(router.currentRoute.value.query.mode).toBe("speed-survival");
    expect(router.currentRoute.value.query.floor).toBeUndefined();
  });

  it("renders Chinese route copy and shows backend description in selected summary", async () => {
    i18n.global.locale.value = "zh-CN";
    mocks.listRunPathOptions.mockResolvedValue({
      mode: "endless",
      options: [
        { path_id: "F1", label: "F1", kind: "floor", description: "夯实基础，稳步推进", goal_total: 10 },
      ],
    });

    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1", mode: "endless-abyss" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.find(".path-sub").text()).toBe("开始深渊路径");
    expect(wrapper.find(".path-start").text()).toBe("进入深渊无尽");
    expect(wrapper.find(".path-actions p").text()).toContain("已选第 1 层");
    expect(wrapper.find(".path-actions p").text()).toContain("夯实基础，稳步推进");
  });

  it("routes review mode to standalone review page", async () => {
    mocks.listRunPathOptions.mockResolvedValue({
      mode: "review",
      options: [
        { path_id: "review-stage-1", label: "R1", kind: "review", description: "Mixed mistakes", goal_total: 20 },
      ],
    });

    const router = createTestRouter();
    await router.push({
      path: ROUTES.levelPath,
      query: { title: "ready-scroll.pdf", documentId: "doc-1", mode: "review", mistakeReview: "true" },
    });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    await wrapper.find(".path-start").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.review);
    expect(router.currentRoute.value.query.mode).toBe("review");
    expect(router.currentRoute.value.query.pathId).toBe("review-stage-1");
  });
});
