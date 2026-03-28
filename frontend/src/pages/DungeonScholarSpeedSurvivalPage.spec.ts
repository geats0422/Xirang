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
      questions: [{ id: "q-1", text: "Speed question", options: [{ id: "o-1", text: "False" }, { id: "o-2", text: "True" }], source_locator: "快捷键", supporting_excerpt: "Ctrl + / # 注释" }],
    });
    mocks.submitAnswer.mockResolvedValue({
      is_correct: true,
      feedback: null,
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


  it("strips markdown formatting in speed question and options", async () => {
    mocks.createRun.mockResolvedValueOnce({
      run_id: "run-speed-1",
      mode: "speed",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 120, pending_coins: 0 },
      questions: [{ id: "q-1", text: "**Speed** question", options: [{ id: "o-1", text: "**False**" }, { id: "o-2", text: "_True_" }] }],
    });

    const router = createTestRouter();
    await router.push({ path: ROUTES.speedSurvival, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.find(".survival-card__body h2").text()).toBe("Speed question");
    expect(wrapper.find(".answer-pill--false .answer-pill__label").text()).toBe("False");
    expect(wrapper.find(".answer-pill--true .answer-pill__label").text()).toBe("True");
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

  it("renders question provenance details when available", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.speedSurvival, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.text()).toContain("来源：快捷键");
    expect(wrapper.text()).toContain("摘录：Ctrl + / # 注释");
  });

  it("renders wrong answer feedback with correct answer and explanation", async () => {
    mocks.submitAnswer.mockResolvedValueOnce({
      is_correct: false,
      feedback: {
        correct_options: [{ id: "o-2", text: "True" }],
        explanation: "The source material marks this statement as true.",
        source_locator: "快捷键",
        supporting_excerpt: "Ctrl + / # 注释",
      },
      run: {
        id: "run-speed-1",
        status: "running",
        score: 0,
        state: { hp: 2, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 118, pending_coins: 0 },
      },
      settlement: null,
    });

    const router = createTestRouter();
    await router.push({ path: ROUTES.speedSurvival, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    await wrapper.find(".answer-pill--false").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("正确答案：True");
    expect(wrapper.text()).toContain("解析：The source material marks this statement as true.");
    expect(wrapper.text()).toContain("来源：快捷键");
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

  it("opens mistake review panel from settlement", async () => {
    mocks.submitAnswer.mockResolvedValueOnce({
      is_correct: false,
      feedback: {
        correct_options: [{ id: "o-2", text: "True" }],
        explanation: "The source material marks this statement as true.",
        source_locator: "快捷键",
        supporting_excerpt: "Ctrl + / # 注释",
      },
      run: {
        id: "run-speed-1",
        status: "completed",
        score: 0,
        state: { hp: 2, max_hp: 3, floor: 8, floor_total: 8, time_left_sec: 0, pending_coins: 0 },
      },
      settlement: {
        run_id: "run-speed-1",
        xp_earned: 10,
        coins_earned: 1,
        combo_max: 1,
        accuracy: 0.5,
        correct_count: 0,
        total_count: 1,
      },
    });

    const router = createTestRouter();
    await router.push({ path: ROUTES.speedSurvival, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    await wrapper.find(".answer-pill--false").trigger("click");
    await flushPromises();

    await wrapper.get(".settlement-secondary").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("Review Mistakes");
    expect(wrapper.text()).toContain("Speed question");
    expect(wrapper.text()).toContain("正确答案：True");
  });
});
