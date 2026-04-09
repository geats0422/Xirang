import { computed, ref } from "vue";
import { getLearningPath, type LearningPathStage, type StageStatus } from "../api/learningPaths";

const CACHE_KEY_PREFIX = "xirang:learning-path:";

export function useLearningPath(documentId: string, mode: "speed" | "draft" | "endless") {
  const stages = ref<LearningPathStage[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const currentStageIndex = computed(() => {
    const completedIndex = stages.value.findIndex((s) => s.status !== "completed");
    return completedIndex === -1 ? stages.value.length : completedIndex;
  });

  const cacheKey = `${CACHE_KEY_PREFIX}${documentId}:${mode}`;

  const loadFromCache = (): LearningPathStage[] | null => {
    if (typeof window === "undefined") return null;
    const cached = localStorage.getItem(cacheKey);
    return cached ? JSON.parse(cached) : null;
  };

  const saveToCache = (data: LearningPathStage[]) => {
    if (typeof window === "undefined") return;
    localStorage.setItem(cacheKey, JSON.stringify(data));
  };

  const fetchProgress = async () => {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await getLearningPath(documentId, mode);
      stages.value = response.stages;
      saveToCache(response.stages);
    } catch {
      const cached = loadFromCache();
      if (cached) {
        stages.value = cached;
      } else {
        error.value = "Failed to load learning path";
      }
    } finally {
      isLoading.value = false;
    }
  };

  const getStageStatus = (index: number): StageStatus => {
    if (index < currentStageIndex.value) return "completed";
    if (index === currentStageIndex.value) return "unlocked";
    return "locked";
  };

  return {
    stages,
    isLoading,
    error,
    currentStageIndex,
    fetchProgress,
    getStageStatus,
  };
}
