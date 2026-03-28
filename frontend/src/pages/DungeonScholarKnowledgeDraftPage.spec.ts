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
      { component: { template: "<div>Game Modes</div>" }, path: ROUTES.gameModes },
      { component: { template: "<div>Level Path</div>" }, path: ROUTES.levelPath },
    ],
  });
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
    const router = createTestRouter();
    await router.push({ path: ROUTES.knowledgeDraft, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.find(".scroll-card").exists()).toBe(true);
    expect(wrapper.find(".scroll-paper h2").exists()).toBe(true);
  });


  it("strips markdown formatting in draft question and chips", async () => {
    mocks.createRun.mockResolvedValueOnce({
      run_id: "run-draft-1",
      mode: "draft",
      status: "running",
      run_state: { hp: 3, max_hp: 3, floor: 1, floor_total: 8, time_left_sec: 600, pending_coins: 0 },
      questions: [{ id: "q-1", text: "**Draft** question", options: [{ id: "o-1", text: "_Wu wei_" }, { id: "o-2", text: "**Legalism**" }] }],
    });

    const router = createTestRouter();
    await router.push({ path: ROUTES.knowledgeDraft, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(wrapper.find(".scroll-paper__body").text()).toContain("Draft question");
    expect(wrapper.find(".scroll-paper__body").text()).not.toContain("**");
    expect(wrapper.findAll(".draft-chip")[0].text()).toBe("Wu wei");
    expect(wrapper.findAll(".draft-chip")[1].text()).toBe("Legalism");
  });

  it("renders feedback action for reporting errors", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.knowledgeDraft, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.find(".feedback-action").exists()).toBe(true);
  });

  it("renders run status notice", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.knowledgeDraft, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
      global: { plugins: [router, i18n] },
    });

    const vm = wrapper.vm as unknown as { setShowNotice: () => void };
    vm.setShowNotice();
    await wrapper.vm.$nextTick();

    expect(wrapper.find(".run-status-notice").exists()).toBe(true);
  });

  it("navigates back when clicking back button", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.knowledgeDraft, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.find(".draft-title__back").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.path).toBe(ROUTES.levelPath);
  });

  it("submits selected draft option through runs api", async () => {
    const router = createTestRouter();
    await router.push({ path: ROUTES.knowledgeDraft, query: { documentId: "doc-1" } });
    await router.isReady();

    const wrapper = mount(DungeonScholarKnowledgeDraftPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    await wrapper.find(".draft-chip").trigger("click");
    await flushPromises();

    expect(mocks.submitAnswer).toHaveBeenCalledTimes(1);
  });
});
