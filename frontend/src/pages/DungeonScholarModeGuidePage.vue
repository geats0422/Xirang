<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { ROUTES } from "../constants/routes";

type ModeId = "endless-abyss" | "speed-survival" | "knowledge-draft" | "review";
type ModeGuideKey = "endlessAbyss" | "speedSurvival" | "knowledgeDraft" | "review";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const mode = computed<ModeId>(() => {
  const rawMode = route.query.mode;
  if (rawMode === "speed-survival" || rawMode === "knowledge-draft" || rawMode === "review") {
    return rawMode;
  }
  return "endless-abyss";
});

const modeGuideKeyMap: Record<ModeId, ModeGuideKey> = {
  "endless-abyss": "endlessAbyss",
  "speed-survival": "speedSurvival",
  "knowledge-draft": "knowledgeDraft",
  review: "review",
};

const modeGuideKey = computed(() => modeGuideKeyMap[mode.value]);
const modeName = computed(() => t(`modeGuide.modes.${modeGuideKey.value}.name`));
const pageTitle = computed(() => t("modeGuide.title", { mode: modeName.value }));
const modeSummary = computed(() => t(`modeGuide.modes.${modeGuideKey.value}.summary`));
const objectiveText = computed(() => t(`modeGuide.modes.${modeGuideKey.value}.objective`));

const flowItems = computed(() =>
  [1, 2, 3].map((index) => t(`modeGuide.modes.${modeGuideKey.value}.flow.${index}`)),
);

const rewardItems = computed(() =>
  [1, 2].map((index) => t(`modeGuide.modes.${modeGuideKey.value}.rewards.${index}`)),
);

const tipItems = computed(() =>
  [1, 2, 3].map((index) => t(`modeGuide.modes.${modeGuideKey.value}.tips.${index}`)),
);

const goBack = async () => {
  await router.push({ path: ROUTES.gameModes, query: route.query });
};
</script>

<template>
  <main class="guide-page">
    <section class="guide-shell" :aria-label="t('modeGuide.aria')">
      <header class="guide-header">
        <button class="guide-back" type="button" :aria-label="t('modeGuide.back')" @click="goBack">
          <span aria-hidden="true">←</span>
          <span>{{ t("modeGuide.back") }}</span>
        </button>
        <div class="guide-header__copy">
          <p>{{ t("modeGuide.eyebrow") }}</p>
          <h1>{{ pageTitle }}</h1>
          <p>{{ modeSummary }}</p>
        </div>
      </header>

      <section class="guide-grid">
        <article class="guide-card">
          <h2>{{ t("modeGuide.sections.objective") }}</h2>
          <p>{{ objectiveText }}</p>
        </article>

        <article class="guide-card">
          <h2>{{ t("modeGuide.sections.flow") }}</h2>
          <ol>
            <li v-for="item in flowItems" :key="item">{{ item }}</li>
          </ol>
        </article>

        <article class="guide-card">
          <h2>{{ t("modeGuide.sections.rewards") }}</h2>
          <ul>
            <li v-for="item in rewardItems" :key="item">{{ item }}</li>
          </ul>
        </article>

        <article class="guide-card">
          <h2>{{ t("modeGuide.sections.tips") }}</h2>
          <ul>
            <li v-for="item in tipItems" :key="item">{{ item }}</li>
          </ul>
        </article>
      </section>

      <footer class="guide-footer">
        <button class="guide-return" type="button" @click="goBack">{{ t("modeGuide.returnToPath") }}</button>
      </footer>
    </section>
  </main>
</template>

<style scoped>
.guide-page {
  background: var(--color-page-bg);
  min-height: 100vh;
  padding: 24px;
}

.guide-shell {
  background: color-mix(in srgb, var(--color-surface) 88%, var(--color-surface-alt) 12%);
  border: 1px solid var(--color-border);
  border-radius: 22px;
  margin: 0 auto;
  max-width: 980px;
  min-height: 740px;
  padding: 22px;
}

.guide-header {
  background: linear-gradient(90deg, var(--color-primary-500), var(--color-primary-600));
  border-radius: 16px;
  color: var(--color-surface);
  display: grid;
  gap: 16px;
  grid-template-columns: auto 1fr;
  padding: 18px;
}

.guide-back {
  align-items: center;
  background: color-mix(in srgb, var(--color-surface) 16%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-surface) 52%, transparent);
  border-radius: 12px;
  color: var(--color-surface);
  cursor: pointer;
  display: inline-flex;
  font-weight: 700;
  gap: 6px;
  height: 40px;
  justify-content: center;
  padding: 0 12px;
}

.guide-header__copy p {
  color: color-mix(in srgb, var(--color-surface) 88%, transparent);
  margin: 0;
}

.guide-header__copy h1 {
  font-family: var(--font-serif);
  font-size: 34px;
  margin: 4px 0;
}

.guide-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 22px;
}

.guide-card {
  background: color-mix(in srgb, var(--color-surface) 92%, var(--color-primary-100) 8%);
  border: 1px solid var(--color-border-soft);
  border-radius: 14px;
  padding: 16px;
}

.guide-card h2 {
  color: var(--color-text-strong);
  font-size: 18px;
  margin: 0 0 8px;
}

.guide-card p,
.guide-card li {
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.55;
}

.guide-card ol,
.guide-card ul {
  margin: 0;
  padding-left: 18px;
}

.guide-footer {
  margin-top: 20px;
  text-align: right;
}

.guide-return {
  background: linear-gradient(90deg, var(--color-primary-600), var(--color-primary-500));
  border: 0;
  border-radius: 12px;
  color: var(--color-surface);
  cursor: pointer;
  font-weight: 700;
  min-height: 44px;
  padding: 0 20px;
}

@media (max-width: 900px) {
  .guide-grid {
    grid-template-columns: 1fr;
  }

  .guide-header__copy h1 {
    font-size: 28px;
  }
}
</style>
