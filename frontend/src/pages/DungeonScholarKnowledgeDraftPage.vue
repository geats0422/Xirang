<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import GameSettlementModal from "../components/GameSettlementModal.vue";

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

const progressCurrent = ref(3);
const progressTotal = ref(10);

const _wordChips = [
  { label: "Water", tone: "water" },
  { label: "Tao", tone: "tao" },
  { label: "Heart", tone: "heart" },
  { label: "Mountain", tone: "mountain" },
  { label: "Heaven", tone: "heaven" },
] as const;

const progressWidth = computed(() => `${(progressCurrent.value / progressTotal.value) * 100}%`);
const backNavigating = ref(false);
const filledSlots = ref<Array<string | null>>([null, null, null]);
const showSettlement = ref(false);

const showNotice = ref(false);

const goBack = async () => {
  await router.push({
    path: "/library/game-modes",
    query: route.query,
  });
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

const _onChipSelect = (label: string) => {
  if (showSettlement.value) {
    return;
  }

  const emptyIndex = filledSlots.value.findIndex((slot) => slot === null);

  if (emptyIndex === -1) {
    return;
  }

  filledSlots.value[emptyIndex] = label;

  if (filledSlots.value.every((slot) => slot !== null)) {
    showSettlement.value = true;
  }
};

const closeSettlement = () => {
  showSettlement.value = false;
};

const setShowNotice = () => {
  showNotice.value = true;
};

defineExpose({
  setShowNotice,
});
</script>

<template>
  <main class="draft-page">
    <section class="draft-shell" aria-label="Knowledge Draft gameplay">
      <header class="draft-topbar">
        <div class="draft-title">
          <button
            class="draft-title__back"
            :class="{ 'draft-title__back--navigating': backNavigating }"
            type="button"
            aria-label="Go back"
            @click="goPreviousPage"
          >
            ←
          </button>
          <h1>Knowledge Draft</h1>
        </div>

        <div class="draft-progress">
          <div class="draft-progress__meta">
            <span>PROGRESS</span>
            <span>{{ progressCurrent }}/{{ progressTotal }}</span>
          </div>
          <div class="draft-progress__track" role="presentation">
            <span class="draft-progress__fill" :style="{ width: progressWidth }" />
          </div>
        </div>

        <div class="draft-actions">
          <span class="draft-reward">🪙 +50</span>
          <button class="draft-settings" type="button" aria-label="Settings">⚙</button>
        </div>
      </header>

      <section class="draft-stage">
        <div class="draft-stage__mountains" aria-hidden="true" />
        <div class="draft-stage__branches" aria-hidden="true" />

        <article class="scroll-card" aria-label="Fill in the scroll">
          <div class="scroll-rod scroll-rod--top">
            <span class="scroll-cap scroll-cap--left" />
            <span class="scroll-cap scroll-cap--right" />
          </div>

          <div class="scroll-paper">
            <p class="scroll-paper__tag">ANCIENT PHILOSOPHY</p>
            <h2>The Flow of Nature</h2>
            <div class="scroll-paper__accent" />

            <p class="scroll-paper__body">
              To understand the Way, one must be like
              <span class="drop-slot">{{ filledSlots[0] ?? "drop here" }}</span>
              . It nourishes all things without striving. It flows to places men reject and so it is like the
              <span class="drop-slot">{{ filledSlots[1] ?? "drop here" }}</span>
              . In dwelling, be close to the land. In meditation, go deep in the
              <span class="drop-slot">{{ filledSlots[2] ?? "drop here" }}</span>
              .
            </p>

            <div class="scroll-watermark" aria-hidden="true">✎</div>
          </div>

          <div class="scroll-rod scroll-rod--bottom">
            <span class="scroll-cap scroll-cap--left" />
            <span class="scroll-cap scroll-cap--right" />
          </div>
        </article>

        <div class="draft-chip-help">↕ DRAG WORDS TO COMPLETE THE SCROLL</div>

        <button class="feedback-action" type="button">
          这题有误
        </button>

        <div v-if="showNotice" class="run-status-notice">
          ⚠ Answer quickly to avoid reduced XP/coins!
        </div>
      </section>
    </section>

    <GameSettlementModal
      :visible="showSettlement"
      mode-name="Knowledge Draft"
      :xp-gained="250"
      :coin-reward="50"
      goal-text="Keep filling the scroll to reach enlightenment through study."
      @close="closeSettlement"
      @confirm="goBack"
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

.drop-slot {
  border: 1px dashed color-mix(in srgb, var(--color-border) 60%, var(--color-badge-blue-bg) 40%);
  border-radius: 999px;
  color: var(--color-text-light-slate);
  display: inline-flex;
  font-family: inherit;
  font-size: 12px;
  justify-content: center;
  margin: 0 6px;
  min-width: 80px;
  padding: 6px 12px;
  transform: translateY(-2px);
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
