import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarEndlessAbyssPage from "./DungeonScholarEndlessAbyssPage.vue";

const mocks = vi.hoisted(() => ({
  createRun: vi.fn(),
  submitAnswer: vi.fn(),
  useRunRevive: vi.fn(),
  getShopBalance: vi.fn(),
}));

vi.mock("../api/runs", () => ({
  createRun: mocks.createRun,
  submitAnswer: mocks.submitAnswer,
  useRunRevive: mocks.useRunRevive,
}));

vi.mock("../api/shop", () => ({
  getShopBalance: mocks.getShopBalance,
}));

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { component: DungeonScholarEndlessAbyssPage, path: ROUTES.endlessAbyss },
      { component: { template: "<div>Game Modes</div>" }, path: ROUTES.gameModes },
      { component: { template: "<div>Level Path</div>" }, path: ROUTES.levelPath },
    ],
  });
}

async function mountEndlessAbyssPage() {
  const router = createTestRouter();
  await router.push({ path: ROUTES.endlessAbyss, query: { documentId: "doc-1" } });
  await router.isReady();

  const wrapper = mount(DungeonScholarEndlessAbyssPage, {
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

describe("DungeonScholarEndlessAbyssPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getShopBalance.mockResolvedValue({ asset_code: "COIN", balance: 0 });
    mocks.createRun.mockResolvedValue({
      run_id: "run-1",
      mode: "endless",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 10, time_left_sec: 900, pending_coins: 0 },
      questions: [{ id: "q-1", text: "Question", options: [{ id: "o-1", text: "water" }] }],
    });
    mocks.submitAnswer.mockResolvedValue({
      is_correct: true,
      run: {
        id: "run-1",
        status: "running",
        score: 10,
        state: { hp: 3, max_hp: 3, floor: 2, floor_total: 10, time_left_sec: 890, pending_coins: 10 },
      },
      settlement: null,
    });
  });

  it("renders question card with content", async () => {
    const { wrapper } = await mountEndlessAbyssPage();

    expect(wrapper.find(".question-card").exists()).toBe(true);
    expect(wrapper.find(".question-card h1").exists()).toBe(true);
  });

  it("renders feedback action for reporting errors", async () => {
    const { wrapper } = await mountEndlessAbyssPage();

    expect(wrapper.find(".feedback-action").exists()).toBe(true);
  });

  it("renders run status notice for reduced reward", async () => {
    const { wrapper } = await mountEndlessAbyssPage();

    const vm = wrapper.vm as unknown as { setReducedReward: () => void };
    vm.setReducedReward();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".run-status-notice").exists()).toBe(true);
  });

  it("navigates back when clicking return", async () => {
    const { router, wrapper } = await mountEndlessAbyssPage();

    await wrapper.find(".return-btn").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.levelPath);
  });

  it("prevents double submit while answer is submitting", async () => {
    const deferred = createDeferred<unknown>();
    mocks.submitAnswer.mockReturnValueOnce(deferred.promise);

    const { wrapper } = await mountEndlessAbyssPage();
    await wrapper.find(".answer-input input").setValue("water");

    const castButton = wrapper.find(".cast-btn");
    await castButton.trigger("click");
    await castButton.trigger("click");

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
    expect(wrapper.find(".cast-btn").attributes("disabled")).toBeDefined();

    deferred.resolve({
      is_correct: true,
      run: {
        id: "run-1",
        status: "running",
        score: 10,
        state: { hp: 3, max_hp: 3, floor: 2, floor_total: 10, time_left_sec: 890, pending_coins: 10 },
      },
      settlement: null,
    });
    await flushPromises();

    expect(wrapper.find(".cast-btn").classes()).not.toContain("cast-btn--submitting");
  });

  it("does not auto-advance on wrong answer and resets notice after question changes", async () => {
    mocks.createRun.mockResolvedValueOnce({
      run_id: "run-1",
      mode: "endless",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 10, time_left_sec: 900, pending_coins: 0 },
      questions: [
        { id: "q-1", text: "First Endless Question", options: [{ id: "o-1", text: "water" }] },
        { id: "q-2", text: "Second Endless Question", options: [{ id: "o-2", text: "fire" }] },
      ],
    });

    mocks.submitAnswer
      .mockResolvedValueOnce({
        is_correct: false,
        run: {
          id: "run-1",
          status: "running",
          score: 5,
          state: { hp: 2, max_hp: 3, floor: 1, floor_total: 10, time_left_sec: 892, pending_coins: 5 },
        },
        settlement: null,
      })
      .mockResolvedValueOnce({
        is_correct: true,
        run: {
          id: "run-1",
          status: "running",
          score: 15,
          state: { hp: 2, max_hp: 3, floor: 2, floor_total: 10, time_left_sec: 886, pending_coins: 15 },
        },
        settlement: null,
      });

    const { wrapper } = await mountEndlessAbyssPage();

    await wrapper.find(".answer-input input").setValue("mistake");
    await wrapper.find(".cast-btn").trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain("First Endless Question");
    expect(wrapper.find(".run-status-notice--danger").exists()).toBe(true);

    await wrapper.find(".answer-input input").setValue("water");
    await wrapper.find(".cast-btn").trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(2);
    expect(wrapper.text()).toContain("Second Endless Question");
    expect(wrapper.find(".run-status-notice--danger").exists()).toBe(false);
  });
});
