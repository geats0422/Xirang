import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarSpeedSurvivalPage from "./DungeonScholarSpeedSurvivalPage.vue";

const mocks = vi.hoisted(() => ({
  createRun: vi.fn(),
  submitAnswer: vi.fn(),
  getShopBalance: vi.fn(),
}));

vi.mock("../api/runs", () => ({
  createRun: mocks.createRun,
  submitAnswer: mocks.submitAnswer,
}));

vi.mock("../api/shop", () => ({
  getShopBalance: mocks.getShopBalance,
}));

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarSpeedSurvivalPage, path: ROUTES.speedSurvival },
      { component: { template: "<div>Game Modes</div>" }, path: ROUTES.gameModes },
      { component: { template: "<div>Level Path</div>" }, path: ROUTES.levelPath },
    ],
  });
}

describe("DungeonScholarSpeedSurvivalPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getShopBalance.mockResolvedValue({ asset_code: "COIN", balance: 0 });
    mocks.createRun.mockResolvedValue({
      run_id: "run-speed-1",
      mode: "speed",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 120, pending_coins: 0 },
      questions: [{ id: "q-1", text: "Speed question", options: [{ id: "o-1", text: "False" }, { id: "o-2", text: "True" }] }],
    });
    mocks.submitAnswer.mockResolvedValue({
      is_correct: true,
      run: {
        id: "run-speed-1",
        status: "running",
        score: 10,
        state: { hp: 3, max_hp: 3, floor: 2, floor_total: 8, time_left_sec: 118, pending_coins: 10 },
      },
      settlement: null,
    });
  });

  it("renders question card with content", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.speedSurvival, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.find(".survival-card").exists()).toBe(true);
    expect(wrapper.find(".survival-card__body h2").exists()).toBe(true);
  });

  it("renders feedback action for reporting errors", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.speedSurvival, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.find(".feedback-action").exists()).toBe(true);
  });

  it("renders run status notice for fast answers", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.speedSurvival, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router, i18n] },
    });

    const vm = wrapper.vm as unknown as { setFastAnswer: () => void };
    vm.setFastAnswer();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".run-status-notice").exists()).toBe(true);
  });

  it("navigates back when clicking exit", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.speedSurvival, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.find(".exit-btn").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.levelPath);
  });

  it("submits answer through runs api", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.speedSurvival, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    await wrapper.find(".answer-pill--false").trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
  });
});
