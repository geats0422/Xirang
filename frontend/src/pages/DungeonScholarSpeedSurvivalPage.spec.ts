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

async function mountSpeedSurvivalPage() {
  const router = createTestRouter();
  await router.push({ path: ROUTES.speedSurvival, query: { documentId: "doc-1" } });
  await router.isReady();

  const wrapper = mount(DungeonScholarSpeedSurvivalPage, {
    global: { plugins: [router, i18n] },
  });
  await flushPromises();

  return { router, wrapper };
}

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolver) => {
    resolve = resolver;
  });
  return { promise, resolve };
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
    const { wrapper } = await mountSpeedSurvivalPage();

    expect(wrapper.find(".survival-card").exists()).toBe(true);
    expect(wrapper.find(".survival-card__title").exists()).toBe(true);
  });

  it("renders markdown in question text", async () => {
    mocks.createRun.mockResolvedValueOnce({
      run_id: "run-speed-1",
      mode: "speed",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 120, pending_coins: 0 },
      questions: [{ id: "q-1", text: "Speed **question**", options: [{ id: "o-1", text: "False" }, { id: "o-2", text: "True" }] }],
    });

    const { wrapper } = await mountSpeedSurvivalPage();

    expect(wrapper.find(".survival-card__title strong").exists()).toBe(true);
  });

  it("renders feedback action for reporting errors", async () => {
    const { wrapper } = await mountSpeedSurvivalPage();

    expect(wrapper.find(".feedback-action").exists()).toBe(true);
  });

  it("renders run status notice for fast answers", async () => {
    const { wrapper } = await mountSpeedSurvivalPage();

    const vm = wrapper.vm as unknown as { setFastAnswer: () => void };
    vm.setFastAnswer();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".run-status-notice").exists()).toBe(true);
  });

  it("navigates back when clicking exit", async () => {
    const { router, wrapper } = await mountSpeedSurvivalPage();

    await wrapper.find(".exit-btn").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.levelPath);
  });

  it("submits answer through runs api", async () => {
    const { wrapper } = await mountSpeedSurvivalPage();

    await wrapper.find(".answer-pill--false").trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
  });

  it("prevents double-submit and shows selected submitting feedback", async () => {
    const deferred = createDeferred<unknown>();
    mocks.submitAnswer.mockReturnValueOnce(deferred.promise);

    const { wrapper } = await mountSpeedSurvivalPage();

    await wrapper.find(".answer-pill--false").trigger("click");
    await wrapper.find(".answer-pill--true").trigger("click");

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
    expect(wrapper.find(".answer-pill--false").classes()).toContain("answer-pill--selected");
    expect(wrapper.find(".answer-pill--false").attributes("disabled")).toBeDefined();

    deferred.resolve({
      is_correct: true,
      run: {
        id: "run-speed-1",
        status: "running",
        score: 10,
        state: { hp: 3, max_hp: 3, floor: 2, floor_total: 8, time_left_sec: 118, pending_coins: 10 },
      },
      settlement: null,
    });
    await flushPromises();
  });

  it("does not auto-advance on wrong answer and resets feedback after question changes", async () => {
    mocks.createRun.mockResolvedValueOnce({
      run_id: "run-speed-1",
      mode: "speed",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 120, pending_coins: 0 },
      questions: [
        {
          id: "q-1",
          text: "First Speed Question",
          options: [{ id: "o-1", text: "False" }, { id: "o-2", text: "True" }],
        },
        {
          id: "q-2",
          text: "Second Speed Question",
          options: [{ id: "o-3", text: "False" }, { id: "o-4", text: "True" }],
        },
      ],
    });

    mocks.submitAnswer
      .mockResolvedValueOnce({
        is_correct: false,
        feedback: {
          correct_answer: "True",
          explanation: "Because this statement is historically accurate.",
        },
        run: {
          id: "run-speed-1",
          status: "running",
          score: 5,
          state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 116, pending_coins: 5 },
        },
        settlement: null,
      })
      .mockResolvedValueOnce({
        is_correct: true,
        feedback: null,
        run: {
          id: "run-speed-1",
          status: "running",
          score: 15,
          state: { hp: 3, max_hp: 3, floor: 2, floor_total: 8, time_left_sec: 112, pending_coins: 15 },
        },
        settlement: null,
      });

    const { wrapper } = await mountSpeedSurvivalPage();

    await wrapper.find(".answer-pill--false").trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain("First Speed Question");
    expect(wrapper.find(".answer-feedback").exists()).toBe(true);
    expect(wrapper.text()).toContain("Correct answer:");

    await wrapper.find(".answer-pill--true").trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(2);
    expect(wrapper.text()).toContain("Second Speed Question");
    expect(wrapper.find(".answer-feedback").exists()).toBe(false);
  });
});
