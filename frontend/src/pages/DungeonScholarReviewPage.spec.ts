import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarReviewPage from "./DungeonScholarReviewPage.vue";

const mocks = vi.hoisted(() => ({
  createRun: vi.fn(),
  submitAnswer: vi.fn(),
  submitFeedback: vi.fn(),
  getShopBalance: vi.fn(),
}));

vi.mock("../api/runs", () => ({
  createRun: mocks.createRun,
  submitAnswer: mocks.submitAnswer,
}));

vi.mock("../api/feedback", () => ({
  submitFeedback: mocks.submitFeedback,
}));

vi.mock("../api/shop", () => ({
  getShopBalance: mocks.getShopBalance,
}));

describe("DungeonScholarReviewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getShopBalance.mockResolvedValue({ balance: 12 });
    mocks.createRun.mockResolvedValue({
      run_id: "run-1",
      mode: "review",
      status: "running",
      run_state: { goal_total: 20 },
      questions: [
        {
          id: "q-1",
          text: "Python 的作者是谁？",
          question_type: "single_choice",
          options: [
            { id: "o-1", text: "Guido van Rossum" },
            { id: "o-2", text: "Bjarne Stroustrup" },
          ],
        },
      ],
    });
  });

  it("bootstraps a review run with review mode", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: ROUTES.review, component: DungeonScholarReviewPage },
        { path: ROUTES.levelPath, component: { template: "<div>Path</div>" } },
        { path: ROUTES.library, component: { template: "<div>Library</div>" } },
      ],
    });

    await router.push({ path: ROUTES.review, query: { mode: "review", mistakeReview: "true" } });
    await router.isReady();

    mount(DungeonScholarReviewPage, {
      global: { plugins: [router, i18n] },
    });
    await flushPromises();

    expect(mocks.createRun).toHaveBeenCalledWith(undefined, "review", 20, undefined, true);
  });
});
