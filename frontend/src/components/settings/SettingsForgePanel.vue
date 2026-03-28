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

      <div ref="modelSelectRef" class="model-select">
        <button class="model-select__btn" type="button" @click="toggleDropdown">
          <span class="model-select__name">{{ activeModel.name }}</span>
          <span class="model-select__arrow">▾</span>
        </button>

        <div v-if="showModelDropdown" class="model-dropdown">
          <article
            v-for="model in availableModels"
            :key="model.id"
            class="model-card"
            :class="{ 'model-card--active': model.id === activeModelId }"
            @click="selectModel(model.id)"
          >
            <div class="model-card__title-row">
              <div class="model-card__title">{{ model.name }}</div>
              <span v-if="model.tags.includes('PRO')" class="pro-chip">PRO</span>
            </div>
            <p>{{ model.description }}</p>
            <div v-if="model.tags.length > 0" class="tag-row">
              <span v-for="tag in model.tags" :key="tag">{{ tag }}</span>
            </div>
          </article>
        </div>
      </div>

      <div class="forge-note">ⓘ {{ t("settings.forge.note") }}</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";

import { useScholarData } from "../../composables/useScholarData";

const { t } = useI18n();
const { activeModel: selectedModel, modelOptions, setActiveModel } = useScholarData();

type Model = {
  id: string;
  name: string;
  description: string;
  tags: string[];
};

const modelCatalog: Record<string, Omit<Model, "id">> = {};

const toModelMeta = (id: string): Model => {
  const normalized = id.trim();
  void modelCatalog[normalized];

  return {
    id: normalized,
    name: normalized,
    description: "Model from runtime settings.",
    tags: [],
  };
};

const availableModels = computed<Model[]>(() => {
  const candidates = modelOptions.value
    .map((item) => item.trim())
    .filter((item, index, arr) => item.length > 0 && arr.indexOf(item) === index);

  if (candidates.length === 0) {
    return [toModelMeta("gpt-4o-mini")];
  }

  return candidates.map(toModelMeta);
});

const showModelDropdown = ref(false);
const modelSelectRef = ref<HTMLElement | null>(null);

const activeModelId = computed(() => selectedModel.value);

const activeModel = computed<Model>(() => {
  const found = availableModels.value.find((model) => model.id === selectedModel.value);
  return found ?? availableModels.value[0];
});

const selectModel = (modelId: string) => {
  setActiveModel(modelId);
  showModelDropdown.value = false;
};

const toggleDropdown = () => {
  showModelDropdown.value = !showModelDropdown.value;
};

const closeDropdown = (event: MouseEvent) => {
  const target = event.target;
  if (!(target instanceof Node)) {
    return;
  }

  if (!modelSelectRef.value?.contains(target)) {
    showModelDropdown.value = false;
  }
};

onMounted(() => {
  document.addEventListener("click", closeDropdown);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", closeDropdown);
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

.model-select {
  margin-top: 10px;
  position: relative;
}

.model-select__btn {
  align-items: center;
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  padding: 14px;
  width: 100%;
}

.model-select__name {
  color: var(--color-text-dark);
  font-family: var(--font-serif);
  font-size: 15px;
  font-weight: 600;
  line-height: 1;
}

.model-select__arrow {
  color: var(--color-icon-text);
  font-size: 14px;
}

.model-dropdown {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: 0 8px 18px rgba(19, 35, 28, 0.12);
  display: grid;
  gap: 10px;
  left: 0;
  padding: 10px;
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  z-index: 9999;
}

.model-dropdown .model-card {
  cursor: pointer;
}

.model-dropdown .model-card:hover {
  border-color: var(--color-primary-500);
}

.model-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 10px;
}

.model-card {
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 14px;
}

.model-card--active {
  background: var(--color-primary-50);
  border-color: var(--color-primary-500);
}

.model-card__title {
  color: var(--color-text-dark);
  font-family: var(--font-serif);
  font-size: 24px;
  line-height: 1;
}

.model-card p {
  color: var(--color-text-muted);
  font-size: 11px;
  line-height: 1.35;
  margin: 8px 0 0;
}

.tag-row {
  display: flex;
  gap: 6px;
  margin-top: 10px;
}

.tag-row span {
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
}

.model-card--active .tag-row span:nth-child(1) {
  background: var(--color-primary-100);
  color: var(--color-primary-600);
}

.model-card--active .tag-row span:nth-child(2) {
  background: var(--color-primary-50);
  color: var(--color-primary-700);
}

.model-card:not(.model-card--active) .tag-row span:nth-child(1) {
  background: var(--color-surface);
  color: var(--color-text-secondary);
}

.model-card:not(.model-card--active) .tag-row span:nth-child(2) {
  background: var(--color-surface);
  color: var(--color-text-muted);
}

.model-card__title-row {
  align-items: center;
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.pro-chip {
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

@media (max-width: 1080px) {
  .model-grid {
    grid-template-columns: 1fr;
  }
}
</style>
