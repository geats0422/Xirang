import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/http";
import { ROUTES } from "../constants/routes";
import DungeonScholarLevelPathPage from "./DungeonScholarLevelPathPage.vue";

const mocks = vi.hoisted(() => ({
  listRunPathOptions: vi.fn(),
  regenerateRunPath: vi.fn(),
}));

vi.mock("../api/runs", () => ({
  listRunPathOptions: mocks.listRunPathOptions,
  regenerateRunPath: mocks.regenerateRunPath,
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
    ],
  });
}

describe("DungeonScholarLevelPathPage", () => {
  beforeEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
    mocks.listRunPathOptions.mockResolvedValue({
      mode: "endless",
      generation_status: "ready",
      options: [
        {
          path_id: "F1",
          label: "F1",
          kind: "floor",
          description: "Warm-up floor",
          goal_total: 10,
          path_version_id: "pv-1",
          level_node_id: "ln-1",
        },
        {
          path_id: "F2",
          label: "F2",
          kind: "floor",
          description: "Steady learning",
          goal_total: 10,
          path_version_id: "pv-1",
          level_node_id: "ln-2",
        },
      ],
    });
    mocks.regenerateRunPath.mockResolvedValue({ generation_status: "generating", mode: "endless" });
  });

  it("renders path nodes", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router] },
    });
    await flushPromises();

    expect(wrapper.findAll(".path-node").length).toBeGreaterThan(0);
  });

  it("goes to endless mode with selected floor", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1", mode: "endless-abyss" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router] },
    });
    await flushPromises();

    await wrapper.find(".path-start").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.path).toBe(ROUTES.endlessAbyss);
    expect(router.currentRoute.value.query.documentId).toBe("doc-1");
    expect(router.currentRoute.value.query.floor).toBe("1");
    expect(router.currentRoute.value.query.pathVersionId).toBe("pv-1");
    expect(router.currentRoute.value.query.levelNodeId).toBe("ln-1");
  });

  it("goes to speed mode without floor query", async () => {
    mocks.listRunPathOptions.mockResolvedValue({
      mode: "speed",
      generation_status: "ready",
      options: [
        { path_id: "speed-route-focus", label: "R1", kind: "checkpoint", description: "Focus", goal_total: 8, path_version_id: "pv-speed", level_node_id: "ln-speed" },
      ],
    });
    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1", mode: "speed-survival" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router] },
    });
    await flushPromises();

    await wrapper.find(".path-start").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.speedSurvival);
    expect(router.currentRoute.value.query.mode).toBe("speed-survival");
    expect(router.currentRoute.value.query.floor).toBeUndefined();
  });
  it("shows generating state without fallback nodes", async () => {
    mocks.listRunPathOptions.mockResolvedValue({
      mode: "endless",
      generation_status: "generating",
      options: [],
    });

    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router] },
    });
    await flushPromises();

    expect(wrapper.findAll(".path-node").length).toBe(0);
    expect(wrapper.text()).toContain("Generating learning path");
  });

  it("triggers regeneration request", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router] },
    });
    await flushPromises();

    const buttons = wrapper.findAll(".path-secondary");
    await buttons[0].trigger("click");
    await flushPromises();

    expect(mocks.regenerateRunPath).toHaveBeenCalledWith("doc-1", "endless");
  });

  it("shows not-ready message then retries successfully", async () => {
    mocks.listRunPathOptions
      .mockRejectedValueOnce(new ApiError("conflict", 409, { detail: "question_set_not_ready" }))
      .mockResolvedValueOnce({
        mode: "endless",
        generation_status: "ready",
        options: [
          {
            path_id: "F1",
            label: "F1",
            kind: "floor",
            description: "Warm-up floor",
            goal_total: 10,
            path_version_id: "pv-1",
            level_node_id: "ln-1",
          },
        ],
      });

    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router] },
    });
    await flushPromises();

    expect(wrapper.text()).toContain("Questions are still generating for this document");

    const retryButton = wrapper.find(".path-status .path-secondary");
    await retryButton.trigger("click");
    await flushPromises();

    expect(mocks.listRunPathOptions).toHaveBeenCalledTimes(2);
    expect(wrapper.findAll(".path-node").length).toBe(1);
  });

  it("shows timeout message when generation polling exceeds max attempts", async () => {
    vi.useFakeTimers();
    mocks.listRunPathOptions.mockResolvedValue({
      mode: "endless",
      generation_status: "generating",
      options: [],
    });

    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router] },
    });
    await flushPromises();

    for (let i = 0; i < 16; i += 1) {
      await vi.advanceTimersByTimeAsync(2000);
      await flushPromises();
    }

    expect(wrapper.text()).toContain("Path generation timed out. Please retry.");
    vi.useRealTimers();
  });

  it("shows regeneration rate limit message on 429", async () => {
    mocks.regenerateRunPath.mockRejectedValue(new ApiError("rate-limit", 429, { detail: "limit" }));

    const router = createTestRouter();
    await router.push({ path: ROUTES.levelPath, query: { title: "bulk-order-07.txt", documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarLevelPathPage, {
      global: { plugins: [router] },
    });
    await flushPromises();

    const regenerateButton = wrapper.find("footer .path-secondary");
    await regenerateButton.trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("Regeneration limit reached (3 times in 24h).");
  });

});
