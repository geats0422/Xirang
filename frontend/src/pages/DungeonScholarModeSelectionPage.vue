<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

type ModeFlow = "begin" | "review";

type DungeonMode = {
  id: string;
  icon: string;
  iconClass: string;
  title: string;
  tag: string;
  description: string;
  previewClass: string;
};

onMounted(() => {
  document.title = "Xi Rang Mode Selection";
});
const libraryRoute = "/library";

const modeOptions: DungeonMode[] = [
  {
    id: "endless-abyss",
    icon: "♡",
    iconClass: "mode-card__icon--crimson",
    title: "Endless Abyss",
    tag: "ROGUELIKE STRATEGY",
    description: "Descend deeper with every correct answer. Manage your health and collect artifacts.",
    previewClass: "mode-card__preview--abyss",
  },
  {
    id: "speed-survival",
    icon: "⚡",
    iconClass: "mode-card__icon--sky",
    title: "Speed Survival",
    tag: "FAST-PACED SWIPE",
    description: "Race against the clock. Swipe left or right to answer. Precision meets speed.",
    previewClass: "mode-card__preview--speed",
  },
  {
    id: "knowledge-draft",
    icon: "◫",
    iconClass: "mode-card__icon--gold",
    title: "Knowledge Draft",
    tag: "TACTILE CARD PLAYING",
    description: "Build a deck of answers. Play cards to defeat enemies in turn-based combat.",
    previewClass: "mode-card__preview--draft",
  },
];

const router = useRouter();
const route = useRoute();
const selectedModeId = ref<string | null>(null);

const modeFlow = computed<ModeFlow>(() => (route.query.flow === "review" ? "review" : "begin"));

const materialTitle = computed(() => {
  const rawTitle = route.query.title;

  if (typeof rawTitle === "string" && rawTitle.trim()) {
    return rawTitle;
  }

  return modeFlow.value === "review" ? "Basic Alchemy 101" : "Modern Biology Vol 1";
});

const materialSubtitle = computed(() => {
  const rawSubtitle = route.query.subtitle;

  if (typeof rawSubtitle === "string" && rawSubtitle.trim()) {
    return rawSubtitle;
  }

  return modeFlow.value === "review"
    ? "Return through a new challenge loop to reinforce what you have already learned."
    : "Choose how this scroll should become your first combat-ready study session.";
});

const surfaceTitle = computed(() =>
  modeFlow.value === "review" ? "Digestion Complete!" : "Choose Your First Dungeon",
);

const surfaceSubtitlePrefix = computed(() =>
  modeFlow.value === "review" ? "Choose your" : "Begin this scroll with a",
);

const surfaceSubtitleAccent = computed(() => "Dungeon Mode");

const heroTitle = computed(() => (modeFlow.value === "review" ? "Mastery Awaits" : "Study Begins"));

const heroBody = computed(() =>
  modeFlow.value === "review"
    ? `Your work on ${materialTitle.value} has been digested. Choose a mode to revisit the knowledge from a different angle.`
    : `You are about to enter ${materialTitle.value}. Pick a mode that matches how you want to internalize the material.`,
);

const footerMeta = computed(() =>
  modeFlow.value === "review"
    ? ["15m Session", "92% Retention"]
    : ["First Run", "Adaptive Trial"],
);

const secondaryActionLabel = computed(() =>
  modeFlow.value === "review" ? "Review Material Instead" : "Return to Library",
);

const selectedMode = computed(
  () => modeOptions.find((mode) => mode.id === selectedModeId.value) ?? null,
);

const modeLabels: Record<string, string> = {
  "endless-abyss": "深度",
  "speed-survival": "刺激",
  "knowledge-draft": "轻松",
};

const enterDungeon = async () => {
  if (!selectedModeId.value) {
    return;
  }
  if (selectedModeId.value === "endless-abyss") {
    await router.push({
      path: "/library/game-modes/endless-abyss",
      query: {
        flow: modeFlow.value,
        title: materialTitle.value,
        subtitle: materialSubtitle.value,
        format: route.query.format || "SCROLL",
      },
    });
    return;
  }

  if (selectedModeId.value === "speed-survival") {
    await router.push({
      path: "/library/game-modes/speed-survival",
      query: {
        flow: modeFlow.value,
        title: materialTitle.value,
        subtitle: materialSubtitle.value,
        format: route.query.format || "SCROLL",
      },
    });
    return;
  }

  if (selectedModeId.value === "knowledge-draft") {
    await router.push({
      path: "/library/game-modes/knowledge-draft",
      query: {
        flow: modeFlow.value,
        title: materialTitle.value,
        subtitle: materialSubtitle.value,
        format: route.query.format || "SCROLL",
      },
    });
  }
};

const closeModal = async () => {
  await router.push(libraryRoute);
};
</script>

<template>
  <main class="mode-main">
    <div class="mode-main__backdrop" aria-hidden="true">
      <div class="ghost-card ghost-card--large" />
      <div class="ghost-card ghost-card--small" />
      <div class="ghost-card ghost-card--square" />
    </div>

    <div class="mode-overlay" aria-hidden="true" @click="closeModal" />

    <section class="mode-dialog" aria-label="Game mode selection dialog">
      <div class="mode-hero">
        <p class="mode-hero__eyebrow">⌘ DUNGEON SCHOLAR</p>
        <h1>{{ heroTitle }}</h1>
        <p class="mode-hero__copy">{{ heroBody }}</p>
        <div class="mode-hero__material">
          <span>{{ route.query.format || "SCROLL" }}</span>
          <strong>{{ materialTitle }}</strong>
          <p>{{ materialSubtitle }}</p>
        </div>

        <div class="mode-hero__meta">
          <span>{{ footerMeta[0] }}</span>
          <span>{{ footerMeta[1] }}</span>
        </div>
      </div>

      <div class="mode-content">
        <header class="mode-content__header">
          <h2>{{ surfaceTitle }}</h2>
          <p>
            {{ surfaceSubtitlePrefix }}
            <span>{{ surfaceSubtitleAccent }}</span>
          </p>
        </header>

        <div class="mode-grid">
          <button
            v-for="mode in modeOptions"
            :key="mode.id"
            class="mode-card"
            :class="{ 'mode-card--active': selectedMode?.id === mode.id }"
            type="button"
            :aria-pressed="selectedMode?.id === mode.id"
            @click="selectedModeId = mode.id"
          >
            <span class="mode-card__icon" :class="mode.iconClass">{{ mode.icon }}</span>
            <h3>{{ mode.title }}</h3>
            <p class="mode-card__tag">{{ mode.tag }}</p>
            <p class="mode-card__label">{{ modeLabels[mode.id] }}</p>
            <p class="mode-card__desc">{{ mode.description }}</p>
            <span class="mode-card__preview" :class="mode.previewClass" />
          </button>
        </div>

        <footer class="mode-actions">
          <button class="mode-actions__primary" type="button" :disabled="!selectedModeId" @click="enterDungeon">
            Enter Dungeon →
          </button>
          <button class="mode-actions__secondary" type="button" @click="closeModal">
            {{ secondaryActionLabel }}
          </button>
        </footer>
      </div>
    </section>
  </main>
</template>

<style scoped>
.mode-main {
  background: #f6f8f6;
  min-height: 100vh;
  overflow: hidden;
  padding: 24px;
  position: relative;
}

.mode-main::before {
  background: radial-gradient(circle at 18% 22%, rgba(46, 164, 168, 0.14), transparent 24%),
    radial-gradient(circle at 82% 80%, rgba(246, 185, 113, 0.16), transparent 26%),
    linear-gradient(180deg, rgba(239, 244, 241, 0.92), rgba(246, 248, 246, 0.98));
  content: "";
  inset: 0;
  position: absolute;
}

.mode-main__backdrop {
  inset: 24px;
  position: absolute;
}

.ghost-card {
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 26px;
  position: absolute;
}

.ghost-card--large {
  height: 280px;
  left: 4%;
  top: 16%;
  width: 24%;
}

.ghost-card--small {
  bottom: 14%;
  height: 146px;
  left: 8%;
  width: 18%;
}

.ghost-card--square {
  bottom: 10%;
  height: 180px;
  right: 8%;
  width: 20%;
}

.mode-overlay {
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  background: rgba(255, 255, 255, 0.3);
  inset: 0;
  position: absolute;
}

.mode-dialog {
  background: #f9fbfa;
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 32px;
  box-shadow: 0 28px 52px rgba(27, 39, 49, 0.12);
  display: grid;
  grid-template-columns: minmax(260px, 0.9fr) minmax(0, 1.7fr);
  margin: 78px auto 0;
  max-width: 980px;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.mode-hero {
  background: radial-gradient(circle at 58% 52%, rgba(24, 137, 138, 0.18), transparent 24%),
    linear-gradient(180deg, rgba(2, 18, 26, 1), rgba(3, 30, 41, 0.98));
  color: #eef8f6;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: 28px 24px 18px;
  position: relative;
}

.mode-hero::after {
  background: radial-gradient(circle at 65% 60%, rgba(16, 139, 150, 0.22), transparent 28%);
  content: "";
  inset: 0;
  position: absolute;
}

.mode-hero > * {
  position: relative;
  z-index: 1;
}

.mode-hero__eyebrow {
  color: #18b6c0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin: 0;
}

.mode-hero h1 {
  font-family: var(--font-serif);
  font-size: 42px;
  line-height: 0.95;
  margin: 22px 0 0;
}

.mode-hero__copy {
  color: rgba(233, 241, 243, 0.8);
  font-size: 14px;
  line-height: 1.6;
  margin: 18px 0 0;
}

.mode-hero__material {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(145, 200, 203, 0.16);
  border-radius: 20px;
  margin-top: 24px;
  padding: 18px 16px;
}

.mode-hero__material span {
  color: #55d8de;
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.mode-hero__material strong {
  display: block;
  font-family: var(--font-serif);
  font-size: 28px;
  line-height: 1.1;
  margin-top: 12px;
}

.mode-hero__material p {
  color: rgba(233, 241, 243, 0.72);
  font-size: 13px;
  line-height: 1.6;
  margin: 12px 0 0;
}

.mode-hero__meta {
  display: flex;
  gap: 18px;
  margin-top: auto;
  padding-top: 32px;
}

.mode-hero__meta span {
  color: rgba(233, 241, 243, 0.82);
  font-size: 12px;
}

.mode-content {
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  flex-direction: column;
  padding: 28px 24px 22px;
}

.mode-content__header h2 {
  color: #111827;
  font-family: var(--font-serif);
  font-size: 49px;
  line-height: 1;
  margin: 0;
}

.mode-content__header p {
  color: #5d6775;
  font-size: 15px;
  margin: 10px 0 0;
}

.mode-content__header span {
  color: #1b9ca7;
  font-weight: 700;
}

.mode-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 24px;
}

.mode-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid #dce5ea;
  border-radius: 18px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  min-height: 318px;
  padding: 16px;
  text-align: left;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.mode-card:hover {
  border-color: #9fd7db;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
  transform: translateY(-2px);
}

.mode-card--active {
  border-color: #2ba0ab;
  box-shadow: 0 16px 28px rgba(23, 113, 121, 0.14);
}

.mode-card__icon {
  align-items: center;
  border-radius: 999px;
  display: inline-flex;
  font-size: 22px;
  height: 50px;
  justify-content: center;
  width: 50px;
}

.mode-card__icon--crimson {
  background: #fff0ef;
  color: #ef5b5b;
}

.mode-card__icon--sky {
  background: #eefafd;
  color: #39a7d6;
}

.mode-card__icon--gold {
  background: #fff8eb;
  color: #ec9f22;
}

.mode-card h3 {
  color: #111827;
  font-family: var(--font-serif);
  font-size: 24px;
  line-height: 1.12;
  margin: 16px 0 0;
}

.mode-card__tag {
  color: #16946d;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 10px 0 0;
}

.mode-card__label {
  color: #f59e0b;
  font-size: 11px;
  font-weight: 700;
  margin: 4px 0 0;
}

.mode-card__desc {
  color: #667085;
  font-size: 13px;
  line-height: 1.6;
  margin: 12px 0 0;
}

.mode-card__preview {
  border-radius: 14px;
  display: block;
  height: 72px;
  margin-top: auto;
}

.mode-card__preview--abyss {
  background: linear-gradient(135deg, rgba(234, 88, 12, 0.18), rgba(251, 146, 60, 0.08)),
    radial-gradient(circle at 24% 30%, rgba(254, 205, 211, 0.7), transparent 32%),
    linear-gradient(140deg, #fff7ed, #fefce8);
}

.mode-card__preview--speed {
  background: radial-gradient(circle at 26% 28%, rgba(251, 191, 36, 0.78), transparent 22%),
    radial-gradient(circle at 64% 34%, rgba(244, 114, 182, 0.68), transparent 24%),
    radial-gradient(circle at 74% 64%, rgba(96, 165, 250, 0.72), transparent 24%),
    linear-gradient(135deg, #fff7cc, #f4d8ff 48%, #c9f4ff);
}

.mode-card__preview--draft {
  background: radial-gradient(circle at 24% 32%, rgba(180, 197, 255, 0.9), transparent 20%),
    radial-gradient(circle at 76% 38%, rgba(147, 197, 253, 0.58), transparent 18%),
    linear-gradient(145deg, #8295ff, #6c70c5 44%, #90b0ff);
}

.mode-actions {
  border-top: 1px solid #e6ecef;
  margin-top: 18px;
  padding-top: 18px;
  text-align: center;
}

.mode-actions__primary {
  background: linear-gradient(90deg, #15919b, #21a8b0);
  border: 0;
  border-radius: 12px;
  box-shadow: 0 14px 28px rgba(21, 145, 155, 0.2);
  color: #ffffff;
  cursor: pointer;
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 700;
  height: 50px;
  padding: 0 28px;
  width: min(100%, 320px);
}

.mode-actions__primary:disabled {
  background: linear-gradient(90deg, #9ca3a8, #b0b5ba);
  box-shadow: none;
  cursor: not-allowed;
}

.mode-actions__secondary {
  background: transparent;
  border: 0;
  color: #9aa2ab;
  cursor: pointer;
  display: block;
  font-size: 13px;
  margin: 12px auto 0;
}

@supports not ((backdrop-filter: blur(6px)) or (-webkit-backdrop-filter: blur(6px))) {
  .mode-overlay {
    background: rgba(115, 129, 125, 0.68);
  }

  .ghost-card,
  .mode-content {
    background: rgba(246, 248, 246, 0.94);
  }
}

@media (max-width: 1180px) {
  .mode-dialog {
    grid-template-columns: 1fr;
    margin-top: 42px;
    max-width: 760px;
  }

  .mode-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .mode-main {
    padding: 14px;
  }

  .mode-main__backdrop {
    inset: 14px;
  }

  .mode-dialog {
    border-radius: 24px;
    margin-top: 12px;
  }

  .mode-hero,
  .mode-content {
    padding: 20px 16px;
  }

  .mode-hero h1,
  .mode-content__header h2 {
    font-size: 34px;
  }

  .mode-grid {
    grid-template-columns: 1fr;
  }
}
</style>
