<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { ROUTES } from "../constants/routes";

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

const { t, locale } = useI18n();

onMounted(() => {
  document.title = t("modeSelection.metaTitle");
});

watch(locale, () => {
  document.title = t("modeSelection.metaTitle");
});
const libraryRoute = ROUTES.library;

const modeOptions = computed<DungeonMode[]>(() => [
  {
    id: "endless-abyss",
    icon: "♡",
    iconClass: "mode-card__icon--crimson",
    title: t("modeSelection.options.endlessAbyss.title"),
    tag: t("modeSelection.options.endlessAbyss.tag"),
    description: t("modeSelection.options.endlessAbyss.description"),
    previewClass: "mode-card__preview--abyss",
  },
  {
    id: "speed-survival",
    icon: "⚡",
    iconClass: "mode-card__icon--sky",
    title: t("modeSelection.options.speedSurvival.title"),
    tag: t("modeSelection.options.speedSurvival.tag"),
    description: t("modeSelection.options.speedSurvival.description"),
    previewClass: "mode-card__preview--speed",
  },
  {
    id: "knowledge-draft",
    icon: "◫",
    iconClass: "mode-card__icon--gold",
    title: t("modeSelection.options.knowledgeDraft.title"),
    tag: t("modeSelection.options.knowledgeDraft.tag"),
    description: t("modeSelection.options.knowledgeDraft.description"),
    previewClass: "mode-card__preview--draft",
  },
]);

const router = useRouter();
const route = useRoute();
const selectedModeId = ref<string | null>(null);

const modeFlow = computed<ModeFlow>(() => (route.query.flow === "review" ? "review" : "begin"));

const materialTitle = computed(() => {
  const rawTitle = route.query.title;

  if (typeof rawTitle === "string" && rawTitle.trim()) {
    return rawTitle;
  }

  return modeFlow.value === "review"
    ? t("modeSelection.defaults.reviewMaterialTitle")
    : t("modeSelection.defaults.beginMaterialTitle");
});

const materialSubtitle = computed(() => {
  const rawSubtitle = route.query.subtitle;

  if (typeof rawSubtitle === "string" && rawSubtitle.trim()) {
    return rawSubtitle;
  }

  return modeFlow.value === "review"
    ? t("modeSelection.defaults.reviewMaterialSubtitle")
    : t("modeSelection.defaults.beginMaterialSubtitle");
});

const surfaceTitle = computed(() =>
  modeFlow.value === "review"
    ? t("modeSelection.surface.reviewTitle")
    : t("modeSelection.surface.beginTitle"),
);

const surfaceSubtitlePrefix = computed(() =>
  modeFlow.value === "review"
    ? t("modeSelection.surface.reviewSubtitlePrefix")
    : t("modeSelection.surface.beginSubtitlePrefix"),
);

const surfaceSubtitleAccent = computed(() => t("modeSelection.surface.subtitleAccent"));

const heroTitle = computed(() =>
  modeFlow.value === "review"
    ? t("modeSelection.hero.reviewTitle")
    : t("modeSelection.hero.beginTitle"),
);

const heroBody = computed(() =>
  modeFlow.value === "review"
    ? t("modeSelection.hero.reviewBody", { material: materialTitle.value })
    : t("modeSelection.hero.beginBody", { material: materialTitle.value }),
);

const footerMeta = computed(() =>
  modeFlow.value === "review"
    ? [t("modeSelection.footer.reviewSession"), t("modeSelection.footer.reviewRetention")]
    : [t("modeSelection.footer.beginRun"), t("modeSelection.footer.beginTrial")],
);

const secondaryActionLabel = computed(() =>
  modeFlow.value === "review"
    ? t("modeSelection.actions.reviewMaterialInstead")
    : t("modeSelection.actions.returnToLibrary"),
);

const selectedMode = computed(
  () => modeOptions.value.find((mode) => mode.id === selectedModeId.value) ?? null,
);

const modeLabels = computed<Record<string, string>>(() => ({
  "endless-abyss": t("modeSelection.labels.endlessAbyss"),
  "speed-survival": t("modeSelection.labels.speedSurvival"),
  "knowledge-draft": t("modeSelection.labels.knowledgeDraft"),
}));

const enterDungeon = async () => {
  if (!selectedModeId.value) {
    return;
  }
  await router.push({
    path: ROUTES.levelPath,
    query: {
      flow: modeFlow.value,
      documentId: route.query.documentId,
      mode: selectedModeId.value,
      title: materialTitle.value,
      subtitle: materialSubtitle.value,
      format: route.query.format || "SCROLL",
    },
  });
};

const closeModal = async () => {
  await router.push({
    path: libraryRoute,
    query: route.query,
  });
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

    <section class="mode-dialog" :aria-label="t('modeSelection.dialogAria')">
      <div class="mode-hero">
        <p class="mode-hero__eyebrow">{{ t("modeSelection.hero.eyebrow") }}</p>
        <h1>{{ heroTitle }}</h1>
        <p class="mode-hero__copy">{{ heroBody }}</p>
        <div class="mode-hero__material">
          <span>{{ route.query.format || t("modeSelection.defaults.scrollFormat") }}</span>
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
            {{ t("modeSelection.actions.enterDungeon") }}
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
  background: var(--color-page-bg);
  min-height: 100vh;
  overflow: hidden;
  padding: 24px;
  position: relative;
}

.mode-main::before {
  background: radial-gradient(
      circle at 18% 22%,
      color-mix(in srgb, var(--color-cyan-100) 34%, transparent),
      transparent 24%
    ),
    radial-gradient(
      circle at 82% 80%,
      color-mix(in srgb, var(--color-streak-bg) 42%, transparent),
      transparent 26%
    ),
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--color-page-bg) 92%, var(--color-surface) 8%),
      color-mix(in srgb, var(--color-page-bg) 98%, var(--color-surface) 2%)
    );
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
  background: var(--color-overlay-glass);
  border: 1px solid var(--color-glass-border);
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
  background: var(--color-overlay-glass);
  inset: 0;
  position: absolute;
}

.mode-dialog {
  background: var(--color-surface-alt);
  border: 1px solid var(--color-glass-border);
  border-radius: 32px;
  box-shadow: var(--shadow-elevated);
  display: grid;
  grid-template-columns: minmax(260px, 0.9fr) minmax(0, 1.7fr);
  margin: 78px auto 0;
  max-width: 980px;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.mode-hero {
  background: radial-gradient(
      circle at 58% 52%,
      color-mix(in srgb, var(--color-cyan-100) 28%, transparent),
      transparent 24%
    ),
    linear-gradient(180deg, var(--color-deep-teal), var(--color-primary-700));
  color: var(--color-surface);
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: 28px 24px 18px;
  position: relative;
}

.mode-hero::after {
  background: radial-gradient(
    circle at 65% 60%,
    color-mix(in srgb, var(--color-cyan-100) 36%, transparent),
    transparent 28%
  );
  content: "";
  inset: 0;
  position: absolute;
}

.mode-hero > * {
  position: relative;
  z-index: 1;
}

.mode-hero__eyebrow {
  color: var(--color-cyan-100);
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
  color: color-mix(in srgb, var(--color-surface) 80%, transparent);
  font-size: 14px;
  line-height: 1.6;
  margin: 18px 0 0;
}

.mode-hero__material {
  background: color-mix(in srgb, var(--color-surface) 6%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-cyan-100) 24%, transparent);
  border-radius: 20px;
  margin-top: 24px;
  padding: 18px 16px;
}

.mode-hero__material span {
  color: var(--color-cyan-100);
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
  color: color-mix(in srgb, var(--color-surface) 72%, transparent);
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
  color: color-mix(in srgb, var(--color-surface) 82%, transparent);
  font-size: 12px;
}

.mode-content {
  background: var(--color-login-card-bg);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  flex-direction: column;
  padding: 28px 24px 22px;
}

.mode-content__header h2 {
  color: var(--color-text-strong);
  font-family: var(--font-serif);
  font-size: 49px;
  line-height: 1;
  margin: 0;
}

.mode-content__header p {
  color: var(--color-text-secondary);
  font-size: 15px;
  margin: 10px 0 0;
}

.mode-content__header span {
  color: var(--color-primary-500);
  font-weight: 700;
}

.mode-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 24px;
}

.mode-card {
  background: color-mix(in srgb, var(--color-surface) 94%, transparent);
  border: 1px solid var(--color-border);
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
  border-color: var(--color-upload-border);
  box-shadow: var(--shadow-card);
  transform: translateY(-2px);
}

.mode-card--active {
  border-color: var(--color-primary-500);
  box-shadow: var(--shadow-button);
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
  background: var(--color-danger-surface);
  color: var(--color-trend-down);
}

.mode-card__icon--sky {
  background: var(--color-cyan-50);
  color: var(--color-shop-brand-teal);
}

.mode-card__icon--gold {
  background: var(--color-streak-bg);
  color: var(--color-coin-value);
}

.mode-card h3 {
  color: var(--color-text-strong);
  font-family: var(--font-serif);
  font-size: 24px;
  line-height: 1.12;
  margin: 16px 0 0;
}

.mode-card__tag {
  color: var(--color-primary-500);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 10px 0 0;
}

.mode-card__label {
  color: var(--color-muted-gold);
  font-size: 11px;
  font-weight: 700;
  margin: 4px 0 0;
}

.mode-card__desc {
  color: var(--color-text-muted);
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
  background: linear-gradient(
      135deg,
      color-mix(in srgb, var(--color-streak-text) 20%, transparent),
      color-mix(in srgb, var(--color-muted-gold) 14%, transparent)
    ),
    radial-gradient(
      circle at 24% 30%,
      color-mix(in srgb, var(--color-streak-bg) 84%, transparent),
      transparent 32%
    ),
    linear-gradient(140deg, var(--color-streak-bg), var(--color-chip-gold-bg));
}

.mode-card__preview--speed {
  background: radial-gradient(
      circle at 26% 28%,
      color-mix(in srgb, var(--color-muted-gold) 78%, transparent),
      transparent 22%
    ),
    radial-gradient(
      circle at 64% 34%,
      color-mix(in srgb, var(--color-chip-violet-text) 42%, transparent),
      transparent 24%
    ),
    radial-gradient(
      circle at 74% 64%,
      color-mix(in srgb, var(--color-badge-blue-text) 54%, transparent),
      transparent 24%
    ),
    linear-gradient(
      135deg,
      color-mix(in srgb, var(--color-streak-bg) 86%, var(--color-surface) 14%),
      color-mix(in srgb, var(--color-chip-violet-bg) 72%, var(--color-surface) 28%) 48%,
      color-mix(in srgb, var(--color-cyan-100) 76%, var(--color-surface) 24%)
    );
}

.mode-card__preview--draft {
  background: radial-gradient(
      circle at 24% 32%,
      color-mix(in srgb, var(--color-badge-blue-bg) 92%, transparent),
      transparent 20%
    ),
    radial-gradient(
      circle at 76% 38%,
      color-mix(in srgb, var(--color-badge-blue-text) 52%, transparent),
      transparent 18%
    ),
    linear-gradient(
      145deg,
      color-mix(in srgb, var(--color-badge-blue-text) 66%, var(--color-surface) 34%),
      color-mix(in srgb, var(--color-chip-violet-text) 70%, var(--color-text-primary) 30%) 44%,
      color-mix(in srgb, var(--color-badge-blue-bg) 54%, var(--color-badge-blue-text) 46%)
    );
}

.mode-actions {
  border-top: 1px solid var(--color-border-soft);
  margin-top: 18px;
  padding-top: 18px;
  text-align: center;
}

.mode-actions__primary {
  background: linear-gradient(90deg, var(--color-primary-600), var(--color-primary-500));
  border: 0;
  border-radius: 12px;
  box-shadow: var(--shadow-button);
  color: var(--color-surface);
  cursor: pointer;
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 700;
  height: 50px;
  padding: 0 28px;
  width: min(100%, 320px);
}

.mode-actions__primary:disabled {
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--color-text-muted) 72%, var(--color-border) 28%),
    color-mix(in srgb, var(--color-text-muted) 56%, var(--color-border) 44%)
  );
  box-shadow: none;
  cursor: not-allowed;
}

.mode-actions__secondary {
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  display: block;
  font-size: 13px;
  margin: 12px auto 0;
}

@supports not ((backdrop-filter: blur(6px)) or (-webkit-backdrop-filter: blur(6px))) {
  .mode-overlay {
    background: var(--color-overlay-fallback);
  }

  .ghost-card,
  .mode-content {
    background: var(--color-modal-fallback);
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
