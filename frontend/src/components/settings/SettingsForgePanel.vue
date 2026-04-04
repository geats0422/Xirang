<template>
  <section class="panel">
    <div class="panel__header">
      <span class="panel__icon">⌘</span>
      <h3>{{ t("settings.forge.title") }}</h3>
    </div>

    <div class="forge-wrap">
      <div class="forge-head">
        <span>{{ t("settings.forge.activeModel") }}</span>
        <span class="ai-powered">✦ {{ t("settings.forge.powered") }}</span>
      </div>

      <!-- Default collapsed state - shows selected model card -->
      <div
        v-if="!isExpanded"
        class="model-card"
        @click="toggleExpand"
      >
        <div class="model-card__content">
          <div class="model-card__header">
            <div class="model-card__name">{{ localizedActiveModel?.name || t("settings.forge.selectModel") }}</div>
            <div v-if="localizedActiveModel?.provider" class="model-card__provider">{{ localizedActiveModel.provider }}</div>
          </div>
          <div v-if="localizedActiveModel?.description" class="model-card__description">{{ localizedActiveModel.description }}</div>
          <div v-if="localizedActiveModel?.tags && localizedActiveModel.tags.length > 0" class="model-card__tags">
            <span v-for="tag in localizedActiveModel.tags" :key="tag" class="model-card__tag">{{ tag }}</span>
          </div>
        </div>
        <div class="model-card__expand-hint">
          <span class="model-card__expand-icon">▼</span>
        </div>
      </div>

      <!-- Expanded model selection list -->
      <div
        v-else
        ref="modelListRef"
        class="model-list-container"
      >
        <div class="model-list-header">
          <span class="model-list-title">{{ t("settings.forge.selectModel") }}</span>
          <div class="model-list-controls">
            <button type="button" class="scroll-btn scroll-btn--up" :disabled="!canScrollUp" @click="scrollUp">↑</button>
            <button type="button" class="scroll-btn scroll-btn--down" :disabled="!canScrollDown" @click="scrollDown">↓</button>
            <button type="button" class="collapse-btn" @click="toggleExpand">{{ t("settings.forge.collapse") }}</button>
          </div>
        </div>
        
        <div ref="scrollAreaRef" class="model-list-scroll-area">
          <div class="model-list" :style="{ transform: `translateY(-${scrollPosition}px)` }">
            <article
              v-for="model in localizedModels"
              :key="model.id"
              class="model-row"
              :class="{ 'model-row--active': model.id === activeModelId }"
              @click="selectModel(model.id)"
            >
              <div class="model-row__info">
                <div class="model-row__name">{{ model.name }}</div>
                <div class="model-row__tags">
                  <span v-if="model.provider" class="model-row__provider">{{ model.provider }}</span>
                  <span v-if="model.tags.includes('PRO')" class="pro-badge">{{ t("settings.forge.proBadge") }}</span>
                </div>
              </div>
            </article>
          </div>
        </div>
      </div>

      <div class="forge-note">ⓘ {{ t("settings.forge.note") }}</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { getAvailableModels, getSettings, updateSettings, type ModelInfo } from "../../api/settings";

const { t } = useI18n();

const MODELS_KEY = "xirang-forge-model";

// Default fallback models (used if API fails)
const defaultModels: ModelInfo[] = [
  {
    id: "nvidia/nemotron-3-nano-30b-a3b",
    name: "NVIDIA Nemotron",
    description: "",
    tags: ["NVIDIA"],
    provider: "nvidia",
  },
];

const availableModels = ref<ModelInfo[]>(defaultModels);
const activeModelId = ref<string>(defaultModels[0].id);
const isLoading = ref(false);
const isExpanded = ref(false);

const localizedModels = computed<ModelInfo[]>(() =>
  availableModels.value.map((model) => {
    if (model.id !== defaultModels[0].id) {
      return model;
    }
    return {
      ...model,
      description: t("settings.forge.defaultModelDesc"),
      tags: ["NVIDIA", t("settings.forge.defaultModelTag")],
    };
  }),
);

const localizedActiveModel = computed(() =>
  localizedModels.value.find((m) => m.id === activeModelId.value) || localizedModels.value[0],
);

// Toggle expand/collapse state
const toggleExpand = () => {
  isExpanded.value = !isExpanded.value;
};

// Scroll state
const modelListRef = ref<HTMLElement | null>(null);
const scrollAreaRef = ref<HTMLElement | null>(null);
const scrollPosition = ref(0);
const rowHeight = 56; // px
const visibleRows = 4;
const scrollStep = rowHeight * 2; // scroll 2 rows at a time



/** Fetch available models from backend API */
const fetchModels = async () => {
  try {
    const models = await getAvailableModels();
    if (models.length > 0) {
      availableModels.value = models;
    }
  } catch {
    // Use default models if API fails
    console.warn("Failed to fetch models from API, using defaults");
  }
};

/** Load user's selected model from backend */
const loadUserModel = async () => {
  try {
    const settings = await getSettings();
    if (settings.selected_model) {
      // Verify the saved model is in available list
      const modelExists = availableModels.value.some((m) => m.id === settings.selected_model);
      if (modelExists) {
        activeModelId.value = settings.selected_model;
        return;
      }
    }
  } catch {
    // Fall back to localStorage
  }

  // Fallback to localStorage
  if (typeof window !== "undefined") {
    const savedModel = window.localStorage.getItem(MODELS_KEY);
    if (savedModel && availableModels.value.some((model) => model.id === savedModel)) {
      activeModelId.value = savedModel;
      return;
    }
  }

  activeModelId.value = availableModels.value[0]?.id ?? defaultModels[0].id;
};

/** Select a model and save to backend */
const selectModel = async (modelId: string) => {
  activeModelId.value = modelId;

  // Save to localStorage as backup
  if (typeof window !== "undefined") {
    window.localStorage.setItem(MODELS_KEY, modelId);
  }

  // Save to backend user settings
  try {
    await updateSettings({ selected_model: modelId });
  } catch {
    console.warn("Failed to save model selection to backend");
  }

  // Collapse the list after selection
  isExpanded.value = false;
};

// Scroll functionality
const totalListHeight = computed(() => availableModels.value.length * rowHeight);
const visibleHeight = computed(() => visibleRows * rowHeight);
const maxScrollPosition = computed(() => Math.max(0, totalListHeight.value - visibleHeight.value));

const canScrollUp = computed(() => scrollPosition.value > 0);
const canScrollDown = computed(() => scrollPosition.value < maxScrollPosition.value);

const scrollUp = () => {
  const newPosition = Math.max(0, scrollPosition.value - scrollStep);
  smoothScrollTo(newPosition);
};

const scrollDown = () => {
  const newPosition = Math.min(maxScrollPosition.value, scrollPosition.value + scrollStep);
  smoothScrollTo(newPosition);
};

const smoothScrollTo = (position: number) => {
  scrollPosition.value = position;
};

// Handle mouse wheel scrolling on the scroll area
const handleWheel = (event: WheelEvent) => {
  event.preventDefault();
  const delta = event.deltaY;
  const direction = delta > 0 ? 1 : -1;
  const newPosition = scrollPosition.value + direction * scrollStep;
  
  if (newPosition >= 0 && newPosition <= maxScrollPosition.value) {
    smoothScrollTo(newPosition);
  }
};

// Ensure active model is visible when selection changes
const ensureActiveModelVisible = () => {
  const activeIndex = availableModels.value.findIndex(model => model.id === activeModelId.value);
  if (activeIndex === -1) return;
  
  const activeItemTop = activeIndex * rowHeight;
  const activeItemBottom = activeItemTop + rowHeight;
  
  if (activeItemTop < scrollPosition.value) {
    // Active item is above visible area
    smoothScrollTo(activeItemTop);
  } else if (activeItemBottom > scrollPosition.value + visibleHeight.value) {
    // Active item is below visible area
    smoothScrollTo(activeItemBottom - visibleHeight.value);
  }
};

onMounted(async () => {
  isLoading.value = true;
  await fetchModels();
  await loadUserModel();
  isLoading.value = false;
  
  // Ensure active model is visible after loading
  setTimeout(() => {
    ensureActiveModelVisible();
  }, 0);
  
  // Add wheel event listener to scroll area
  const scrollArea = scrollAreaRef.value;
  if (scrollArea) {
    scrollArea.addEventListener('wheel', handleWheel, { passive: false });
  }
});

onBeforeUnmount(() => {
  // Remove wheel event listener
  const scrollArea = scrollAreaRef.value;
  if (scrollArea) {
    scrollArea.removeEventListener('wheel', handleWheel);
  }
});

// Watch for active model changes to ensure it's visible
watch(activeModelId, () => {
  setTimeout(() => {
    ensureActiveModelVisible();
  }, 0);
});
</script>

<style scoped>
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-top: 16px;
  overflow: visible;
}

.panel__header {
  align-items: center;
  border-bottom: 1px solid var(--color-border-soft);
  display: flex;
  gap: 10px;
  padding: 14px 16px;
}

.panel__icon {
  color: var(--color-icon-text);
  font-size: 16px;
}

.panel__header h3 {
  color: var(--color-text-dark);
  font-family: var(--font-serif);
  font-size: 24px;
  margin: 0;
}

.forge-wrap {
  padding: 14px 16px 16px;
}

.forge-head {
  align-items: center;
  color: var(--color-text-muted);
  display: flex;
  font-size: 12px;
  font-weight: 600;
  justify-content: space-between;
}

.ai-powered {
  color: var(--color-primary-500);
  font-size: 11px;
  letter-spacing: 0.04em;
}

/* Model card - default collapsed state */
.model-card {
  align-items: flex-start;
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  margin-top: 10px;
  padding: 16px;
  transition: all 0.2s ease;
}

.model-card:hover {
  border-color: var(--color-primary-500);
  background: var(--color-surface);
}

.model-card__content {
  flex: 1;
}

.model-card__header {
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.model-card__name {
  color: var(--color-text-dark);
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 500;
  line-height: 1.3;
}

.model-card__provider {
  background: var(--color-primary-100);
  border-radius: 999px;
  color: var(--color-primary-600);
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
}

.model-card__description {
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 10px;
}

.model-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.model-card__tag {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
}

.model-card__expand-hint {
  align-items: center;
  display: flex;
  padding-left: 16px;
}

.model-card__expand-icon {
  color: var(--color-text-muted);
  font-size: 12px;
}

/* Model list container */
.model-list-container {
  margin-top: 10px;
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px;
  position: relative;
}

.model-list-header {
  align-items: center;
  color: var(--color-text-muted);
  display: flex;
  font-size: 12px;
  font-weight: 600;
  justify-content: space-between;
  margin-bottom: 12px;
}

.model-list-title {
  color: var(--color-text-dark);
  font-weight: 600;
}

.model-list-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.scroll-btn {
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  height: 24px;
  justify-content: center;
  width: 24px;
}

.scroll-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.scroll-btn:hover:not(:disabled) {
  background: var(--color-primary-50);
  border-color: var(--color-primary-500);
  color: var(--color-primary-700);
}

.collapse-btn {
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  font-size: 11px;
  font-weight: 500;
  height: 24px;
  justify-content: center;
  padding: 0 8px;
}

.collapse-btn:hover {
  background: var(--color-primary-50);
  border-color: var(--color-primary-500);
  color: var(--color-primary-700);
}

.model-list-scroll-area {
  height: 224px; /* 4 rows * 56px */
  overflow: hidden;
  position: relative;
}

.model-list {
  transition: transform 0.2s ease;
  will-change: transform;
}

.model-row {
  align-items: center;
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  height: 56px;
  padding: 0 12px;
  transition: all 0.15s ease;
}

.model-row:hover {
  background: var(--color-surface);
  border-color: var(--color-border);
}

.model-row--active {
  background: var(--color-primary-50);
  border-color: var(--color-primary-500);
}

.model-row--active:hover {
  background: var(--color-primary-100);
  border-color: var(--color-primary-500);
}

.model-row__info {
  align-items: center;
  display: flex;
  gap: 12px;
  flex: 1;
}

.model-row__name {
  color: var(--color-text-dark);
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.2;
  flex: 1;
}

.model-row__tags {
  align-items: center;
  display: flex;
  gap: 6px;
}

.model-row__provider {
  background: var(--color-surface);
  border-radius: 999px;
  color: var(--color-text-secondary);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
}

.model-row--active .model-row__provider {
  background: var(--color-primary-100);
  color: var(--color-primary-600);
}

.pro-badge {
  background: var(--color-chip-amber-bg);
  border-radius: 4px;
  color: var(--color-chip-amber-text);
  font-size: 10px;
  font-weight: 700;
  padding: 2px 5px;
}

.forge-note {
  align-items: center;
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text-muted);
  font-size: 12px;
  line-height: 1.45;
  margin-top: 12px;
  padding: 11px 12px;
}

/* Responsive adjustments for smaller screens */
@media (max-width: 1080px) {
  .model-list-scroll-area {
    height: 168px; /* 3 rows * 56px for smaller screens */
  }
}
</style>
