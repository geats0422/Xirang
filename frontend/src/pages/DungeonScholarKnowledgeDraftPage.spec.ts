import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarKnowledgeDraftPage from "./DungeonScholarKnowledgeDraftPage.vue";

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
      { component: DungeonScholarKnowledgeDraftPage, path: ROUTES.knowledgeDraft },
      { component: { template: "<div>Library</div>" }, path: ROUTES.library },
      { component: { template: "<div>Game Modes</div>" }, path: ROUTES.gameModes },
      { component: { template: "<div>Level Path</div>" }, path: ROUTES.levelPath },
    ],
  });
}

async function mountKnowledgeDraftPage() {
  const router = createTestRouter();
  await router.push({ path: ROUTES.knowledgeDraft, query: { documentId: "doc-1" } });
  await router.isReady();

  const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
    global: { plugins: [router, i18n] },
  });

  await flushPromises();

  return {
    router,
    wrapper,
  };
}

function createDataTransfer(): DataTransfer {
  const records = new Map<string, string>();
  return {
    dropEffect: "move",
    effectAllowed: "move",
    files: [] as unknown as FileList,
    items: [] as unknown as DataTransferItemList,
    types: [],
    clearData: (format?: string) => {
      if (format) {
        records.delete(format);
        return;
      }
      records.clear();
    },
    getData: (format: string) => records.get(format) ?? "",
    setData: (format: string, data: string) => {
      records.set(format, data);
    },
    setDragImage: () => {},
  } as DataTransfer;
}

describe("DungeonScholarKnowledgeDraftPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getShopBalance.mockResolvedValue({ asset_code: "COIN", balance: 0 });
    mocks.createRun.mockResolvedValue({
      run_id: "run-draft-1",
      mode: "draft",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 600, pending_coins: 0 },
      questions: [{ id: "q-1", text: "Draft question", options: [{ id: "o-1", text: "Wu wei" }, { id: "o-2", text: "Legalism" }] }],
    });
    mocks.submitAnswer.mockResolvedValue({
      is_correct: true,
      run: {
        id: "run-draft-1",
        status: "running",
        score: 10,
        state: { hp: 3, max_hp: 3, floor: 2, floor_total: 8, time_left_sec: 595, pending_coins: 10 },
      },
      settlement: null,
    });
  });

  it("renders scroll card with content", async () => {
    const { wrapper } = await mountKnowledgeDraftPage();

    expect(wrapper.find(".scroll-card").exists()).toBe(true);
    expect(wrapper.find(".scroll-paper h2").exists()).toBe(true);
  });

  it("renders markdown in text segments while keeping blank slots", async () => {
    mocks.createRun.mockResolvedValueOnce({
      run_id: "run-draft-1",
      mode: "draft",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 600, pending_coins: 0 },
      questions: [
        {
          id: "q-1",
          text: "Use **clarity** in ____ lines.",
          options: [{ id: "o-1", text: "all" }],
        },
      ],
    });

    const { wrapper } = await mountKnowledgeDraftPage();

    expect(wrapper.find(".scroll-paper__body strong").exists()).toBe(true);
    expect(wrapper.find(".drop-slot").exists()).toBe(true);
  });

  it("renders feedback action for reporting errors", async () => {
    const { wrapper } = await mountKnowledgeDraftPage();

    expect(wrapper.find(".feedback-action").exists()).toBe(true);
  });

  it("renders run status notice", async () => {
    const { wrapper } = await mountKnowledgeDraftPage();

    const vm = wrapper.vm as unknown as { setShowNotice: () => void };
    vm.setShowNotice();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".run-status-notice").exists()).toBe(true);
  });

  it("navigates back when clicking back button", async () => {
    const { router, wrapper } = await mountKnowledgeDraftPage();

    await wrapper.find(".draft-title__back").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.levelPath);
  });

  it("submits selected draft option through runs api", async () => {
    const { wrapper } = await mountKnowledgeDraftPage();

    await wrapper.find(".draft-chip").trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
    expect(mocks.submitAnswer).toHaveBeenCalledWith("run-draft-1", "q-1", ["o-1"], expect.any(Number));
  });

  it("fills multiple blanks in click order and only submits after all blanks are filled", async () => {
    mocks.createRun.mockResolvedValue({
      run_id: "run-draft-1",
      mode: "draft",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 600, pending_coins: 0 },
      questions: [
        {
          id: "q-1",
          text: "Seek ____ and ____ in every line.",
          options: [
            { id: "o-1", text: "balance" },
            { id: "o-2", text: "clarity" },
            { id: "o-3", text: "noise" },
          ],
        },
      ],
    });

    const { wrapper } = await mountKnowledgeDraftPage();
    const chips = wrapper.findAll(".draft-chip");

    await chips[0].trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).not.toHaveBeenCalled();
    expect(wrapper.findAll(".drop-slot")[0].text()).toContain("balance");
    expect(wrapper.findAll(".draft-chip")[0].classes()).toContain("draft-chip--selected");

    await chips[1].trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
    expect(mocks.submitAnswer).toHaveBeenCalledWith(
      "run-draft-1",
      "q-1",
      ["o-1", "o-2"],
      expect.any(Number),
    );
  });

  it("shows feedback after wrong submission and advances after local correction", async () => {
    mocks.createRun.mockResolvedValue({
      run_id: "run-draft-1",
      mode: "draft",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 600, pending_coins: 0 },
      questions: [
        {
          id: "q-1",
          text: "First ____ ____",
          options: [
            { id: "o-1", text: "alpha" },
            { id: "o-2", text: "beta" },
            { id: "o-3", text: "gamma" },
          ],
        },
        {
          id: "q-2",
          text: "Second puzzle",
          options: [{ id: "o-4", text: "delta" }],
        },
      ],
    });

    mocks.submitAnswer
      .mockResolvedValueOnce({
        is_correct: false,
        feedback: {
          correct_option_ids: ["o-3", "o-2"],
          correct_answer: "gamma, beta",
          explanation: "The source sentence requires gamma and beta in order.",
        },
        run: {
          id: "run-draft-1",
          status: "running",
          score: 10,
          state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 590, pending_coins: 10 },
        },
        settlement: null,
      });

    const { wrapper } = await mountKnowledgeDraftPage();
    const chips = wrapper.findAll(".draft-chip");

    await chips[0].trigger("click");
    await chips[1].trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
    expect(wrapper.find(".scroll-paper__body").text()).toContain("First");
    expect(wrapper.find(".run-status-notice").exists()).toBe(true);
    expect(wrapper.find(".answer-feedback").exists()).toBe(true);
    expect(wrapper.text()).toContain("Correct answer:");

    const slots = wrapper.findAll(".drop-slot");
    await slots[0].trigger("click");
    await chips[2].trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain("Second puzzle");
    expect(wrapper.find(".answer-feedback").exists()).toBe(false);
  });

  it("supports drag filling and slot reordering before submit", async () => {
    mocks.createRun.mockResolvedValue({
      run_id: "run-draft-1",
      mode: "draft",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 600, pending_coins: 0 },
      questions: [
        {
          id: "q-1",
          text: "____ ____ ____",
          options: [
            { id: "o-1", text: "Dao" },
            { id: "o-2", text: "Flow" },
            { id: "o-3", text: "Heaven" },
          ],
        },
      ],
    });

    const { wrapper } = await mountKnowledgeDraftPage();
    const chips = wrapper.findAll(".draft-chip");

    const optionTransfer = createDataTransfer();
    await chips[2].trigger("dragstart", { dataTransfer: optionTransfer });
    await wrapper.findAll(".drop-slot")[0].trigger("drop", {
      dataTransfer: optionTransfer,
      preventDefault: () => {},
    });
    await chips[2].trigger("dragend");
    await flushPromises();

    expect(mocks.submitAnswer).not.toHaveBeenCalled();
    expect(wrapper.findAll(".drop-slot")[0].text()).toContain("Heaven");

    await chips[0].trigger("click");
    await flushPromises();
    expect(mocks.submitAnswer).not.toHaveBeenCalled();

    const slotTransfer = createDataTransfer();
    await wrapper.findAll(".drop-slot")[1].trigger("dragstart", { dataTransfer: slotTransfer });
    await wrapper.findAll(".drop-slot")[0].trigger("drop", {
      dataTransfer: slotTransfer,
      preventDefault: () => {},
    });
    await wrapper.findAll(".drop-slot")[1].trigger("dragend");
    await flushPromises();

    expect(wrapper.findAll(".drop-slot")[0].text()).toContain("Dao");
    expect(mocks.submitAnswer).not.toHaveBeenCalled();

    await chips[1].trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
    expect(mocks.submitAnswer.mock.calls[0][2]).toEqual(["o-1", "o-3", "o-2"]);
  });
});
