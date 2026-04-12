<script setup lang="ts">
import { useActiveEffects } from "../../composables/useActiveEffects";

const { activeXpBoost } = useActiveEffects();

function formatTime(secs: number): string {
  if (!Number.isFinite(secs) || secs === Infinity) return "∞";
  const m = Math.floor(secs / 60).toString().padStart(2, "0");
  const s = (secs % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}
</script>

<template>
  <div v-if="activeXpBoost" class="active-effects-bar">
    <span class="effect-pill effect-pill--violet">
      ⚡ {{ activeXpBoost.multiplier }}x {{ $t("shop.xpBoost") }}
      {{ formatTime(activeXpBoost.remainingSeconds) }}
    </span>
  </div>
</template>
