<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    visible: boolean;
    modeName: string;
    xpGained: number;
    coinReward: number;
    goalText: string;
    comboCount?: number;
    goalCurrent?: number;
    goalTotal?: number;
    xpGainPercent?: number;
    reviewEnabled?: boolean;
    reviewLabel?: string;
  }>(),
  {
    comboCount: 12,
    goalCurrent: 5,
    goalTotal: 10,
    xpGainPercent: 15,
    reviewEnabled: true,
    reviewLabel: "Review Mistakes",
  }
);

const emit = defineEmits<{
  close: [];
  confirm: [];
  review: [];
}>();

const goalProgressPercent = computed(() => {
  if (props.goalTotal === 0) return 0;
  return Math.round((props.goalCurrent / props.goalTotal) * 100);
});

const goalFillWidth = computed(() => `${goalProgressPercent.value}%`);
</script>

<template>
  <transition name="settlement-fade">
    <div v-if="visible" class="settlement-overlay" @click="emit('close')">
      <section class="settlement-modal" aria-label="Dungeon cultivation report" @click.stop>
        <header class="settlement-header">
          <div>
            <h2>Dungeon Secured!</h2>
          </div>
        </header>

        <div class="settlement-hero" aria-hidden="true">
          <div class="settlement-avatar">
            <img src="/taotie-settlement.svg" alt="" />
          </div>
          <span class="coin coin--a">🪙</span>
          <span class="coin coin--b">🪙</span>
          <span class="coin coin--c">🪙</span>
        </div>

        <article class="settlement-card settlement-card--stats">
          <div class="stat-col">
            <p>XP GAINED</p>
            <div class="settlement-value-row">
              <strong>{{ xpGained }}</strong>
              <span class="gain-pill">↗{{ xpGainPercent }}%</span>
            </div>
          </div>

          <div class="stat-col">
            <p>DOPAMINE COINS</p>
            <div class="settlement-value-row">
              <strong class="coin-value">🪙 {{ coinReward }}</strong>
            </div>
          </div>

          <div class="stat-col">
            <p>PERFECT COMBO</p>
            <div class="settlement-value-row">
              <strong>{{ comboCount }}x</strong>
              <span class="combo-bolt">⚡</span>
            </div>
          </div>
        </article>

        <section class="settlement-lower">
          <article class="settlement-card settlement-card--goal">
            <div class="goal-row">
              <p class="settlement-goal-title">✿ Cultivation Goal</p>
              <span>{{ goalCurrent }}/{{ goalTotal }} mins</span>
            </div>
            <div class="settlement-goal-track" role="presentation">
              <span class="settlement-goal-fill" :style="{ width: goalFillWidth }" />
            </div>
            <p class="settlement-goal-copy">{{ goalText }}</p>
          </article>

          <article class="settlement-card settlement-card--league">
            <p>Weekly League</p>
            <strong>Top 12%</strong>
            <span>Keep climbing the ladder</span>
          </article>
        </section>

        <footer class="settlement-actions">
          <button class="settlement-cta" type="button" @click="emit('confirm')">Continue to Library →</button>
          <button
            class="settlement-secondary"
            type="button"
            :disabled="!reviewEnabled"
            @click="emit('review')"
          >
            {{ reviewLabel }}
          </button>
        </footer>
      </section>
    </div>
  </transition>
</template>

<style scoped>
.settlement-overlay {
  align-items: center;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  background: radial-gradient(circle at 50% 20%, rgba(225, 244, 240, 0.55), rgba(245, 248, 246, 0.82) 46%, rgba(245, 248, 246, 0.92));
  display: flex;
  inset: 0;
  justify-content: center;
  padding: 24px;
  position: fixed;
  z-index: 80;
}

.settlement-modal {
  background: transparent;
  max-width: 720px;
  overflow: visible;
  padding: 8px 0 0;
  position: relative;
  width: 100%;
}

.settlement-header {
  text-align: center;
  position: relative;
  z-index: 1;
}

.settlement-header h2 {
  color: #183f3f;
  font-family: var(--font-serif);
  font-size: 52px;
  margin: 0;
  text-shadow: 0 8px 22px rgba(233, 246, 241, 0.9);
}

.settlement-hero {
  align-items: center;
  display: flex;
  justify-content: center;
  margin-top: 18px;
  min-height: 154px;
  position: relative;
}

.settlement-avatar {
  align-items: center;
  display: inline-flex;
  justify-content: center;
}

.settlement-avatar img {
  display: block;
  height: auto;
  max-width: 248px;
  width: min(248px, 52vw);
}

.coin {
  filter: drop-shadow(0 10px 16px rgba(224, 180, 55, 0.26));
  font-size: 24px;
  position: absolute;
}

.coin--a {
  left: 42%;
  top: 18px;
}

.coin--b {
  left: 54%;
  top: 10px;
}

.coin--c {
  left: 59%;
  top: 36px;
}

.settlement-card p,
.settlement-goal-copy {
  color: #798590;
  margin: 0;
}

.settlement-card {
  background: #ffffff;
  border: 1px solid #edf1ef;
  border-radius: 20px;
  box-shadow: 0 16px 38px rgba(47, 67, 75, 0.08);
  padding: 18px 20px;
  position: relative;
  z-index: 1;
}

.settlement-card--stats {
  align-items: stretch;
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 2px;
}

.stat-col {
  border-right: 1px solid #eef2ef;
  min-height: 92px;
  padding-right: 12px;
}

.stat-col:last-child {
  border-right: 0;
  padding-right: 0;
}

.settlement-value-row {
  align-items: baseline;
  display: flex;
  gap: 6px;
  margin-top: 8px;
}

.settlement-value-row strong,
.settlement-card--reward strong {
  color: #1f2a3d;
  font-size: 40px;
  line-height: 1;
}

.gain-pill {
  background: #dff8f0;
  border-radius: 999px;
  color: #26b88f;
  font-size: 12px;
  font-weight: 800;
  padding: 3px 8px;
}

.coin-value {
  color: #e0a126 !important;
  font-size: 32px !important;
}

.combo-bolt {
  color: #3a9cd6;
  font-size: 18px;
}

.settlement-lower {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1.45fr) minmax(0, 0.72fr);
  margin-top: 14px;
}

.settlement-goal-title {
  color: #287f88 !important;
  font-size: 13px;
  font-weight: 800;
}

.goal-row {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.goal-row span {
  color: #95a09e;
  font-size: 12px;
  font-weight: 700;
}

.settlement-goal-track {
  background: #d7ece8;
  border-radius: 999px;
  height: 10px;
  margin-top: 12px;
  overflow: hidden;
}

.settlement-goal-fill {
  background: linear-gradient(90deg, #2ba8b1, #58c6bd);
  display: block;
  height: 100%;
}

.settlement-goal-copy {
  font-size: 13px;
  line-height: 1.5;
  margin-top: 12px;
}

.settlement-card--league {
  align-items: center;
  background: linear-gradient(180deg, #f5f8ff, #eef3ff 70%, #ecf2ff);
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 136px;
  text-align: center;
}

.settlement-card--league p {
  color: #7a8ba1;
  font-size: 12px;
}

.settlement-card--league strong {
  color: #2a5f9b;
  font-size: 28px;
  margin-top: 6px;
}

.settlement-card--league span {
  color: #9fb0bf;
  font-size: 12px;
  margin-top: 8px;
}

.settlement-actions {
  display: grid;
  gap: 10px;
  grid-template-columns: minmax(0, 1fr) auto;
  margin-top: 16px;
}

.settlement-cta {
  background: linear-gradient(90deg, #15939c, #1eb0b6);
  border: 0;
  border-radius: 18px;
  box-shadow: 0 16px 30px rgba(21, 147, 156, 0.26);
  color: #fff;
  cursor: pointer;
  font-family: var(--font-serif);
  font-size: 17px;
  font-weight: 700;
  height: 54px;
  position: relative;
  z-index: 1;
}

.settlement-secondary {
  background: #ffffff;
  border: 1px solid #dde5e6;
  border-radius: 16px;
  color: #71868e;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  height: 54px;
  padding: 0 16px;
}

.settlement-secondary:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

@media (max-width: 760px) {
  .settlement-modal {
    border-radius: 22px;
    padding: 18px;
  }

  .settlement-header h2 {
    font-size: 40px;
  }

  .settlement-card--stats,
  .settlement-lower,
  .settlement-actions {
    grid-template-columns: 1fr;
  }

  .stat-col {
    border-right: 0;
    border-bottom: 1px solid #eef2ef;
    padding-bottom: 10px;
    padding-right: 0;
  }

  .stat-col:last-child {
    border-bottom: 0;
    padding-bottom: 0;
  }
}

.settlement-fade-enter-active,
.settlement-fade-leave-active {
  transition: opacity 0.2s ease;
}

.settlement-fade-enter-from,
.settlement-fade-leave-to {
  opacity: 0;
}
</style>
