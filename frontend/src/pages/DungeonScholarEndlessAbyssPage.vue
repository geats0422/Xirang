<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import GameSettlementModal from "../components/GameSettlementModal.vue";
import { ROUTES } from "../constants/routes";
import { createRun, submitAnswer, useRunRevive, type RunQuestion } from "../api/runs";
import { submitFeedback } from "../api/feedback";
import { getShopBalance } from "../api/shop";

const { t, locale } = useI18n();

onMounted(() => {
  document.title = t("endlessAbyss.metaTitle");
});

// Update document title reactively when locale changes
watch(locale, () => {
  document.title = t("endlessAbyss.metaTitle");
});

type RunStatus = "normal" | "reduced-reward";

const route = useRoute();
const router = useRouter();
const shopRoute = ROUTES.shop;

const maxHp = ref<number | null>(null);
const hpLevel = ref<number | null>(null);
const floor = ref<number | null>(null);
const floorTotal = ref<number | null>(null);
const timeLeftSec = ref<number | null>(null);
const coins = ref<number | null>(null);

const runId = ref<string | null>(null);
const questions = ref<RunQuestion[]>([]);
const questionIndex = ref(0);
const runBootstrapFailed = ref(false);
const questionStartAt = ref<number>(Date.now());
let tickerId: number | null = null;

const answer = ref("");
const isSubmittingAnswer = ref(false);
const showSettlement = ref(false);
const runStatus = ref<RunStatus>("normal");
const settlementXp = ref(0);
const settlementCoins = ref(0);
const settlementCombo = ref(0);
const settlementGoalCurrent = ref(0);
const settlementGoalTotal = ref(10);
const settlementTopPercent = ref<number | null>(null);

const showNotice = ref(false);
const showFeedback = ref(false);
const lastAnswerCorrect = ref(false);
const feedbackCorrectAnswer = ref<string | null>(null);
const feedbackExplanation = ref<string | null>(null);
const awaitingCorrection = ref(false);
const expectedCorrectOptionIds = ref<string[]>([]);
const correctionRetryNotice = ref(false);
const showReviveModal = ref(false);
const reviveError = ref("");
const reviveShieldCount = ref(0);
const reviveShieldExpiresAt = ref<string | null>(null);

const materialTitle = computed(() => {
  const rawTitle = route.query.title;
  return typeof rawTitle === "string" && rawTitle.trim() ? rawTitle : t("endlessAbyss.ancientWisdom");
});

const chapterTitle = computed(() =>
  t("endlessAbyss.chapterLabel", { n: floor.value ?? "--", title: materialTitle.value }),
);

const time = computed(() => {
  if (timeLeftSec.value === null) {
    return "--:--";
  }
  const minutes = Math.floor(timeLeftSec.value / 60)
    .toString()
    .padStart(2, "0");
  const seconds = Math.floor(timeLeftSec.value % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}`;
});

const currentQuestion = computed(() => questions.value[questionIndex.value] ?? null);

const questionTitle = computed(() => {
  if (runBootstrapFailed.value) {
    return t("endlessAbyss.loadingQuestionFailed");
  }
  if (currentQuestion.value?.text) {
    return currentQuestion.value.text;
  }
  return t("endlessAbyss.loadingQuestion");
});

const hasTypedAnswer = computed(() => answer.value.trim().length > 0);

const defaultWrongAnswerNotice = computed(() => {
  if (locale.value === "zh-CN") {
    return "⚠ 回答错误，生命值下降。";
  }
  if (locale.value === "zh-TW") {
    return "⚠ 回答錯誤，生命值下降。";
  }
  return "⚠ Wrong answer. HP decreased.";
});

const correctionRetryNoticeText = computed(() => {
  if (locale.value === "zh-CN") {
    return "⚠ 仍未答对，请继续修正。";
  }
  if (locale.value === "zh-TW") {
    return "⚠ 仍未答對，請繼續修正。";
  }
  return "⚠ Still not correct, please keep revising.";
});

const noticeMessage = computed(() => {
  return correctionRetryNotice.value
    ? correctionRetryNoticeText.value
    : defaultWrongAnswerNotice.value;
});


const questionHint = computed(() => {
  const firstOption = currentQuestion.value?.options[0];
  if (!firstOption?.text) {
    return t("endlessAbyss.hintNoOption");
  }
  const firstChar = firstOption.text.trim().charAt(0).toUpperCase();
  return firstChar ? `${t("endlessAbyss.hintStartsWith", { char: firstChar })}` : t("endlessAbyss.hintNoOption");
});

const reviveShieldActive = computed(() => reviveShieldCount.value > 0);

const floorProgress = computed(() => {
  if (floor.value === null || floorTotal.value === null) {
    return 0;
  }
  return (floor.value / Math.max(1, floorTotal.value)) * 100;
});

const resolveLeagueTopPercent = (accuracy: number | null | undefined): number | null => {
  if (typeof accuracy !== "number" || !Number.isFinite(accuracy)) {
    return null;
  }
  const normalized = Math.min(1, Math.max(0, accuracy));
  return Math.max(1, 100 - Math.round(normalized * 100));
};

const areSameOptionSet = (a: string[], b: string[]): boolean => {
  if (a.length !== b.length) {
    return false;
  }
  const setA = new Set(a);
  return b.every((item) => setA.has(item));
};

const normalizeComparableText = (value: string): string => {
  return value
    .trim()
    .toLowerCase()
    .replace(/\u3000/g, " ")
    .replace(/\s+/g, "");
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
    .filter((option) => {
      const optionTokens = normalizeTokens(option.text);
      return optionTokens.some((token) => answerTokens.includes(token));
    })
    .map((option) => option.id);
};

const applyRunState = (state: Record<string, unknown> | null | undefined) => {
  if (!state) {
    return;
  }
  const hp = Number(state.hp);
  const maxHpValue = Number(state.max_hp);
  const floorValue = Number(state.floor);
  const floorTotalValue = Number(state.floor_total);
  const timeValue = Number(state.time_left_sec);
  const shieldCount = Number(state.revive_shield_count);
  const shieldExpires = typeof state.revive_shield_expires_at === "string"
    ? state.revive_shield_expires_at
    : null;
  hpLevel.value = Number.isFinite(hp) ? hp : hpLevel.value;
  maxHp.value = Number.isFinite(maxHpValue) ? maxHpValue : maxHp.value;
  floor.value = Number.isFinite(floorValue) ? floorValue : floor.value;
  floorTotal.value = Number.isFinite(floorTotalValue) ? floorTotalValue : floorTotal.value;
  timeLeftSec.value = Number.isFinite(timeValue) ? timeValue : timeLeftSec.value;
  reviveShieldCount.value = Number.isFinite(shieldCount) ? shieldCount : 0;
  reviveShieldExpiresAt.value = shieldExpires;
};

const startTicker = () => {
  if (tickerId !== null) {
    window.clearInterval(tickerId);
  }
  tickerId = window.setInterval(() => {
    if (showSettlement.value || timeLeftSec.value === null || timeLeftSec.value <= 0) {
      return;
    }
    timeLeftSec.value = Math.max(0, timeLeftSec.value - 1);
  }, 1000);
};

const stopTicker = () => {
  if (tickerId !== null) {
    window.clearInterval(tickerId);
    tickerId = null;
  }
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
  const documentId = typeof rawDocumentId === "string" ? rawDocumentId : "";
  const rawPathId = route.query.pathId;
  const pathId = typeof rawPathId === "string" ? rawPathId : undefined;
  const isMistakeReview = String(route.query.mistakeReview ?? "").toLowerCase() === "true";
  if (!documentId) {
    return;
  }

  try {
    const created = await createRun(documentId, "endless", 10, pathId, isMistakeReview);
    runBootstrapFailed.value = false;
    runId.value = created.run_id;
    questions.value = created.questions;
    questionIndex.value = 0;
    applyRunState(created.run_state);
    questionStartAt.value = Date.now();
    startTicker();
  } catch {
    runBootstrapFailed.value = true;
    runStatus.value = "reduced-reward";
  }
};

const goBack = async () => {
  const isMistakeReview = String(route.query.mistakeReview ?? "").toLowerCase() === "true";
  await router.push({
    path: isMistakeReview ? ROUTES.gameModes : route.query.documentId ? ROUTES.levelPath : ROUTES.gameModes,
    query: route.query,
  });
};

const goLibrary = async () => {
  await router.push(ROUTES.library);
};

const castSpell = async () => {
  if (
    showSettlement.value ||
    isSubmittingAnswer.value ||
    !answer.value.trim() ||
    !runId.value ||
    !currentQuestion.value
  ) {
    return;
  }

  const elapsedMs = Math.max(0, Date.now() - questionStartAt.value);
  const normalizedInput = answer.value.trim();
  const normalizedAnswer = normalizedInput.toLowerCase();
  const isFillInBlankQuestion = currentQuestion.value.question_type === "fill_in_blank";
  const matchedOption = currentQuestion.value.options.find(
    (option) => option.text.trim().toLowerCase() === normalizedAnswer,
  );
  const selectedOptionIds = matchedOption ? [matchedOption.id] : [];

  if (awaitingCorrection.value) {
    const matchedByOption = expectedCorrectOptionIds.value.length > 0 && areSameOptionSet(selectedOptionIds, expectedCorrectOptionIds.value);
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
    return;
  }

  isSubmittingAnswer.value = true;

  try {
    const result = await submitAnswer(
      runId.value,
      currentQuestion.value.id,
      selectedOptionIds,
      elapsedMs,
      isFillInBlankQuestion ? normalizedInput : undefined,
    );
    applyRunState(result.run.state);

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
        settlementXp.value = result.settlement.xp_earned;
        settlementCoins.value = result.settlement.coins_earned;
        settlementCombo.value = result.settlement.combo_max;
        settlementGoalCurrent.value = result.settlement.goal_current ?? 0;
        settlementGoalTotal.value = result.settlement.goal_total ?? 10;
        settlementTopPercent.value = resolveLeagueTopPercent(result.settlement.accuracy);
        showSettlement.value = true;
        await refreshBalance();
        return;
      }
      if (result.run.status === "aborted") {
        reviveError.value = "";
        showReviveModal.value = true;
        stopTicker();
      }
      return;
    }

    showNotice.value = false;
    showFeedback.value = false;
    awaitingCorrection.value = false;
    correctionRetryNotice.value = false;
    expectedCorrectOptionIds.value = [];

    if (result.settlement) {
      settlementXp.value = result.settlement.xp_earned;
      settlementCoins.value = result.settlement.coins_earned;
      settlementCombo.value = result.settlement.combo_max;
      settlementGoalCurrent.value = result.settlement.goal_current ?? 0;
      settlementGoalTotal.value = result.settlement.goal_total ?? 10;
      settlementTopPercent.value = resolveLeagueTopPercent(result.settlement.accuracy);
      showSettlement.value = true;
      await refreshBalance();
    } else {
      questionIndex.value = Math.min(questionIndex.value + 1, questions.value.length - 1);
      questionStartAt.value = Date.now();
      if (result.run.status === "aborted") {
        reviveError.value = "";
        showReviveModal.value = true;
        stopTicker();
      }
    }
  } catch {
    runStatus.value = "reduced-reward";
  } finally {
    answer.value = "";
    isSubmittingAnswer.value = false;
  }
};

const closeSettlement = () => {
  showSettlement.value = false;
}


const purchaseRevive = async () => {
  if (!runId.value) {
    return;
  }
  reviveError.value = "";
  try {
    const result = await useRunRevive(runId.value);
    applyRunState(result.run.state);
    coins.value = result.coin_balance;
    showReviveModal.value = false;
    questionStartAt.value = Date.now();
    startTicker();
  } catch (error) {
    const message = error instanceof Error ? error.message : t("endlessAbyss.reviveFallbackError");
    reviveError.value = message;
  }
};

const leaveAbyss = async () => {
  showReviveModal.value = false;
  await goLibrary();
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
      detail_text: "User reported this question has an error.",
    });
  } catch (error) {
    console.error("Failed to submit feedback:", error);
  }
};
;

const goShop = async () => {
  await router.push(shopRoute);
};

const setShowNotice = () => {
  showNotice.value = true;
};

const setReducedReward = () => {
  runStatus.value = "reduced-reward";
};

defineExpose({
  setShowNotice,
  setReducedReward,
});

onMounted(async () => {
  await bootstrapRun();
});

watch(showReviveModal, (visible) => {
  if (visible) {
    stopTicker();
  } else if (!showSettlement.value) {
    startTicker();
  }
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
    isSubmittingAnswer.value = false;
  },
  { immediate: true },
);

onUnmounted(() => {
  stopTicker();
});
</script>

<template>
  <main class="abyss-page">
    <section class="abyss-shell" :aria-label="t('endlessAbyss.shellAria')">
      <header class="abyss-status">
        <div class="hp-block" :aria-label="t('endlessAbyss.hpAria')">
          <span v-for="index in maxHp" :key="index" class="hp-heart" :class="{ 'hp-heart--empty': index > (hpLevel ?? 0) }">
            ♥
          </span>
          <span class="hp-label">{{ t("endlessAbyss.hpLevel", { level: hpLevel ?? "--" }) }}</span>
        </div>

        <div class="floor-block" :aria-label="t('endlessAbyss.floorAria')">
          <p>{{ t("endlessAbyss.floor", { floor: floor ?? "--" }) }}</p>
          <div class="floor-track" role="presentation">
            <span class="floor-fill" :style="{ width: `${floorProgress}%` }" />
          </div>
          <span>{{ floorTotal ?? "--" }}</span>
        </div>

        <div class="meta-block" :aria-label="t('endlessAbyss.metaAria')">
          <span>🕒 {{ time }}</span>
          <button class="meta-coin" type="button" @click="goShop">🪙 {{ coins ?? "--" }}</button>
        </div>
      </header>

      <section class="battle-stage">
        <div class="dragon-bg" aria-hidden="true">
          <div class="dragon-art" />
          <div class="dragon-fog" />
        </div>

        <article class="question-card" :aria-label="t('endlessAbyss.questionCardAria')">
          <p class="question-card__tag">{{ t("endlessAbyss.questionTag") }}</p>
          <h1>{{ questionTitle }}</h1>

          <footer class="question-card__footer">
            <span>{{ chapterTitle }}</span>
            <span class="question-card__hint">{{ questionHint }}</span>
          </footer>
        </article>
      </section>

      <footer class="answer-zone">
        <label class="answer-input" :class="{ 'answer-input--ready': hasTypedAnswer, 'answer-input--submitting': isSubmittingAnswer }">
          <span aria-hidden="true">✎</span>
          <input v-model="answer" type="text" :placeholder="t('endlessAbyss.answerPlaceholder')" :disabled="isSubmittingAnswer" @keydown.enter="castSpell" />
        </label>

        <button
          class="cast-btn"
          :class="{ 'cast-btn--ready': hasTypedAnswer, 'cast-btn--submitting': isSubmittingAnswer }"
          type="button"
          :disabled="isSubmittingAnswer || !hasTypedAnswer"
          @click="castSpell"
        >
          {{ isSubmittingAnswer ? t("endlessAbyss.casting") : t("endlessAbyss.castSpell") }}
        </button>
        <button class="return-btn" type="button" @click="goBack">{{ t("endlessAbyss.returnToModeSelect") }}</button>

        <button class="feedback-action" type="button" @click="handleFeedback">
          {{ t("common.reportQuestionIssue") }}
        </button>

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
          {{ t("endlessAbyss.reducedRewardNotice") }}
        </div>
      </footer>
    </section>

    <div v-if="showReviveModal" class="revive-overlay">
      <div class="revive-modal" role="dialog" aria-modal="true" :aria-label="t('endlessAbyss.reviveModal.dialogAria')">
        <p class="revive-modal__eyebrow">{{ t("endlessAbyss.reviveModal.eyebrow") }}</p>
        <h2>{{ t("endlessAbyss.reviveModal.title") }}</h2>
        <p>{{ t("endlessAbyss.reviveModal.description") }}</p>
        <p v-if="reviveShieldActive" class="revive-modal__buff">{{ t("endlessAbyss.reviveModal.shieldActive", { time: reviveShieldExpiresAt ?? t('endlessAbyss.reviveModal.soon') }) }}</p>
        <p v-if="reviveError" class="revive-modal__error">{{ reviveError }}</p>
        <div class="revive-modal__actions">
          <button class="cast-btn" type="button" @click="purchaseRevive">{{ t("endlessAbyss.reviveModal.useCoins") }}</button>
          <button class="return-btn" type="button" @click="leaveAbyss">{{ t("endlessAbyss.reviveModal.leave") }}</button>
        </div>
      </div>
    </div>

    <GameSettlementModal
      :visible="showSettlement"
      :mode-name="t('endlessAbyss.settlementModeName')"
      :xp-gained="settlementXp"
      :coin-reward="settlementCoins"
      :combo-count="settlementCombo"
      :goal-current="settlementGoalCurrent"
      :goal-total="settlementGoalTotal"
      :league-top-percent="settlementTopPercent"
      :goal-text="t('endlessAbyss.settlementGoal')"
      @close="closeSettlement"
      @confirm="goLibrary"
    />
  </main>
</template>

<style scoped>
.abyss-page {
  background: radial-gradient(
      circle at 20% 12%,
      color-mix(in srgb, var(--color-cyan-100) 40%, transparent),
      transparent 32%
    ),
    radial-gradient(
      circle at 86% 86%,
      color-mix(in srgb, var(--color-badge-blue-bg) 40%, transparent),
      transparent 36%
    ),
    var(--color-page-bg);
  min-height: 100vh;
  padding: 28px;
}

.abyss-shell {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin: 0 auto;
  max-width: 1040px;
  overflow: hidden;
}

.abyss-status {
  align-items: center;
  border-bottom: 1px solid var(--color-border-soft);
  display: grid;
  gap: 18px;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr) auto;
  padding: 12px 16px;
}

.hp-block {
  align-items: center;
  display: flex;
  gap: 4px;
}

.hp-heart {
  color: var(--color-trend-down);
  font-size: 14px;
}

.hp-heart--empty {
  color: var(--color-border);
}

.hp-label {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 700;
  margin-left: 8px;
}

.floor-block {
  align-items: center;
  display: grid;
  gap: 8px;
  grid-template-columns: auto minmax(0, 1fr) auto;
}

.floor-block p,
.floor-block span {
  color: var(--color-primary-600);
  font-size: 11px;
  font-weight: 700;
  margin: 0;
}

.floor-track {
  background: var(--color-progress-track);
  border-radius: 999px;
  height: 6px;
  overflow: hidden;
}

.floor-fill {
  background: var(--color-primary-500);
  display: block;
  height: 100%;
}

.meta-block {
  align-items: center;
  display: flex;
  gap: 8px;
}

.meta-block span {
  background: var(--color-streak-bg);
  border: 1px solid color-mix(in srgb, var(--color-streak-bg) 72%, var(--color-muted-gold) 28%);
  border-radius: 999px;
  color: var(--color-soft-brown);
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
}

.meta-coin {
  background: var(--color-streak-bg);
  border: 1px solid color-mix(in srgb, var(--color-streak-bg) 72%, var(--color-muted-gold) 28%);
  border-radius: 999px;
  color: var(--color-soft-brown);
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
}

.battle-stage {
  margin: 18px auto 0;
  max-width: 760px;
  min-height: 530px;
  position: relative;
}

.dragon-bg {
  background: radial-gradient(
      circle at 26% 26%,
      color-mix(in srgb, var(--color-text-muted) 32%, transparent),
      transparent 28%
    ),
    radial-gradient(
      circle at 56% 38%,
      color-mix(in srgb, var(--color-text-muted) 18%, transparent),
      transparent 42%
    ),
    linear-gradient(
      145deg,
      color-mix(in srgb, var(--color-text-light-slate) 72%, var(--color-text-secondary) 28%) 0%,
      var(--color-text-muted) 44%,
      var(--color-text-tertiary) 72%,
      color-mix(in srgb, var(--color-text-muted) 86%, var(--color-text-light-slate) 14%) 100%
    );
  border-radius: 2px;
  box-shadow: inset 0 -80px 140px color-mix(in srgb, var(--color-text-primary) 32%, transparent);
  height: 100%;
  overflow: hidden;
  position: absolute;
  width: 100%;
}

.dragon-art {
  background-image: linear-gradient(
      180deg,
      color-mix(in srgb, var(--color-surface) 8%, transparent),
      color-mix(in srgb, var(--color-text-primary) 14%, transparent)
    ),
    url("/figma-endless-abyss-dragon-source.png");
  background-position: center, 60% 12%;
  background-repeat: no-repeat;
  background-size: cover, 118% auto;
  filter: grayscale(0.1) contrast(0.9) brightness(0.94);
  inset: 0;
  opacity: 0.92;
  position: absolute;
}

.dragon-fog {
  background: linear-gradient(
      180deg,
      color-mix(in srgb, var(--color-surface) 12%, transparent),
      color-mix(in srgb, var(--color-text-primary) 8%, transparent) 44%,
      color-mix(in srgb, var(--color-surface) 22%, transparent) 100%
    ),
    radial-gradient(
      circle at 17% 18%,
      color-mix(in srgb, var(--color-surface) 24%, transparent),
      transparent 22%
    ),
    radial-gradient(
      circle at 28% 58%,
      color-mix(in srgb, var(--color-surface) 8%, transparent),
      transparent 32%
    );
  inset: 0;
  position: absolute;
}

.question-card {
  background: var(--color-surface);
  border: 1px solid var(--color-primary-100);
  border-top: 3px solid var(--color-cyan-100);
  border-radius: 16px;
  box-shadow: var(--shadow-elevated);
  bottom: 62px;
  left: 72px;
  max-width: 478px;
  padding: 16px 18px 12px;
  position: absolute;
  width: calc(100% - 144px);
}

.question-card__tag {
  background: var(--color-cyan-50);
  border-radius: 8px;
  color: var(--color-primary-500);
  display: inline-block;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  margin: 0;
  padding: 4px 8px;
}

.question-card h1 {
  color: var(--color-text-strong);
  font-size: 23px;
  font-weight: 800;
  letter-spacing: -0.01em;
  line-height: 1.24;
  margin: 14px 0 0;
  max-width: 390px;
}

.question-card__footer {
  align-items: center;
  border-top: 1px solid var(--color-border-soft);
  display: flex;
  justify-content: space-between;
  margin-top: 14px;
  padding-top: 10px;
}

.question-card__footer span {
  color: var(--color-text-muted);
  font-size: 12px;
}

.question-card__hint {
  background: var(--color-cyan-50);
  border: 1px solid var(--color-cyan-100);
  border-radius: 999px;
  color: var(--color-primary-500);
  font-size: 11px;
  font-weight: 700;
  padding: 4px 8px;
}

.answer-zone {
  align-items: center;
  display: grid;
  gap: 10px;
  grid-template-columns: minmax(0, 1fr) auto;
  margin: 0 auto;
  max-width: 760px;
  padding: 0 0 18px;
}

.answer-input {
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  color: var(--color-text-muted);
  display: flex;
  gap: 8px;
  height: 42px;
  padding: 0 12px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}

.answer-input--ready {
  border-color: color-mix(in srgb, var(--color-primary-500) 32%, var(--color-border) 68%);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary-100) 55%, transparent);
}

.answer-input--submitting {
  opacity: 0.78;
}

.answer-input input {
  background: transparent;
  border: 0;
  color: var(--color-text-slate);
  flex: 1;
  font-size: 14px;
  outline: 0;
}

.cast-btn {
  background: linear-gradient(90deg, var(--color-primary-600), var(--color-primary-500));
  border: 0;
  border-radius: 12px;
  color: var(--color-surface);
  cursor: pointer;
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 700;
  height: 42px;
  min-width: 154px;
  padding: 0 16px;
  transition: filter 0.2s ease, transform 0.2s ease, opacity 0.2s ease;
}

.cast-btn--ready {
  filter: saturate(1.08);
}

.cast-btn--submitting {
  transform: scale(0.98);
}

.cast-btn:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.return-btn {
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
  grid-column: 1 / -1;
  justify-self: end;
  letter-spacing: 0.03em;
  padding: 0;
}

.feedback-action {
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 11px;
  margin-top: 12px;
  opacity: 0.7;
  padding: 0;
  text-decoration: underline;
}

.feedback-action:hover {
  opacity: 1;
}

.run-status-notice {
  background: var(--color-focus-amber-bg);
  border: 1px solid color-mix(in srgb, var(--color-focus-amber-bg) 78%, var(--color-muted-gold) 22%);
  border-radius: 8px;
  color: var(--color-focus-amber-text);
  font-size: 12px;
  font-weight: 700;
  margin-top: 12px;
  padding: 8px 12px;
  text-align: center;
}

.run-status-notice--danger {
  background: var(--color-danger-surface);
  border-color: var(--color-danger-border);
  color: var(--color-danger-title);
}

.answer-feedback {
  background: var(--color-danger-surface);
  border: 1px solid var(--color-danger-border);
  border-radius: 12px;
  margin-top: 12px;
  padding: 14px;
  text-align: left;
}

.answer-feedback--wrong {
  background: var(--color-danger-surface);
  border-color: var(--color-danger-border);
}

.answer-feedback__header {
  align-items: center;
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.answer-feedback__icon {
  align-items: center;
  background: var(--color-danger-title);
  border-radius: 50%;
  color: var(--color-surface);
  display: inline-flex;
  font-size: 14px;
  height: 24px;
  justify-content: center;
  width: 24px;
}

.answer-feedback__title {
  color: var(--color-danger-title);
  font-size: 14px;
  font-weight: 700;
}

.answer-feedback__correct {
  color: var(--color-danger-title);
  font-size: 13px;
  margin-bottom: 8px;
}

.answer-feedback__explanation {
  color: var(--color-danger-title);
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 900px) {
  .abyss-page {
    padding: 12px;
  }

  .abyss-status {
    grid-template-columns: 1fr;
  }

  .battle-stage {
    min-height: 460px;
  }

  .question-card {
    bottom: 42px;
    left: 12px;
    padding: 12px;
    width: calc(100% - 24px);
  }

  .dragon-art {
    background-position: center, 62% 8%;
    background-size: cover, 144% auto;
  }

  .question-card h1 {
    font-size: 19px;
    max-width: none;
  }

  .answer-zone {
    grid-template-columns: 1fr;
    padding: 0 12px 14px;
  }

  .cast-btn,
  .return-btn {
    width: 100%;
  }
}

.revive-overlay {
  align-items: center;
  background: color-mix(in srgb, var(--color-text-primary) 55%, transparent);
  display: flex;
  inset: 0;
  justify-content: center;
  padding: 24px;
  position: fixed;
  z-index: 50;
}

.revive-modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  box-shadow: var(--shadow-elevated);
  max-width: 420px;
  padding: 24px;
  width: 100%;
}

.revive-modal__eyebrow {
  color: var(--color-primary-500);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 0 0 8px;
}

.revive-modal h2 {
  margin: 0 0 12px;
}

.revive-modal p {
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.revive-modal__actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.revive-modal__buff {
  color: var(--color-primary-500);
  font-weight: 700;
}

.revive-modal__error {
  color: var(--color-trend-down);
  font-weight: 700;
}

</style>


