<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import GameSettlementModal from "../components/GameSettlementModal.vue";
import { ROUTES } from "../constants/routes";

const { t, locale } = useI18n();

onMounted(() => {
  document.title = t("endlessAbyss.metaTitle");
});

// Update document title reactively when locale changes
watch(locale, () => {
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

const maxHp = 5;
const hpLevel = ref(3);
const floor = ref(5);
const floorTotal = ref(10);
const time = ref("12:45");
const coins = ref(350);

const answer = ref("");
const showSettlement = ref(false);
const runStatus = ref<RunStatus>("normal");

const showNotice = ref(false);

const materialTitle = computed(() => {
  const rawTitle = route.query.title;
    return typeof rawTitle === "string" && rawTitle.trim() ? rawTitle : "Ancient Wisdom";
});

    const chapterTitle = computed(() => `Chapter 3: ${materialTitle.value}`);

                const floorProgress = computed(() => (floor.value / floorTotal.value) * 100);

                const goBack = async () => {
                    await router.push({
                        path: ROUTES.gameModes,
                        query: route.query,
                    });
                };

                const castSpell = () => {
                    if (!answer.value.trim()) {
                        return;
                    }

                    answer.value = "";
                    coins.value += 10;
                    showSettlement.value = true;
                };

                const closeSettlement = () => {
                    showSettlement.value = false;
                };

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
</script>

<template>
  <main class="abyss-page">
    <section class="abyss-shell" aria-label="Endless Abyss gameplay">
      <header class="abyss-status">
        <div class="hp-block" aria-label="Health points">
          <span v-for="index in maxHp" :key="index" class="hp-heart" :class="{ 'hp-heart--empty': index > hpLevel }">
            ♥
          </span>
          <span class="hp-label">HP LEVEL {{ hpLevel }}</span>
        </div>

        <div class="floor-block" aria-label="Floor progress">
          <p>FLOOR {{ floor }}</p>
          <div class="floor-track" role="presentation">
            <span class="floor-fill" :style="{ width: `${floorProgress}%` }" />
          </div>
          <span>{{ floorTotal }}</span>
        </div>

        <div class="meta-block" aria-label="Session info">
          <span>🕒 {{ time }}</span>
          <button class="meta-coin" type="button" @click="goShop">🪙 {{ coins }}</button>
        </div>
      </header>

      <section class="battle-stage">
        <div class="dragon-bg" aria-hidden="true">
          <div class="dragon-art" />
          <div class="dragon-fog" />
        </div>

        <article class="question-card" aria-label="Question card">
          <p class="question-card__tag">QUESTION CARD</p>
          <h1>The philosophical concept of ____ emphasizes living in harmony with the Dao.</h1>

          <footer class="question-card__footer">
            <span>{{ chapterTitle }}</span>
            <span class="question-card__hint">HINT: STARTS WITH W</span>
          </footer>
        </article>
      </section>

      <footer class="answer-zone">
        <label class="answer-input">
          <span aria-hidden="true">✎</span>
          <input v-model="answer" type="text" placeholder="Type the answer keyword" @keydown.enter="castSpell" />
        </label>

        <button class="cast-btn" type="button" @click="castSpell">Cast Spell ✦</button>
        <button class="return-btn" type="button" @click="goBack">Return to Mode Select</button>

        <button class="feedback-action" type="button">
          这题有误
        </button>

        <div v-if="runStatus === 'reduced-reward'" class="run-status-notice">
          ⚠ Reduced rewards: -50% XP/coins
        </div>
      </footer>
    </section>

    <GameSettlementModal
      :visible="showSettlement"
      mode-name="Endless Abyss"
      :xp-gained="250"
      :coin-reward="50"
      goal-text="Keep meditating to reach enlightenment through the abyss."
      @close="closeSettlement"
      @confirm="goBack"
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
</style>
