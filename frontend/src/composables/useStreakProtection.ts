import { computed } from "vue";
import { useInventory } from "./useInventory";

export function useStreakProtection() {
  const { quantityOf } = useInventory();
  const hasStreakFreeze = computed(() => quantityOf("streak_freeze") > 0);
  return { hasStreakFreeze };
}
