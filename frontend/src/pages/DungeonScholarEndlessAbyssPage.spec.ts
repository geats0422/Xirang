import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarEndlessAbyssPage from "./DungeonScholarEndlessAbyssPage.vue";

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
      { component: DungeonScholarEndlessAbyssPage, path: ROUTES.endlessAbyss },
      { component: { template: "<div>Game Modes</div>" }, path: ROUTES.gameModes },
    ],
  });
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
      questions: [
        {
          id: "q-1",
          text: "Question",
          options: [{ id: "o-1", text: "water" }],
          source_locator: "一、Python简介",
          supporting_excerpt: "Python语法和动态类型，以及解释型语言的本质",
        },
      ],
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
    const router = createTestRouter();
    await router.push(ROUTES.endlessAbyss);
    await router.isReady();

    const wrapper = mount(DungeonScholarEndlessAbyssPage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.find(".question-card").exists()).toBe(true);
    expect(wrapper.find(".question-card h1").exists()).toBe(true);
  });


  it("strips markdown formatting in question card and answer matching", async () => {
    mocks.createRun.mockResolvedValueOnce({
      run_id: "run-1",
      mode: "endless",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 10, time_left_sec: 900, pending_coins: 0 },
      questions: [{ id: "q-1", text: "**核心转变**是什么?", options: [{ id: "o-1", text: "**Water**" }] }],
    });

    const router = createTestRouter();
    await router.push({ path: ROUTES.endlessAbyss, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarEndlessAbyssPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.find(".question-card h1").text()).toContain("核心转变是什么?");
    expect(wrapper.find(".question-card h1").text()).not.toContain("**");

    const answerInput = wrapper.find('input[placeholder="Type the answer keyword"]');
    await answerInput.setValue("water");
    await answerInput.trigger("keydown.enter");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledWith("run-1", "q-1", ["o-1"], expect.any(Number));
  });

  it("renders feedback action for reporting errors", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.endlessAbyss);
    await router.isReady();

    const wrapper = mount(DungeonScholarEndlessAbyssPage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.find(".feedback-action").exists()).toBe(true);
  });

  it("renders question provenance details when available", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.endlessAbyss, query: { documentId: "doc-1", title: "Python" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarEndlessAbyssPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.text()).toContain("来源：一、Python简介");
    expect(wrapper.text()).toContain("摘录：Python语法和动态类型，以及解释型语言的本质");
  });

  it("renders run status notice for reduced reward", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.endlessAbyss);
    await router.isReady();

    const wrapper = mount(DungeonScholarEndlessAbyssPage, {
      global: { plugins: [router, i18n] },
    });

    const vm = wrapper.vm as unknown as { setReducedReward: () => void };
    vm.setReducedReward();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".run-status-notice").exists()).toBe(true);
  });

  it("navigates back when clicking return", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.endlessAbyss);
    await router.isReady();

    const wrapper = mount(DungeonScholarEndlessAbyssPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.find(".return-btn").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.gameModes);
  });
});
