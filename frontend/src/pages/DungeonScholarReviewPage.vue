<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import GameSettlementModal from "../components/GameSettlementModal.vue";
import { ApiError } from "../api/http";
import { createRun, submitAnswer, type RunQuestion } from "../api/runs";
import { submitFeedback } from "../api/feedback";
import { getShopBalance } from "../api/shop";
import { ROUTES } from "../constants/routes";

type RunStatus = "normal" | "reduced-reward" | "no-review-questions";

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();

const runId = ref<string | null>(null);
const questions = ref<RunQuestion[]>([]);
const questionIndex = ref(0);
const answer = ref("");
const selectedOptionIds = ref<string[]>([]);
const isSubmittingAnswer = ref(false);
const runStatus = ref<RunStatus>("normal");
const showNotice = ref(false);
const showFeedback = ref(false);
const lastAnswerCorrect = ref(false);
const feedbackCorrectAnswer = ref<string | null>(null);
const feedbackExplanation = ref<string | null>(null);
const awaitingCorrection = ref(false);
const expectedCorrectOptionIds = ref<string[]>([]);
const correctionRetryNotice = ref(false);
const questionStartAt = ref(Date.now());
const coins = ref<number | null>(null);

const showSettlement = ref(false);
const settlementXp = ref(0);
const settlementCoins = ref(0);
const settlementCombo = ref(0);
const settlementGoalCurrent = ref(0);
const settlementGoalTotal = ref(20);
const settlementTopPercent = ref<number | null>(null);

const currentQuestion = computed(() => questions.value[questionIndex.value] ?? null);
const isMistakeReview = computed(() => String(route.query.mistakeReview ?? "").toLowerCase() === "true");
const isFillInBlankQuestion = computed(() => currentQuestion.value?.question_type === "fill_in_blank");
const isMultiChoiceQuestion = computed(() => currentQuestion.value?.question_type === "multiple_choice");
const isChoiceQuestion = computed(() => !isFillInBlankQuestion.value);
const hasTypedAnswer = computed(() => answer.value.trim().length > 0);
const hasSelectableAnswer = computed(() => selectedOptionIds.value.length > 0);
const canSubmit = computed(() => (isFillInBlankQuestion.value ? hasTypedAnswer.value : hasSelectableAnswer.value));

const materialTitle = computed(() => {
  const rawTitle = route.query.title;
  if (typeof rawTitle === "string" && rawTitle.trim()) {
    return rawTitle;
  }
  return isMistakeReview.value
    ? t("reviewMode.defaults.mistakeTitle")
    : t("reviewMode.defaults.materialTitle");
});

const pageTitle = computed(() =>
  isMistakeReview.value
    ? t("reviewMode.header.mistakeTitle")
    : t("reviewMode.header.documentTitle", { material: materialTitle.value }),
);

const pageSubtitle = computed(() =>
  isMistakeReview.value
    ? t("reviewMode.header.mistakeSubtitle")
    : t("reviewMode.header.documentSubtitle"),
);

const questionTitle = computed(() => {
  if (runStatus.value === "no-review-questions") {
    return t("reviewMode.noReviewQuestionsTitle");
  }
  return currentQuestion.value?.text ?? t("reviewMode.loadingQuestion");
});
const progressCurrent = computed(() => Math.min(settlementGoalTotal.value, questionIndex.value + 1));
const progressWidth = computed(
  () => `${Math.min(100, (progressCurrent.value / Math.max(1, settlementGoalTotal.value)) * 100)}%`,
);

const questionHint = computed(() => {
  const firstOption = currentQuestion.value?.options[0];
  if (!firstOption?.text) {
    return t("reviewMode.hintEmpty");
  }
  const firstChar = firstOption.text.trim().charAt(0).toUpperCase();
  return firstChar ? t("reviewMode.hintStartsWith", { char: firstChar }) : t("reviewMode.hintEmpty");
});

const answerPrompt = computed(() => {
  if (isMultiChoiceQuestion.value) {
    return t("speedSurvival.tapOption");
  }
  if (isChoiceQuestion.value) {
    return t("speedSurvival.chooseBestOption");
  }
  return t("reviewMode.answerPlaceholder");
});

const noticeMessage = computed(() =>
  correctionRetryNotice.value ? t("reviewMode.retryNotice") : t("reviewMode.wrongAnswerNotice"),
);

const areSameOptionSet = (left: string[], right: string[]): boolean => {
  if (left.length !== right.length) {
    return false;
  }
  const leftSet = new Set(left);
  return right.every((item) => leftSet.has(item));
};

const normalizeComparableText = (value: string): string => {
  return value.trim().toLowerCase().replace(/\u3000/g, " ").replace(/\s+/g, "");
};

const normalizeTokens = (value: string): string[] => {
  return value
    .toLowerCase()
    .split(/[\s,，。！？!?;；:：/]+/)
    .map((token) => token.trim())
    .filter((token) => token.length > 0);
};

const resolveExpectedCorrectOptionIds = (payload: {
  correctOptionIds: string[];
  correctAnswerText: string | null;
  options: { id: string; text: string }[];
}): string[] => {
  if (payload.correctOptionIds.length > 0) {
    return payload.correctOptionIds;
  }
  if (!payload.correctAnswerText) {
    return [];
  }
  const answerTokens = normalizeTokens(payload.correctAnswerText);
  if (answerTokens.length === 0) {
    return [];
  }
  return payload.options
    .filter((option) => normalizeTokens(option.text).some((token) => answerTokens.includes(token)))
    .map((option) => option.id);
};

const resolveLeagueTopPercent = (accuracy: number | null | undefined): number | null => {
  if (typeof accuracy !== "number" || !Number.isFinite(accuracy)) {
    return null;
  }
  const normalized = Math.min(1, Math.max(0, accuracy));
  return Math.max(1, 100 - Math.round(normalized * 100));
};

const applySettlement = (settlement: {
  xp_earned: number;
  coins_earned: number;
  combo_max: number;
  goal_current?: number;
  goal_total?: number | null;
  accuracy: number;
}) => {
  settlementXp.value = settlement.xp_earned;
  settlementCoins.value = settlement.coins_earned;
  settlementCombo.value = settlement.combo_max;
  settlementGoalCurrent.value = settlement.goal_current ?? 0;
  settlementGoalTotal.value = settlement.goal_total ?? 20;
  settlementTopPercent.value = resolveLeagueTopPercent(settlement.accuracy);
  showSettlement.value = true;
};

const refreshBalance = async () => {
  try {
    const balance = await getShopBalance();
    coins.value = balance.balance;
  } catch {
    coins.value = null;
  }
};

const bootstrapRun = async () => {
  await refreshBalance();
  const rawDocumentId = route.query.documentId;
  const documentId = typeof rawDocumentId === "string" ? rawDocumentId : undefined;
  const rawPathId = route.query.pathId;
  const pathId = typeof rawPathId === "string" ? rawPathId : undefined;

  try {
    const created = await createRun(documentId, "review", 20, pathId, isMistakeReview.value);
    runId.value = created.run_id;
    questions.value = created.questions;
    questionIndex.value = 0;

    const goalTotal = Number(created.run_state.goal_total);
    if (Number.isFinite(goalTotal) && goalTotal > 0) {
      settlementGoalTotal.value = goalTotal;
    }
    questionStartAt.value = Date.now();
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      const detail =
        typeof error.detail === "object" && error.detail !== null && "detail" in error.detail
          ? String((error.detail as { detail: unknown }).detail)
          : null;
      if (detail === "no_review_questions") {
        runStatus.value = "no-review-questions";
        questions.value = [];
        return;
      }
    }
    runStatus.value = "reduced-reward";
  }
};

const goBack = async () => {
  await router.push({
    path: ROUTES.levelPath,
    query: {
      ...route.query,
      mode: "review",
    },
  });
};

const goLibrary = async () => {
  await router.push(ROUTES.library);
};

const toggleOptionSelection = (optionId: string) => {
  if (isSubmittingAnswer.value || isFillInBlankQuestion.value) {
    return;
  }

  if (isMultiChoiceQuestion.value) {
    if (selectedOptionIds.value.includes(optionId)) {
      selectedOptionIds.value = selectedOptionIds.value.filter((item) => item !== optionId);
      return;
    }
    selectedOptionIds.value = [...selectedOptionIds.value, optionId];
    return;
  }

  selectedOptionIds.value = [optionId];
};

const handleFeedback = async () => {
  if (!currentQuestion.value || !runId.value) {
    return;
  }
  const rawDocumentId = route.query.documentId;
  const documentId = typeof rawDocumentId === "string" ? rawDocumentId : "";
  try {
    await submitFeedback({
      question_id: currentQuestion.value.id,
      document_id: documentId,
      run_id: runId.value,
      feedback_type: "wrong_answer",
      detail_text: "User reported this review question has an error.",
    });
  } catch {
    // ignore feedback submission errors
  }
};

const castSpell = async () => {
  if (
    showSettlement.value ||
    isSubmittingAnswer.value ||
    !runId.value ||
    !currentQuestion.value ||
    !canSubmit.value
  ) {
    return;
  }

  const elapsedMs = Math.max(0, Date.now() - questionStartAt.value);
  const normalizedInput = answer.value.trim();
  const normalizedAnswer = normalizedInput.toLowerCase();
  const matchedOption = currentQuestion.value.options.find(
    (option) => option.text.trim().toLowerCase() === normalizedAnswer,
  );
  const submissionOptionIds = isFillInBlankQuestion.value
    ? (matchedOption ? [matchedOption.id] : [])
    : selectedOptionIds.value;

  if (awaitingCorrection.value) {
    const matchedByOption =
      expectedCorrectOptionIds.value.length > 0 &&
      areSameOptionSet(submissionOptionIds, expectedCorrectOptionIds.value);
    const normalizedCurrentAnswer = normalizeComparableText(normalizedInput);
    const normalizedCorrectAnswer = normalizeComparableText(feedbackCorrectAnswer.value ?? "");
    const matchedByAnswer =
      normalizedCurrentAnswer.length > 0 &&
      normalizedCorrectAnswer.length > 0 &&
      normalizedCurrentAnswer === normalizedCorrectAnswer;

    if (!matchedByOption && !matchedByAnswer) {
      showNotice.value = true;
      showFeedback.value = true;
      correctionRetryNotice.value = true;
      return;
    }

    awaitingCorrection.value = false;
    expectedCorrectOptionIds.value = [];
    showFeedback.value = false;
    showNotice.value = false;
    correctionRetryNotice.value = false;
    questionIndex.value = Math.min(questionIndex.value + 1, questions.value.length - 1);
    questionStartAt.value = Date.now();
    answer.value = "";
    selectedOptionIds.value = [];
    return;
  }

  isSubmittingAnswer.value = true;

  try {
    const result = await submitAnswer(
      runId.value,
      currentQuestion.value.id,
      submissionOptionIds,
      elapsedMs,
      isFillInBlankQuestion.value ? normalizedInput : undefined,
    );

    lastAnswerCorrect.value = result.is_correct;
    feedbackCorrectAnswer.value = result.feedback?.correct_answer ?? null;
    feedbackExplanation.value = result.feedback?.explanation ?? null;

    if (!result.is_correct) {
      showNotice.value = true;
      showFeedback.value = true;
      correctionRetryNotice.value = false;
      awaitingCorrection.value = true;
      expectedCorrectOptionIds.value = resolveExpectedCorrectOptionIds({
        correctOptionIds: result.feedback?.correct_option_ids ?? [],
        correctAnswerText: result.feedback?.correct_answer ?? null,
        options: currentQuestion.value.options,
      });
      if (result.settlement) {
        applySettlement(result.settlement);
        await refreshBalance();
      }
      return;
    }

    showNotice.value = false;
    showFeedback.value = false;
    awaitingCorrection.value = false;
    correctionRetryNotice.value = false;
    expectedCorrectOptionIds.value = [];

    if (result.settlement) {
      applySettlement(result.settlement);
      await refreshBalance();
    } else {
      questionIndex.value = Math.min(questionIndex.value + 1, questions.value.length - 1);
      questionStartAt.value = Date.now();
      answer.value = "";
      selectedOptionIds.value = [];
    }
  } catch {
    runStatus.value = "reduced-reward";
  } finally {
    isSubmittingAnswer.value = false;
  }
};

const closeSettlement = () => {
  showSettlement.value = false;
};

watch(locale, () => {
  document.title = t("reviewMode.metaTitle");
});

watch(
  currentQuestion,
  () => {
    showNotice.value = false;
    showFeedback.value = false;
    lastAnswerCorrect.value = false;
    feedbackCorrectAnswer.value = null;
    feedbackExplanation.value = null;
    awaitingCorrection.value = false;
    expectedCorrectOptionIds.value = [];
    correctionRetryNotice.value = false;
    answer.value = "";
    selectedOptionIds.value = [];
    isSubmittingAnswer.value = false;
  },
  { immediate: true },
);

onMounted(async () => {
  document.title = t("reviewMode.metaTitle");
  await bootstrapRun();
});
</script>

<template>
  <main class="review-page">
    <section class="review-shell" :aria-label="t('reviewMode.shellAria')">
      <header class="review-status">
        <div>
          <p class="review-status__eyebrow">{{ t("reviewMode.header.eyebrow") }}</p>
          <h1>{{ pageTitle }}</h1>
          <p class="review-status__subtitle">{{ pageSubtitle }}</p>
        </div>
        <div class="review-meta">
          <span>{{ t("reviewMode.progressLabel", { current: progressCurrent, total: settlementGoalTotal }) }}</span>
          <button class="review-meta__coin" type="button">🪙 {{ coins ?? "--" }}</button>
        </div>
      </header>

      <div class="review-progress" role="presentation">
        <span class="review-progress__fill" :style="{ width: progressWidth }" />
      </div>

      <section class="battle-stage">
        <article class="question-card" :aria-label="t('reviewMode.questionCardAria')">
          <p class="question-card__tag">{{ t("reviewMode.questionTag") }}</p>
          <h2>{{ questionTitle }}</h2>
          <footer class="question-card__footer">
            <span>{{ materialTitle }}</span>
            <span class="question-card__hint">{{ questionHint }}</span>
          </footer>
        </article>
      </section>

      <section v-if="runStatus !== 'no-review-questions' && isChoiceQuestion" class="review-options">
        <p class="review-options__prompt">{{ answerPrompt }}</p>
        <div class="review-options__grid">
          <button
            v-for="option in currentQuestion?.options ?? []"
            :key="option.id"
            class="review-option"
            :class="{ 'review-option--active': selectedOptionIds.includes(option.id) }"
            type="button"
            @click="toggleOptionSelection(option.id)"
          >
            {{ option.text }}
          </button>
        </div>
      </section>

      <footer v-if="runStatus !== 'no-review-questions'" class="answer-zone">
        <label
          v-if="isFillInBlankQuestion"
          class="answer-input"
          :class="{ 'answer-input--ready': hasTypedAnswer, 'answer-input--submitting': isSubmittingAnswer }"
        >
          <span aria-hidden="true">✎</span>
          <input
            v-model="answer"
            type="text"
            :placeholder="t('reviewMode.answerPlaceholder')"
            :disabled="isSubmittingAnswer"
            @keydown.enter="castSpell"
          />
        </label>

        <button
          class="cast-btn"
          :class="{ 'cast-btn--ready': canSubmit, 'cast-btn--submitting': isSubmittingAnswer }"
          type="button"
          :disabled="isSubmittingAnswer || !canSubmit"
          @click="castSpell"
        >
          {{ isSubmittingAnswer ? t("reviewMode.submitting") : t("reviewMode.submit") }}
        </button>
        <button class="return-btn" type="button" @click="goBack">{{ t("reviewMode.backToPath") }}</button>
        <button class="feedback-action" type="button" @click="handleFeedback">{{ t("common.reportQuestionIssue") }}</button>

        <div v-if="showFeedback && !lastAnswerCorrect" class="answer-feedback answer-feedback--wrong">
          <div class="answer-feedback__header">
            <span class="answer-feedback__icon">✗</span>
            <span class="answer-feedback__title">{{ t("speedSurvival.incorrect") }}</span>
          </div>
          <div v-if="feedbackCorrectAnswer" class="answer-feedback__correct">
            <strong>{{ t("speedSurvival.correctAnswer") }}</strong> {{ feedbackCorrectAnswer }}
          </div>
          <div v-if="feedbackExplanation" class="answer-feedback__explanation">
            <strong>{{ t("speedSurvival.explanation") }}</strong> {{ feedbackExplanation }}
          </div>
        </div>

        <div v-if="showNotice" class="run-status-notice run-status-notice--danger">
          {{ noticeMessage }}
        </div>

        <div v-if="runStatus === 'reduced-reward'" class="run-status-notice">
          {{ t("reviewMode.reducedRewardNotice") }}
        </div>
      </footer>

      <footer v-else class="answer-zone answer-zone--empty">
        <div class="run-status-notice">{{ t("reviewMode.noReviewQuestionsNotice") }}</div>
        <button class="return-btn" type="button" @click="goBack">{{ t("reviewMode.backToPath") }}</button>
      </footer>
    </section>

    <GameSettlementModal
      :visible="showSettlement"
      :mode-name="t('reviewMode.settlementModeName')"
      :xp-gained="settlementXp"
      :coin-reward="settlementCoins"
      :combo-count="settlementCombo"
      :goal-current="settlementGoalCurrent"
      :goal-total="settlementGoalTotal"
      :league-top-percent="settlementTopPercent"
      :goal-text="t('reviewMode.settlementGoal')"
      @close="closeSettlement"
      @confirm="goLibrary"
    />
  </main>
</template>

<style scoped>
.review-page {
  background: var(--color-page-bg);
  min-height: 100vh;
  padding: 24px;
}

.review-shell {
  background: color-mix(in srgb, var(--color-surface) 92%, var(--color-surface-alt) 8%);
  border: 1px solid var(--color-border);
  border-radius: 24px;
  margin: 0 auto;
  max-width: 980px;
  min-height: calc(100vh - 48px);
  padding: 24px;
}

.review-status {
  align-items: end;
  display: flex;
  gap: 20px;
  justify-content: space-between;
}

.review-status__eyebrow {
  color: var(--color-primary-600);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 0;
}

.review-status h1 {
  font-family: var(--font-serif);
  font-size: 36px;
  margin: 8px 0 0;
}

.review-status__subtitle {
  color: var(--color-text-secondary);
  margin: 8px 0 0;
}

.review-meta {
  align-items: end;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.review-meta span {
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 700;
}

.review-meta__coin {
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-100);
  border-radius: 999px;
  color: var(--color-primary-700);
  font-weight: 700;
  min-height: 40px;
  padding: 0 14px;
}

.review-progress {
  background: var(--color-border-soft);
  border-radius: 999px;
  height: 8px;
  margin-top: 18px;
  overflow: hidden;
}

.review-progress__fill {
  background: linear-gradient(90deg, var(--color-primary-500), var(--color-muted-gold));
  display: block;
  height: 100%;
}

.battle-stage {
  margin-top: 24px;
}

.question-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-soft);
  border-radius: 24px;
  box-shadow: var(--shadow-card);
  min-height: 220px;
  padding: 24px;
}

.question-card__tag {
  color: var(--color-primary-600);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 0;
}

.question-card h2 {
  font-family: var(--font-serif);
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.18;
  margin: 16px 0 0;
}

.question-card__footer {
  align-items: center;
  color: var(--color-text-secondary);
  display: flex;
  justify-content: space-between;
  margin-top: 18px;
}

.question-card__hint {
  color: var(--color-primary-600);
  font-weight: 700;
}

.review-options {
  margin-top: 18px;
}

.review-options__prompt {
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 700;
  margin: 0 0 12px;
}

.review-options__grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.review-option {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  color: var(--color-text-strong);
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  min-height: 56px;
  padding: 14px 16px;
  text-align: left;
}

.review-option--active {
  background: var(--color-primary-50);
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary-500) 14%, transparent);
  color: var(--color-primary-700);
}

.answer-zone {
  display: grid;
  gap: 14px;
  margin-top: 24px;
}

.answer-input {
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  display: flex;
  gap: 10px;
  min-height: 58px;
  padding: 0 16px;
}

.answer-input--ready {
  border-color: var(--color-primary-500);
}

.answer-input input {
  background: transparent;
  border: 0;
  color: var(--color-text-strong);
  flex: 1;
  font-size: 16px;
  outline: 0;
}

.cast-btn,
.return-btn,
.feedback-action {
  align-items: center;
  border-radius: 14px;
  cursor: pointer;
  display: inline-flex;
  font-weight: 700;
  justify-content: center;
  min-height: 48px;
  padding: 0 18px;
}

.cast-btn {
  background: var(--color-border-soft);
  border: 1px solid transparent;
  color: var(--color-text-muted);
}

.cast-btn--ready {
  background: var(--color-primary-500);
  color: var(--color-surface);
}

.return-btn,
.feedback-action {
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

.answer-feedback {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 14px 16px;
}

.answer-feedback__header {
  align-items: center;
  color: #b91c1c;
  display: flex;
  gap: 8px;
  font-weight: 800;
}

.answer-feedback__correct,
.answer-feedback__explanation {
  color: var(--color-text-secondary);
  margin-top: 10px;
}

.run-status-notice {
  border-radius: 12px;
  color: var(--color-text-secondary);
  font-weight: 700;
  padding: 12px 14px;
}

.run-status-notice--danger {
  background: #fef2f2;
  color: #b91c1c;
}

@media (max-width: 768px) {
  .review-page {
    padding: 14px;
  }

  .review-shell {
    min-height: auto;
    padding: 16px;
  }

  .review-status {
    align-items: start;
    flex-direction: column;
  }

  .review-meta {
    align-items: start;
  }

  .question-card__footer {
    align-items: start;
    flex-direction: column;
    gap: 8px;
  }
}
</style>
