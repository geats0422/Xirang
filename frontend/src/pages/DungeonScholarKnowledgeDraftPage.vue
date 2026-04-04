<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import GameSettlementModal from "../components/GameSettlementModal.vue";
import { ROUTES } from "../constants/routes";
import { createRun, submitAnswer, type RunQuestion, type RunQuestionOption } from "../api/runs";
import { submitFeedback } from "../api/feedback";
import { getShopBalance } from "../api/shop";

type QuestionSegment =
  | {
      kind: "text";
      key: string;
      value: string;
    }
  | {
      kind: "blank";
      key: string;
      blankIndex: number;
    };

type DragPayload =
  | {
      kind: "option";
      optionId: string;
    }
  | {
      kind: "slot";
      slotIndex: number;
    };

const BLANK_PATTERN = /\[\[\s*blank\s*\]\]|\[\s*blank\s*\]|\{\{\s*blank\s*\}\}|<blank>|_{2,}/gi;
const DRAG_DATA_KEY = "application/x-xirang-draft-payload";

const { t, locale } = useI18n();

onMounted(() => {
  document.title = t("knowledgeDraft.metaTitle");
});

// Update document title reactively when locale changes
watch(locale, () => {
  document.title = t("knowledgeDraft.metaTitle");
});

const route = useRoute();
const router = useRouter();

const progressCurrent = ref(0);
const progressTotal = ref(1);
const coins = ref<number | null>(null);
const timeLeftSec = ref<number | null>(null);
const maxRunTime = ref<number | null>(null);

const runId = ref<string | null>(null);
const questions = ref<RunQuestion[]>([]);
const questionIndex = ref(0);
const questionStartAt = ref<number>(Date.now());
let tickerId: number | null = null;

const progressWidth = computed(() => `${(progressCurrent.value / progressTotal.value) * 100}%`);
const backNavigating = ref(false);
const showSettlement = ref(false);
const settlementXp = ref(0);
const settlementCoins = ref(0);
const settlementCombo = ref(0);
const settlementGoalCurrent = ref(0);
const settlementGoalTotal = ref(10);
const settlementTopPercent = ref<number | null>(null);

const showNotice = ref(false);

const currentQuestion = computed(() => questions.value[questionIndex.value] ?? null);
const materialTitle = computed(() => {
  const rawTitle = route.query.title;
  return typeof rawTitle === "string" && rawTitle.trim() ? rawTitle : t("knowledgeDraft.defaultMaterialTitle");
});

const questionText = computed(() => {
  if (currentQuestion.value?.text) {
    return currentQuestion.value.text;
  }
  return t("knowledgeDraft.loadingQuestion");
});

const questionSegments = computed<QuestionSegment[]>(() => {
  const text = questionText.value;
  const segments: QuestionSegment[] = [];
  let cursor = 0;
  let blankIndex = 0;

  for (const match of text.matchAll(BLANK_PATTERN)) {
    const start = match.index ?? 0;
    if (start > cursor) {
      segments.push({
        kind: "text",
        key: `text-${cursor}`,
        value: text.slice(cursor, start),
      });
    }

    segments.push({
      kind: "blank",
      key: `blank-${blankIndex}-${start}`,
      blankIndex,
    });
    blankIndex += 1;
    cursor = start + match[0].length;
  }

  if (blankIndex === 0) {
    return [
      {
        kind: "text",
        key: "text-full",
        value: text,
      },
    ];
  }

  if (cursor < text.length) {
    segments.push({
      kind: "text",
      key: `text-${cursor}`,
      value: text.slice(cursor),
    });
  }

  return segments;
});

const hasInlineBlanks = computed(() => questionSegments.value.some((segment) => segment.kind === "blank"));
const blankCount = computed(
  () => Math.max(1, questionSegments.value.filter((segment) => segment.kind === "blank").length),
);
const blankSelections = ref<(string | null)[]>([]);
const activeBlankIndex = ref(0);
const dragHoverBlankIndex = ref<number | null>(null);
const draggingOptionId = ref<string | null>(null);
const draggingSlotIndex = ref<number | null>(null);
const isSubmittingAnswer = ref(false);

const chipTones = ["water", "tao", "heart", "mountain", "heaven"] as const;

const optionChips = computed(() =>
  (currentQuestion.value?.options ?? []).map((option, index) => ({
    ...option,
    tone: chipTones[index % chipTones.length],
  })),
);

const optionTextMap = computed(() => {
  return new Map(optionChips.value.map((option) => [option.id, option.text]));
});

const selectedOptionIds = computed(() => {
  return new Set(blankSelections.value.filter((selection): selection is string => selection !== null));
});

const hasFilledAllBlanks = computed(() => {
  return blankSelections.value.length > 0 && blankSelections.value.every((selection) => selection !== null);
});

const timerLabel = computed(() => {
  if (timeLeftSec.value === null) {
    return "--";
  }
  return `${Math.max(0, timeLeftSec.value)}s`;
});

const resolveLeagueTopPercent = (accuracy: number | null | undefined): number | null => {
  if (typeof accuracy !== "number" || !Number.isFinite(accuracy)) {
    return null;
  }
  const normalized = Math.min(1, Math.max(0, accuracy));
  return Math.max(1, 100 - Math.round(normalized * 100));
};

const applyRunState = (state: Record<string, unknown> | null | undefined) => {
  if (!state) {
    return;
  }
  const nextTime = Number(state.time_left_sec);
  if (Number.isFinite(nextTime)) {
    timeLeftSec.value = nextTime;
  }
  if (timeLeftSec.value !== null && (maxRunTime.value === null || maxRunTime.value < timeLeftSec.value)) {
    maxRunTime.value = timeLeftSec.value;
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
    if (showSettlement.value || timeLeftSec.value === null || timeLeftSec.value <= 0) {
      return;
    }
    timeLeftSec.value = Math.max(0, timeLeftSec.value - 1);
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

const syncProgress = () => {
  progressTotal.value = Math.max(1, questions.value.length);
  progressCurrent.value = Math.min(progressTotal.value, questionIndex.value + 1);
};

const clearDragState = () => {
  dragHoverBlankIndex.value = null;
  draggingOptionId.value = null;
  draggingSlotIndex.value = null;
};

const resetBlankState = () => {
  blankSelections.value = Array.from({ length: blankCount.value }, () => null);
  activeBlankIndex.value = 0;
  clearDragState();
  isSubmittingAnswer.value = false;
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
    const created = await createRun(documentId, "draft", 8, pathId);
    runId.value = created.run_id;
    questions.value = created.questions;
    questionIndex.value = 0;
    syncProgress();
    applyRunState(created.run_state);
    questionStartAt.value = Date.now();
    startTicker();
  } catch {
    showNotice.value = true;
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

const goPreviousPage = async () => {
  backNavigating.value = true;

  if (window.history.length > 1) {
    router.back();
    window.setTimeout(() => {
      backNavigating.value = false;
    }, 220);
    return;
  }

  await goBack();

  window.setTimeout(() => {
    backNavigating.value = false;
  }, 220);
};

const resolveSelectedOptionText = (optionId: string | null) => {
  if (!optionId) {
    return "";
  }
  return optionTextMap.value.get(optionId) ?? "";
};

const setActiveBlank = (blankIndex: number) => {
  if (blankIndex < 0 || blankIndex >= blankSelections.value.length) {
    return;
  }
  activeBlankIndex.value = blankIndex;
};

const findPreferredBlankIndex = () => {
  const firstEmpty = blankSelections.value.findIndex((selection) => selection === null);
  if (firstEmpty !== -1) {
    return firstEmpty;
  }
  return Math.min(activeBlankIndex.value, blankSelections.value.length - 1);
};

const setBlankSelection = (optionId: string, targetIndex: number) => {
  if (targetIndex < 0 || targetIndex >= blankSelections.value.length) {
    return false;
  }

  const nextSelections = [...blankSelections.value];
  const sourceIndex = nextSelections.findIndex((selection) => selection === optionId);
  const targetValue = nextSelections[targetIndex];

  if (sourceIndex === targetIndex) {
    setActiveBlank(targetIndex);
    return false;
  }

  nextSelections[targetIndex] = optionId;

  if (sourceIndex !== -1) {
    nextSelections[sourceIndex] = targetValue && targetValue !== optionId ? targetValue : null;
  }

  blankSelections.value = nextSelections;
  const nextEmpty = nextSelections.findIndex((selection) => selection === null);
  activeBlankIndex.value = nextEmpty === -1 ? targetIndex : nextEmpty;
  return true;
};

const moveBlankSelection = (fromIndex: number, toIndex: number) => {
  if (
    fromIndex < 0 ||
    toIndex < 0 ||
    fromIndex >= blankSelections.value.length ||
    toIndex >= blankSelections.value.length ||
    fromIndex === toIndex
  ) {
    return false;
  }

  const nextSelections = [...blankSelections.value];
  const sourceValue = nextSelections[fromIndex];

  if (!sourceValue) {
    return false;
  }

  const targetValue = nextSelections[toIndex];
  nextSelections[toIndex] = sourceValue;
  nextSelections[fromIndex] = targetValue;

  blankSelections.value = nextSelections;
  const nextEmpty = nextSelections.findIndex((selection) => selection === null);
  activeBlankIndex.value = nextEmpty === -1 ? toIndex : nextEmpty;
  return true;
};

const readDragPayload = (event: DragEvent): DragPayload | null => {
  const transfer = event.dataTransfer;
  if (!transfer) {
    return null;
  }

  const rawPayload = transfer.getData(DRAG_DATA_KEY) || transfer.getData("text/plain");
  if (!rawPayload) {
    return null;
  }

  try {
    const payload = JSON.parse(rawPayload) as Partial<DragPayload>;
    if (payload.kind === "option" && typeof payload.optionId === "string") {
      return {
        kind: "option",
        optionId: payload.optionId,
      };
    }

    if (payload.kind === "slot" && typeof payload.slotIndex === "number") {
      return {
        kind: "slot",
        slotIndex: payload.slotIndex,
      };
    }
  } catch {
    return null;
  }

  return null;
};

const writeDragPayload = (event: DragEvent, payload: DragPayload) => {
  const transfer = event.dataTransfer;
  if (!transfer) {
    return;
  }

  const serialized = JSON.stringify(payload);
  transfer.effectAllowed = "move";
  transfer.setData(DRAG_DATA_KEY, serialized);
  transfer.setData("text/plain", serialized);
};

const maybeSubmitFilledAnswer = () => {
  if (!hasFilledAllBlanks.value) {
    return;
  }
  void submitFilledAnswer();
};

const submitFilledAnswer = async () => {
  if (
    showSettlement.value ||
    !runId.value ||
    !currentQuestion.value ||
    isSubmittingAnswer.value ||
    !hasFilledAllBlanks.value
  ) {
    return;
  }

  isSubmittingAnswer.value = true;

  const elapsedMs = Math.max(0, Date.now() - questionStartAt.value);
  const selectedOptionIds = blankSelections.value.filter(
    (selection): selection is string => selection !== null,
  );

  try {
    const result = await submitAnswer(
      runId.value,
      currentQuestion.value.id,
      selectedOptionIds,
      elapsedMs,
    );

    applyRunState(result.run.state);

    if (result.settlement) {
      settlementXp.value = result.settlement.xp_earned;
      settlementCoins.value = result.settlement.coins_earned;
      settlementCombo.value = result.settlement.combo_max;
      settlementGoalCurrent.value = result.settlement.goal_current ?? 0;
      settlementGoalTotal.value = result.settlement.goal_total ?? 10;
      settlementTopPercent.value = resolveLeagueTopPercent(result.settlement.accuracy);
      showSettlement.value = true;
      stopTicker();
      await refreshBalance();
      return;
    }

    if (!result.is_correct) {
      showNotice.value = true;
      return;
    }

    showNotice.value = false;

    questionIndex.value = Math.min(questionIndex.value + 1, questions.value.length - 1);
    syncProgress();
    questionStartAt.value = Date.now();
  } catch {
    showNotice.value = true;
  } finally {
    isSubmittingAnswer.value = false;
  }
};

const chooseOption = (option: RunQuestionOption) => {
  if (showSettlement.value || isSubmittingAnswer.value || blankSelections.value.length === 0) {
    return;
  }

  const preferredIndex = findPreferredBlankIndex();
  const changed = setBlankSelection(option.id, preferredIndex);
  if (!changed) {
    return;
  }

  maybeSubmitFilledAnswer();
};

const onOptionDragStart = (optionId: string, event: DragEvent) => {
  if (isSubmittingAnswer.value) {
    event.preventDefault();
    return;
  }

  draggingOptionId.value = optionId;
  draggingSlotIndex.value = null;
  writeDragPayload(event, {
    kind: "option",
    optionId,
  });
};

const onBlankDragStart = (blankIndex: number, event: DragEvent) => {
  const selectedOptionId = blankSelections.value[blankIndex];
  if (isSubmittingAnswer.value || !selectedOptionId) {
    event.preventDefault();
    return;
  }

  draggingSlotIndex.value = blankIndex;
  draggingOptionId.value = selectedOptionId;
  writeDragPayload(event, {
    kind: "slot",
    slotIndex: blankIndex,
  });
};

const onBlankDragOver = (blankIndex: number, event: DragEvent) => {
  if (isSubmittingAnswer.value || showSettlement.value) {
    return;
  }

  event.preventDefault();
  dragHoverBlankIndex.value = blankIndex;

  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = "move";
  }
};

const onBlankDragLeave = (blankIndex: number) => {
  if (dragHoverBlankIndex.value === blankIndex) {
    dragHoverBlankIndex.value = null;
  }
};

const onBlankDrop = (blankIndex: number, event: DragEvent) => {
  if (isSubmittingAnswer.value || showSettlement.value) {
    return;
  }

  event.preventDefault();
  dragHoverBlankIndex.value = null;

  const payload = readDragPayload(event);
  if (!payload) {
    clearDragState();
    return;
  }

  const changed =
    payload.kind === "option"
      ? setBlankSelection(payload.optionId, blankIndex)
      : moveBlankSelection(payload.slotIndex, blankIndex);

  clearDragState();
  if (changed) {
    maybeSubmitFilledAnswer();
  }
};

const onDragEnd = () => {
  clearDragState();
};

const closeSettlement = () => {
  showSettlement.value = false;
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
const setShowNotice = () => {
  showNotice.value = true;
};

defineExpose({
  setShowNotice,
});

onMounted(async () => {
  await bootstrapRun();
});

watch(currentQuestion, () => {
  showNotice.value = false;
  resetBlankState();
}, { immediate: true });

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
  <main class="draft-page">
    <section class="draft-shell" :aria-label="t('knowledgeDraft.shellAria')">
      <header class="draft-topbar">
        <div class="draft-title">
          <button
            class="draft-title__back"
            :class="{ 'draft-title__back--navigating': backNavigating }"
            type="button"
            :aria-label="t('knowledgeDraft.goBackAria')"
            @click="goPreviousPage"
          >
            ←
          </button>
          <h1>{{ t("knowledgeDraft.title") }}</h1>
        </div>

        <div class="draft-progress">
          <div class="draft-progress__meta">
            <span>{{ t("knowledgeDraft.progress") }}</span>
            <span>{{ progressCurrent }}/{{ progressTotal }}</span>
          </div>
          <div class="draft-progress__track" role="presentation">
            <span class="draft-progress__fill" :style="{ width: progressWidth }" />
          </div>
        </div>

        <div class="draft-actions">
          <span class="draft-reward">🪙 {{ coins ?? "--" }}</span>
          <span class="draft-timer">🕒 {{ timerLabel }}</span>
          <button class="draft-settings" type="button" :aria-label="t('knowledgeDraft.settingsAria')">⚙</button>
        </div>
      </header>

      <section class="draft-stage">
        <div class="draft-stage__mountains" aria-hidden="true" />
        <div class="draft-stage__branches" aria-hidden="true" />

        <article class="scroll-card" :aria-label="t('knowledgeDraft.scrollAria')">
          <div class="scroll-rod scroll-rod--top">
            <span class="scroll-cap scroll-cap--left" />
            <span class="scroll-cap scroll-cap--right" />
          </div>

          <div class="scroll-paper">
            <p class="scroll-paper__tag">{{ t("knowledgeDraft.questionCardTag") }}</p>
            <h2>{{ materialTitle }}</h2>
            <div class="scroll-paper__accent" />

            <p class="scroll-paper__body">
              <template v-for="segment in questionSegments" :key="segment.key">
                <span v-if="segment.kind === 'text'">{{ segment.value }}</span>
                <button
                  v-else
                  class="drop-slot"
                  :class="{
                    'drop-slot--active': activeBlankIndex === segment.blankIndex,
                    'drop-slot--filled': Boolean(blankSelections[segment.blankIndex]),
                    'drop-slot--dragover': dragHoverBlankIndex === segment.blankIndex,
                  }"
                  type="button"
                  :aria-label="t('knowledgeDraft.blankAria', { index: segment.blankIndex + 1 })"
                  :draggable="Boolean(blankSelections[segment.blankIndex])"
                  @click="setActiveBlank(segment.blankIndex)"
                  @dragstart="onBlankDragStart(segment.blankIndex, $event)"
                  @dragend="onDragEnd"
                  @dragover="onBlankDragOver(segment.blankIndex, $event)"
                  @dragleave="onBlankDragLeave(segment.blankIndex)"
                  @drop="onBlankDrop(segment.blankIndex, $event)"
                >
                  <span v-if="blankSelections[segment.blankIndex]" class="drop-slot__text">
                    {{ resolveSelectedOptionText(blankSelections[segment.blankIndex]) }}
                  </span>
                  <span v-else class="drop-slot__placeholder">____</span>
                </button>
              </template>
            </p>

            <div v-if="!hasInlineBlanks" class="scroll-paper__slot-row">
              <button
                v-for="(_, blankIndex) in blankSelections"
                :key="`fallback-slot-${blankIndex}`"
                class="drop-slot"
                :class="{
                  'drop-slot--active': activeBlankIndex === blankIndex,
                  'drop-slot--filled': Boolean(blankSelections[blankIndex]),
                  'drop-slot--dragover': dragHoverBlankIndex === blankIndex,
                }"
                type="button"
                :aria-label="t('knowledgeDraft.blankAria', { index: blankIndex + 1 })"
                :draggable="Boolean(blankSelections[blankIndex])"
                @click="setActiveBlank(blankIndex)"
                @dragstart="onBlankDragStart(blankIndex, $event)"
                @dragend="onDragEnd"
                @dragover="onBlankDragOver(blankIndex, $event)"
                @dragleave="onBlankDragLeave(blankIndex)"
                @drop="onBlankDrop(blankIndex, $event)"
              >
                <span v-if="blankSelections[blankIndex]" class="drop-slot__text">
                  {{ resolveSelectedOptionText(blankSelections[blankIndex]) }}
                </span>
                <span v-else class="drop-slot__placeholder">____</span>
              </button>
            </div>

            <div class="scroll-watermark" aria-hidden="true">✎</div>
          </div>

          <div class="scroll-rod scroll-rod--bottom">
            <span class="scroll-cap scroll-cap--left" />
            <span class="scroll-cap scroll-cap--right" />
          </div>
        </article>

        <div class="draft-chip-help">{{ t("knowledgeDraft.dragHint") }}</div>

        <div class="draft-chip-row">
          <button
            v-for="chip in optionChips"
            :key="chip.id"
            class="draft-chip"
            :class="[
              `draft-chip--${chip.tone}`,
              {
                'draft-chip--selected': selectedOptionIds.has(chip.id),
                'draft-chip--dragging': draggingOptionId === chip.id,
              },
            ]"
            type="button"
            :aria-pressed="selectedOptionIds.has(chip.id)"
            :disabled="isSubmittingAnswer"
            :draggable="!isSubmittingAnswer"
            @dragstart="onOptionDragStart(chip.id, $event)"
            @dragend="onDragEnd"
            @click="chooseOption(chip)"
          >
            {{ chip.text }}
          </button>
        </div>

        <button class="feedback-action" type="button" @click="handleFeedback">
          {{ t("common.reportQuestionIssue") }}
        </button>

        <div v-if="showNotice" class="run-status-notice">
          {{ t("knowledgeDraft.notice") }}
        </div>
      </section>
    </section>

    <GameSettlementModal
      :visible="showSettlement"
      :mode-name="t('knowledgeDraft.settlementModeName')"
      :xp-gained="settlementXp"
      :coin-reward="settlementCoins"
      :combo-count="settlementCombo"
      :goal-current="settlementGoalCurrent"
      :goal-total="settlementGoalTotal"
      :league-top-percent="settlementTopPercent"
      :goal-text="t('knowledgeDraft.settlementGoal')"
      @close="closeSettlement"
      @confirm="goLibrary"
    />
  </main>
</template>

<style scoped>
.draft-page {
  background: linear-gradient(180deg, var(--color-page-gradient-start), var(--color-page-gradient-end));
  min-height: 100vh;
  padding: 28px;
}

.draft-shell {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  margin: 0 auto;
  max-width: 1040px;
  min-height: 640px;
  overflow: hidden;
}

.draft-topbar {
  align-items: center;
  border-bottom: 1px solid var(--color-border-soft);
  display: grid;
  gap: 16px;
  grid-template-columns: auto minmax(0, 1fr) auto;
  padding: 10px 18px;
}

.draft-title {
  align-items: center;
  display: flex;
  gap: 12px;
}

.draft-title__back {
  align-items: center;
  background: transparent;
  border: 0;
  color: var(--color-primary-500);
  cursor: pointer;
  display: inline-flex;
  font-size: 18px;
  font-weight: 700;
  justify-content: center;
  line-height: 1;
  padding: 0;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.draft-title__back:hover {
  transform: translateX(-2px);
}

.draft-title__back--navigating {
  opacity: 0.65;
  transform: scale(0.92);
}

.draft-title h1 {
  color: var(--color-text-strong);
  font-family: var(--font-serif);
  font-size: 28px;
  margin: 0;
}

.draft-progress {
  justify-self: center;
  width: min(100%, 330px);
}

.draft-progress__meta {
  color: var(--color-text-muted);
  display: flex;
  font-size: 10px;
  font-weight: 800;
  justify-content: space-between;
  letter-spacing: 0.08em;
}

.draft-progress__track {
  background: var(--color-progress-track);
  border-radius: 999px;
  height: 6px;
  margin-top: 6px;
  overflow: hidden;
}

.draft-progress__fill {
  background: var(--color-primary-500);
  display: block;
  height: 100%;
}

.draft-actions {
  align-items: center;
  display: flex;
  gap: 12px;
}

.draft-reward {
  align-items: center;
  background: var(--color-streak-bg);
  border: 1px solid color-mix(in srgb, var(--color-streak-bg) 72%, var(--color-muted-gold) 28%);
  border-radius: 999px;
  color: var(--color-coin-value);
  display: inline-flex;
  font-size: 12px;
  font-weight: 800;
  height: 28px;
  padding: 0 10px;
}

.draft-timer {
  align-items: center;
  background: var(--color-streak-bg);
  border: 1px solid color-mix(in srgb, var(--color-streak-bg) 72%, var(--color-muted-gold) 28%);
  border-radius: 999px;
  color: var(--color-soft-brown);
  display: inline-flex;
  font-size: 12px;
  font-weight: 800;
  height: 28px;
  padding: 0 10px;
}

.draft-settings {
  align-items: center;
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  color: var(--color-text-muted);
  cursor: pointer;
  display: inline-flex;
  height: 28px;
  justify-content: center;
  width: 28px;
}

.draft-stage {
  min-height: 590px;
  padding: 36px 34px 30px;
  position: relative;
}

.draft-stage__mountains,
.draft-stage__branches {
  position: absolute;
}

.draft-stage__mountains {
  background: radial-gradient(
      circle at 40% 50%,
      color-mix(in srgb, var(--color-text-muted) 26%, transparent),
      transparent 36%
    ),
    linear-gradient(
      135deg,
      color-mix(in srgb, var(--color-text-muted) 24%, transparent),
      color-mix(in srgb, var(--color-border-soft) 0%, transparent)
    );
  clip-path: polygon(5% 88%, 18% 58%, 29% 72%, 40% 42%, 56% 70%, 66% 54%, 78% 76%, 100% 88%, 100% 100%, 0 100%);
  height: 170px;
  left: 20px;
  opacity: 0.8;
  top: 142px;
  width: 160px;
}

.draft-stage__branches {
  background: radial-gradient(
      circle at 75% 20%,
      color-mix(in srgb, var(--color-text-muted) 32%, transparent),
      transparent 12%
    ),
    radial-gradient(
      circle at 66% 34%,
      color-mix(in srgb, var(--color-text-muted) 30%, transparent),
      transparent 12%
    ),
    radial-gradient(
      circle at 54% 50%,
      color-mix(in srgb, var(--color-text-muted) 28%, transparent),
      transparent 11%
    ),
    radial-gradient(
      circle at 42% 66%,
      color-mix(in srgb, var(--color-text-muted) 26%, transparent),
      transparent 11%
    ),
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--color-text-muted) 36%, transparent),
      color-mix(in srgb, var(--color-text-muted) 0%, transparent)
    );
  border-radius: 140px 140px 0 0;
  bottom: 64px;
  height: 164px;
  opacity: 0.6;
  right: 34px;
  width: 152px;
}

.scroll-card {
  margin: 0 auto;
  max-width: 544px;
  position: relative;
}

.scroll-rod {
  background: color-mix(in srgb, var(--color-soft-brown) 44%, var(--color-surface-alt) 56%);
  border-radius: 2px;
  height: 16px;
  position: relative;
}

.scroll-cap {
  background: var(--color-soft-brown);
  border-radius: 3px;
  height: 22px;
  position: absolute;
  top: -3px;
  width: 18px;
}

.scroll-cap::before {
  background: color-mix(in srgb, var(--color-text-primary) 35%, transparent);
  border-radius: 999px;
  content: "";
  height: 10px;
  left: 7px;
  position: absolute;
  top: 6px;
  width: 4px;
}

.scroll-cap--left {
  left: 12px;
}

.scroll-cap--right {
  right: 12px;
}

.scroll-paper {
  background: var(--color-surface-alt);
  box-shadow: var(--shadow-elevated);
  margin: 0 18px;
  min-height: 284px;
  padding: 36px 44px 40px;
  position: relative;
}

.scroll-paper__tag {
  background: var(--color-primary-50);
  border-radius: 999px;
  color: var(--color-primary-600);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 0 auto;
  padding: 6px 12px;
  width: fit-content;
}

.scroll-paper h2 {
  color: var(--color-text-strong);
  font-family: var(--font-serif);
  font-size: 30px;
  margin: 18px 0 0;
  text-align: center;
}

.scroll-paper__accent {
  background: var(--color-primary-500);
  border-radius: 999px;
  height: 4px;
  margin: 14px auto 0;
  width: 62px;
}

.scroll-paper__body {
  color: var(--color-text-secondary);
  font-family: var(--font-serif);
  font-size: 18px;
  line-height: 1.55;
  margin: 28px 0 0;
  text-align: left;
}

.scroll-paper__slot-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.drop-slot {
  align-items: center;
  background: var(--color-surface);
  border: 1px dashed color-mix(in srgb, var(--color-border) 60%, var(--color-badge-blue-bg) 40%);
  border-radius: 999px;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: inline-flex;
  font-weight: 700;
  font-family: inherit;
  font-size: 13px;
  justify-content: center;
  margin: 0 4px;
  min-width: 92px;
  padding: 6px 12px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease, transform 0.2s ease;
  transform: translateY(-2px);
}

.drop-slot--active {
  border-color: color-mix(in srgb, var(--color-primary-500) 45%, var(--color-border) 55%);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary-100) 70%, transparent);
}

.drop-slot--filled {
  background: color-mix(in srgb, var(--color-primary-50) 70%, var(--color-surface) 30%);
  border-style: solid;
  color: var(--color-primary-700);
}

.drop-slot--dragover {
  transform: translateY(-3px) scale(1.03);
}

.drop-slot__text {
  animation: slot-fill-pop 0.18s ease;
}

.drop-slot__placeholder {
  color: var(--color-text-muted);
  font-weight: 600;
}

.scroll-watermark {
  bottom: 24px;
  color: color-mix(in srgb, var(--color-text-muted) 38%, transparent);
  font-size: 60px;
  position: absolute;
  right: 26px;
}

.draft-chip-help {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  margin-top: 34px;
  text-align: center;
}

.draft-chip-row {
  display: flex;
  gap: 14px;
  justify-content: center;
  margin-top: 16px;
}

.draft-chip {
  border: 0;
  border-radius: 16px;
  box-shadow: var(--shadow-card);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 700;
  min-width: 98px;
  padding: 12px 20px;
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}

.draft-chip:hover {
  transform: translateY(-1px);
}

.draft-chip:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.draft-chip--water {
  background: var(--color-cyan-50);
}

.draft-chip--tao {
  background: var(--color-primary-50);
}

.draft-chip--heart {
  background: var(--color-streak-bg);
}

.draft-chip--mountain {
  background: var(--color-chip-violet-bg);
}

.draft-chip--heaven {
  background: var(--color-chip-amber-bg);
}

.draft-chip--selected {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary-500) 44%, transparent), var(--shadow-card);
  color: var(--color-primary-700);
}

.draft-chip--dragging {
  filter: saturate(1.1);
  opacity: 0.8;
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
  background: var(--color-primary-50);
  border: 1px solid var(--color-primary-100);
  border-radius: 8px;
  color: var(--color-primary-600);
  font-size: 12px;
  font-weight: 700;
  margin-top: 12px;
  padding: 8px 12px;
  text-align: center;
}

@keyframes slot-fill-pop {
  0% {
    opacity: 0;
    transform: scale(0.94);
  }

  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 900px) {
  .draft-page {
    padding: 12px;
  }

  .draft-topbar {
    grid-template-columns: 1fr;
  }

  .draft-progress {
    justify-self: stretch;
    width: 100%;
  }

  .draft-actions {
    justify-content: flex-end;
  }

  .draft-stage {
    padding: 18px 12px 24px;
  }

  .scroll-paper {
    margin: 0 8px;
    padding: 24px 20px 28px;
  }

  .scroll-paper h2 {
    font-size: 26px;
  }

  .scroll-paper__body {
    font-size: 16px;
  }

  .draft-chip-row {
    flex-wrap: wrap;
  }
}
</style>
