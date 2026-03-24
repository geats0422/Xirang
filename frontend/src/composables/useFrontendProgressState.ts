import { computed, ref } from "vue";

const xp = ref(0);
const coins = ref(3450);
const streak = ref(0);
const comboCount = ref(0);
const goalCurrent = ref(0);
const goalTotal = ref(10);

const sessionXpGained = ref(0);
const sessionCoinsEarned = ref(0);

const goalProgress = computed(() => {
  if (goalTotal.value === 0) return 0;
  return Math.round((goalCurrent.value / goalTotal.value) * 100);
});

export function useFrontendProgressState() {
  const addXp = (amount: number) => {
    xp.value += amount;
    sessionXpGained.value += amount;
  };

  const addCoins = (amount: number) => {
    coins.value += amount;
    sessionCoinsEarned.value += amount;
  };

  const spendCoins = (amount: number): boolean => {
    if (coins.value < amount) {
      return false;
    }
    coins.value -= amount;
    return true;
  };

  const incrementStreak = () => {
    streak.value += 1;
  };

  const resetStreak = () => {
    streak.value = 0;
  };

  const setCombo = (count: number) => {
    comboCount.value = count;
  };

  const incrementCombo = () => {
    comboCount.value += 1;
  };

  const resetCombo = () => {
    comboCount.value = 0;
  };

  const setGoalProgress = (current: number, total: number) => {
    goalCurrent.value = current;
    goalTotal.value = total;
  };

  const resetSession = () => {
    sessionXpGained.value = 0;
    sessionCoinsEarned.value = 0;
    comboCount.value = 0;
  };

  const resetAll = () => {
    xp.value = 0;
    coins.value = 3450;
    streak.value = 0;
    resetSession();
    goalCurrent.value = 0;
    goalTotal.value = 10;
  };

  return {
    xp,
    coins,
    streak,
    comboCount,
    goalCurrent,
    goalTotal,
    goalProgress,
    sessionXpGained,
    sessionCoinsEarned,
    addXp,
    addCoins,
    spendCoins,
    incrementStreak,
    resetStreak,
    setCombo,
    incrementCombo,
    resetCombo,
    setGoalProgress,
    resetSession,
    resetAll,
  };
}
