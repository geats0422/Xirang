<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import GameSettlementModal from "../components/GameSettlementModal.vue";
import { ROUTES } from "../constants/routes";
import { createRun, submitAnswer, type RunQuestion } from '../api/runs';
import { submitFeedback } from '../api/feedback';
import { getShopBalance } from "../api/shop";

const { t, locale } = useI18n();

onMounted(() => {
  document.title = t("speedSurvival.metaTitle");
});

// Update document title reactively when locale changes
watch(locale, () => {
  document.title = t("speedSurvival.metaTitle");
});

type RunStatus = "normal" | "fast-answer" | "reduced-reward";

const route = useRoute();
const router = useRouter();

const timeRemaining = ref<number | null>(null);
const combo = ref<number | null>(null);
const coins = ref<number | null>(null);
const maxRunTime = ref<number | null>(null);
const runId = ref<string | null>(null);
const questions = ref<RunQuestion[]>([]);
const questionIndex = ref(0);
const questionStartAt = ref<number>(Date.now());
let tickerId: number | null = null;

const showSettlement = ref(false);
const runStatus = ref<RunStatus>("normal");
const settlementXp = ref(0);
const settlementCoins = ref(0);
const settlementCombo = ref(0);
const settlementGoalCurrent = ref(0);
const settlementGoalTotal = ref(8);


const currentQuestion = computed(() => questions.value[questionIndex.value] ?? null);

const questionText = computed(() => {
  if (currentQuestion.value?.text) {
    return currentQuestion.value.text;
  }
  return "Loading question...";
});

const progressPercent = computed(() => {
  if (maxRunTime.value === null || timeRemaining.value === null || maxRunTime.value <= 0) {
    return 0;
  }
  return Math.max(0, Math.min(100, (timeRemaining.value / maxRunTime.value) * 100));
});

const answerPrompt = computed(() => {
  if (!currentQuestion.value) {
    return "Loading options...";
  }
  return currentQuestion.value.options.length === 2
    ? "Choose the best option"
    : "Tap the option that matches the statement";
});

const falseOptionLabel = computed(() => currentQuestion.value?.options[0]?.text || "--");
const trueOptionLabel = computed(() => currentQuestion.value?.options[1]?.text || "--");

const applyRunState = (state: Record<string, unknown> | null | undefined) => {
  if (!state) {
    return;
  }
  const nextTime = Number(state.time_left_sec);
  const nextCombo = Number(state.combo_count);

  if (Number.isFinite(nextTime)) {
    timeRemaining.value = nextTime;
  }

  if (Number.isFinite(nextCombo)) {
    combo.value = nextCombo;
  }

  if (timeRemaining.value !== null && (maxRunTime.value === null || maxRunTime.value < timeRemaining.value)) {
    maxRunTime.value = timeRemaining.value;
  }
};

const stopTicker = () => {
  if (tickerId !== null) {
    window.clearInterval(tickerId);
    tickerId = null;
  }
};

const startTicker = () => {
  stopTicker();
  tickerId = window.setInterval(() => {
    if (showSettlement.value || timeRemaining.value === null || timeRemaining.value <= 0) {
      return;
    }
    timeRemaining.value = Math.max(0, timeRemaining.value - 1);
  }, 1000);
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
  if (!documentId) {
    return;
  }

  try {
    const created = await createRun(documentId, "speed", 8, pathId);
    runId.value = created.run_id;
    questions.value = created.questions;
    questionIndex.value = 0;
    combo.value = 0;
    applyRunState(created.run_state);
    questionStartAt.value = Date.now();
    startTicker();
  } catch {
    runStatus.value = "reduced-reward";
  }
};

const goBack = async () => {
  await router.push({
    path: route.query.documentId ? ROUTES.levelPath : ROUTES.gameModes,
    query: route.query,
  });
};

const goLibrary = async () => {
  await router.push(ROUTES.library);
};

const chooseAnswer = async (answer: "false" | "true") => {
  if (showSettlement.value || !runId.value || !currentQuestion.value) {
    return;
  }

  const selectedOption = answer === "false"
    ? currentQuestion.value.options[0]
    : currentQuestion.value.options[1] || currentQuestion.value.options[0];
  const elapsedMs = Math.max(0, Date.now() - questionStartAt.value);

  try {
    const result = await submitAnswer(
      runId.value,
      currentQuestion.value.id,
      selectedOption ? [selectedOption.id] : [],
      elapsedMs,
    );
    applyRunState(result.run.state);

    if (result.is_correct) {
      combo.value = (combo.value ?? 0) + 1;
      runStatus.value = elapsedMs <= 1500 ? "fast-answer" : "normal";
    } else {
      combo.value = 0;
      runStatus.value = "normal";
    }

    if (result.settlement) {
      settlementXp.value = result.settlement.xp_earned;
      settlementCoins.value = result.settlement.coins_earned;
      settlementCombo.value = result.settlement.combo_max;
      settlementGoalCurrent.value = result.settlement.goal_current ?? 0;
      settlementGoalTotal.value = result.settlement.goal_total ?? 8;
      showSettlement.value = true;
      stopTicker();
      await refreshBalance();
    } else {
      questionIndex.value = Math.min(questionIndex.value + 1, questions.value.length - 1);
      questionStartAt.value = Date.now();
    }
  } catch {
    runStatus.value = "reduced-reward";
  }
};

const closeSettlement = () => {
  showSettlement.value = false;
};

const toggleFeedbackForm = async () => {
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

const setFastAnswer = () => {
  runStatus.value = "fast-answer";
};

defineExpose({
  setFastAnswer,
});

onMounted(async () => {
  await bootstrapRun();
});

watch(showSettlement, (visible) => {
  if (visible) {
    stopTicker();
  }
});

onUnmounted(() => {
  stopTicker();
});
</script>

<template>
  <main class="speed-page">
    <section class="speed-shell" aria-label="Speed Survival gameplay">
      <header class="speed-topbar">
        <div class="speed-topbar__title">
          <span class="speed-topbar__icon">⚡</span>
          <h1>Speed Survival</h1>
        </div>

        <div class="speed-topbar__actions">
          <button class="coin-badge" type="button">🪙 {{ coins ?? "--" }}</button>
          <button class="exit-btn" type="button" @click="goBack">Exit Game</button>
          <button class="settings-btn" type="button" aria-label="Settings">⚙</button>
        </div>
      </header>

      <section class="speed-stage">
        <header class="countdown-strip">
          <div class="countdown-strip__meta">
            <p>TIME REMAINING</p>
            <span>{{ timeRemaining === null ? "--" : `${timeRemaining}s` }}</span>
          </div>

          <div class="countdown-strip__bar" role="presentation">
            <span class="countdown-strip__fill" :style="{ width: `${progressPercent}%` }" />
          </div>

          <div class="combo-badge">⚡ Combo x{{ combo ?? "--" }}</div>
        </header>

        <article class="survival-card" aria-label="True false card">
          <div class="survival-card__art" aria-hidden="true">
            <div class="survival-card__glow" />
          </div>

          <div class="survival-card__body">
            <p class="survival-card__eyebrow">✦ MYTHOLOGY</p>
            <h2>{{ questionText }}</h2>
            <p class="survival-card__prompt">{{ answerPrompt }}</p>
          </div>
        </article>

        <footer class="answer-pad">
          <button class="answer-pill answer-pill--false" type="button" @click="chooseAnswer('false')">
            <span class="answer-pill__icon">✕</span>
            <span class="answer-pill__label">{{ falseOptionLabel }}</span>
          </button>

          <button class="answer-pill answer-pill--true" type="button" @click="chooseAnswer('true')">
            <span class="answer-pill__icon">✓</span>
            <span class="answer-pill__label">{{ trueOptionLabel }}</span>
          </button>
        </footer>

        <p class="answer-tip">SWIPE OR USE ARROW KEYS</p>

        <button class="feedback-action" type="button" @click="toggleFeedbackForm">
          这题有误?
        </button>

        <div v-if="runStatus === 'fast-answer'" class="run-status-notice">
          ⚡ Fast answer! +50% XP bonus
        </div>
      </section>
    </section>

    <GameSettlementModal
      :visible="showSettlement"
      mode-name="Speed Survival"
      :xp-gained="settlementXp"
      :coin-reward="settlementCoins"
      :combo-count="settlementCombo"
      :goal-current="settlementGoalCurrent"
      :goal-total="settlementGoalTotal"
      goal-text="Keep sharpening your reflexes to reach enlightenment through speed." 
      @close="closeSettlement"
      @confirm="goLibrary"
    />
  </main>
</template>

<style scoped>
.speed-page {
  background: linear-gradient(180deg, var(--color-page-gradient-start), var(--color-page-gradient-end));
  min-height: 100vh;
  padding: 28px;
}

.speed-shell {
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  margin: 0 auto;
  max-width: 1040px;
  min-height: 640px;
  padding: 14px 18px 26px;
}

.speed-topbar {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.speed-topbar__title {
  align-items: center;
  display: flex;
  gap: 10px;
}

.speed-topbar__icon {
  align-items: center;
  background: var(--color-cyan-50);
  border: 1px solid var(--color-cyan-100);
  border-radius: 999px;
  color: var(--color-primary-500);
  display: inline-flex;
  height: 24px;
  justify-content: center;
  width: 24px;
}

.speed-topbar h1 {
  color: var(--color-text-primary);
  font-size: 20px;
  margin: 0;
}

.speed-topbar__actions {
  align-items: center;
  display: flex;
  gap: 10px;
}

.coin-badge {
  background: var(--color-streak-bg);
  border: 1px solid color-mix(in srgb, var(--color-streak-bg) 72%, var(--color-muted-gold) 28%);
  border-radius: 999px;
  color: var(--color-soft-brown);
  font-size: 12px;
  font-weight: 700;
  height: 30px;
  padding: 0 10px;
}

.exit-btn,
.settings-btn {
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  height: 30px;
  padding: 0 12px;
}

.settings-btn {
  padding: 0;
  width: 30px;
}

.speed-stage {
  margin: 108px auto 0;
  max-width: 660px;
}

.countdown-strip__meta {
  align-items: baseline;
  display: flex;
  justify-content: space-between;
}

.countdown-strip__meta p,
.countdown-strip__meta span {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 800;
  margin: 0;
}

.countdown-strip__meta span {
  color: var(--color-primary-500);
}

.countdown-strip__bar {
  background: var(--color-progress-track);
  border-radius: 999px;
  height: 6px;
  margin-top: 6px;
  overflow: hidden;
}

.countdown-strip__fill {
  background: linear-gradient(90deg, var(--color-primary-600), var(--color-primary-500));
  display: block;
  height: 100%;
}

.combo-badge {
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-100);
  border-radius: 12px;
  color: var(--color-primary-600);
  display: inline-flex;
  font-size: 12px;
  font-weight: 800;
  margin-left: auto;
  margin-top: 10px;
  padding: 6px 10px;
}

.survival-card {
  background: var(--color-surface);
  border-radius: 24px;
  box-shadow: var(--shadow-elevated);
  display: grid;
  grid-template-columns: 168px minmax(0, 1fr);
  margin-top: 18px;
  overflow: hidden;
}

.survival-card__art {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--color-streak-bg) 92%, var(--color-surface) 8%),
    color-mix(in srgb, var(--color-text-primary) 25%, transparent) 10%,
    color-mix(in srgb, var(--color-text-primary) 96%, transparent) 18%,
    color-mix(in srgb, var(--color-soft-brown) 64%, var(--color-text-primary) 36%) 50%,
    color-mix(in srgb, var(--color-text-primary) 94%, transparent) 82%,
    color-mix(in srgb, var(--color-streak-bg) 88%, var(--color-surface) 12%)
  );
  min-height: 194px;
  position: relative;
}

.survival-card__art::before,
.survival-card__art::after {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--color-streak-bg) 90%, var(--color-surface) 10%),
    color-mix(in srgb, var(--color-muted-gold) 20%, transparent)
  );
  content: "";
  height: 14px;
  left: 0;
  position: absolute;
  right: 0;
}

.survival-card__art::before {
  top: 8px;
}

.survival-card__art::after {
  bottom: 8px;
}

.survival-card__glow {
  background: radial-gradient(
    circle,
    color-mix(in srgb, var(--color-streak-bg) 96%, var(--color-surface) 4%) 0%,
    color-mix(in srgb, var(--color-muted-gold) 74%, transparent) 34%,
    color-mix(in srgb, var(--color-muted-gold) 24%, transparent) 68%,
    transparent 78%
  );
  border-radius: 999px;
  box-shadow: 0 0 20px color-mix(in srgb, var(--color-muted-gold) 78%, transparent),
    0 0 44px color-mix(in srgb, var(--color-streak-bg) 48%, transparent);
  height: 96px;
  left: 36px;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 96px;
}

.survival-card__glow::before,
.survival-card__glow::after {
  border: 1px solid color-mix(in srgb, var(--color-streak-bg) 60%, transparent);
  border-radius: 999px;
  content: "";
  inset: 10px;
  position: absolute;
}

.survival-card__glow::after {
  inset: 22px;
}

.survival-card__body {
  padding: 28px 28px 24px;
}

.survival-card__eyebrow {
  color: var(--color-primary-500);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  margin: 0;
}

.survival-card__body h2 {
  color: var(--color-text-primary);
  font-size: 24px;
  font-weight: 800;
  line-height: 1.15;
  margin: 14px 0 0;
  max-width: 328px;
}

.survival-card__prompt {
  color: var(--color-text-secondary);
  font-size: 13px;
  margin: 22px 0 0;
}

.answer-pad {
  display: flex;
  gap: 42px;
  justify-content: center;
  margin-top: 32px;
}

.answer-pill {
  align-items: center;
  background: transparent;
  border: 0;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  font-size: 13px;
  font-weight: 700;
  gap: 10px;
}

.answer-pill__icon {
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  display: inline-flex;
  font-size: 28px;
  height: 64px;
  justify-content: center;
  width: 64px;
}

.answer-pill--false .answer-pill__icon {
  color: var(--color-trend-down);
}

.answer-pill--true .answer-pill__icon {
  color: var(--color-primary-500);
}

.answer-tip {
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 18px 0 0;
  text-align: center;
}

.feedback-action {
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 11px;
  margin-top: 16px;
  opacity: 0.7;
  padding: 0;
  text-decoration: underline;
}

.feedback-action:hover {
  opacity: 1;
}

.run-status-notice {
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-100);
  border-radius: 8px;
  color: var(--color-primary-600);
  font-size: 12px;
  font-weight: 700;
  margin-top: 16px;
  padding: 8px 12px;
  text-align: center;
}

@media (max-width: 900px) {
  .speed-page {
    padding: 12px;
  }

  .speed-shell {
    min-height: auto;
    padding: 12px;
  }

  .speed-stage {
    margin-top: 42px;
  }

  .survival-card {
    grid-template-columns: 1fr;
  }

  .survival-card__art {
    min-height: 170px;
  }

  .survival-card__body {
    padding: 20px 16px;
  }

  .survival-card__body h2 {
    font-size: 22px;
    max-width: none;
  }

  .answer-pad {
    gap: 20px;
  }
}
</style>
