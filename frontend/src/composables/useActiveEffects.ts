import { computed, onMounted, onUnmounted, ref } from "vue";
import { getActiveEffects, type ActiveEffect } from "../api/shop";

export type ActiveEffectWithRemaining = ActiveEffect & {
  remainingSeconds: number;
};

export function useActiveEffects() {
  const effects = ref<ActiveEffectWithRemaining[]>([]);
  let timer: ReturnType<typeof setInterval> | null = null;

  async function refresh() {
    const raw = await getActiveEffects();
    effects.value = raw.effects.map((e) => ({
      ...e,
      remainingSeconds: e.expires_at
        ? Math.max(0, Math.floor((new Date(e.expires_at).getTime() - Date.now()) / 1000))
        : Infinity,
    }));
  }

  function startTimer() {
    timer = setInterval(() => {
      effects.value = effects.value.map((e) => ({
        ...e,
        remainingSeconds: e.expires_at
          ? Math.max(0, Math.floor((new Date(e.expires_at).getTime() - Date.now()) / 1000))
          : Infinity,
      }));
    }, 1000);
  }

  onMounted(() => {
    refresh();
    startTimer();
  });

  onUnmounted(() => {
    if (timer) clearInterval(timer);
  });

  const activeXpBoost = computed(() =>
    effects.value.find((e) => e.effect_type === "xp_boost" && e.remainingSeconds > 0),
  );

  const activeShield = computed(() =>
    effects.value.find((e) => e.effect_type === "revive_shield" && e.remainingSeconds > 0),
  );

  return { effects, activeXpBoost, activeShield, refresh };
}
