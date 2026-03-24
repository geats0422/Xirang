<template>
  <section class="panel">
    <div class="panel__header">
      <span class="panel__icon">⌘</span>
      <h3>The Forge Engine</h3>
    </div>

    <div class="forge-wrap">
      <div class="forge-head">
        <span>Active Intelligence Model</span>
        <span class="ai-powered">✦ AI POWERED</span>
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

      <div class="forge-note">ⓘ The Forge Engine powers dynamic storytelling. Pro models may consume more energy (credits) but provide richer narrative depth.</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

type Model = {
  id: string;
  name: string;
  description: string;
  tags: string[];
};

const MODELS_KEY = "xirang-forge-model";

const defaultModels: Model[] = [
  {
    id: "gemini-2.5-flash",
    name: "Gemini 2.5 Flash",
    description: "Fast and efficient. Ideal for quick storytelling and standard quests.",
    tags: ["High Speed", "Low Latency"],
  },
  {
    id: "gemini-3.1-pro",
    name: "Gemini 3.1 Pro",
    description: "Advanced reasoning for complex campaigns and deep lore generation.",
    tags: ["PRO", "Deep Logic", "Creative"],
  },
  {
    id: "claude-3.5-sonnet",
    name: "Claude 3.5 Sonnet",
    description: "Balanced performance for educational content generation.",
    tags: ["Balanced", "Education"],
  },
  {
    id: "gpt-4o",
    name: "GPT-4o",
    description: "Strong all-around capabilities for diverse content needs.",
    tags: ["Versatile", "Adaptive"],
  },
];

const parseAvailableModels = (): Model[] => {
  const envModels = import.meta.env.VITE_AVAILABLE_MODELS;
  if (typeof envModels !== "string") {
    return defaultModels;
  }

  const parsedIds = envModels
    .split(",")
    .map((id) => id.trim())
    .filter((id) => id.length > 0);

  if (parsedIds.length === 0) {
    return defaultModels;
  }

  return parsedIds.map((id) => {
    const matchedModel = defaultModels.find((model) => model.id === id);
    if (matchedModel) {
      return matchedModel;
    }

    return {
      id,
      name: id,
      description: "",
      tags: [],
    };
  });
};

const availableModels = computed<Model[]>(() => parseAvailableModels());
const showModelDropdown = ref(false);
const activeModelId = ref<string>(defaultModels[0].id);
const modelSelectRef = ref<HTMLElement | null>(null);

const activeModel = computed<Model>(() => {
  return availableModels.value.find((model) => model.id === activeModelId.value) ?? availableModels.value[0];
});

const loadActiveModel = () => {
  if (typeof window === "undefined") {
    return;
  }

  const savedModel = window.localStorage.getItem(MODELS_KEY);
  if (savedModel && availableModels.value.some((model) => model.id === savedModel)) {
    activeModelId.value = savedModel;
    return;
  }

  activeModelId.value = availableModels.value[0]?.id ?? defaultModels[0].id;
};

const selectModel = (modelId: string) => {
  activeModelId.value = modelId;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(MODELS_KEY, modelId);
  }
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
  loadActiveModel();
  document.addEventListener("click", closeDropdown);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", closeDropdown);
});
</script>

<style scoped>
.panel {
  background: #ffffff;
  border: 1px solid #e6ece8;
  border-radius: 8px;
  margin-top: 16px;
  overflow: visible;
}

.panel__header {
  align-items: center;
  border-bottom: 1px solid #edf1ee;
  display: flex;
  gap: 10px;
  padding: 14px 16px;
}

.panel__icon {
  color: #728a8d;
  font-size: 16px;
}

.panel__header h3 {
  color: #25333d;
  font-family: var(--font-serif);
  font-size: 24px;
  margin: 0;
}

.forge-wrap {
  padding: 14px 16px 16px;
}

.forge-head {
  align-items: center;
  color: #6c8087;
  display: flex;
  font-size: 12px;
  font-weight: 600;
  justify-content: space-between;
}

.ai-powered {
  color: #2a9ca7;
  font-size: 11px;
  letter-spacing: 0.04em;
}

.model-select {
  margin-top: 10px;
  position: relative;
}

.model-select__btn {
  align-items: center;
  background: #f7f9f8;
  border: 1px solid #dae3de;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  padding: 14px;
  width: 100%;
}

.model-select__name {
  color: #263640;
  font-family: var(--font-serif);
  font-size: 15px;
  font-weight: 600;
  line-height: 1;
}

.model-select__arrow {
  color: #728a8d;
  font-size: 14px;
}

.model-dropdown {
  background: #ffffff;
  border: 1px solid #dae3de;
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
  border-color: #26a0aa;
}

.model-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 10px;
}

.model-card {
  background: #f7f9f8;
  border: 1px solid #dae3de;
  border-radius: 8px;
  padding: 14px;
}

.model-card--active {
  background: #f3fbfc;
  border-color: #26a0aa;
}

.model-card__title {
  color: #263640;
  font-family: var(--font-serif);
  font-size: 24px;
  line-height: 1;
}

.model-card p {
  color: #93a0a6;
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
  background: #d8f5d8;
  color: #498450;
}

.model-card--active .tag-row span:nth-child(2) {
  background: #ddebff;
  color: #5576ac;
}

.model-card:not(.model-card--active) .tag-row span:nth-child(1) {
  background: #ede3ff;
  color: #6b57a7;
}

.model-card:not(.model-card--active) .tag-row span:nth-child(2) {
  background: #ffe9cf;
  color: #b87426;
}

.model-card__title-row {
  align-items: center;
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.pro-chip {
  background: #ffe9c4;
  border-radius: 4px;
  color: #bf852f;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 5px;
}

.forge-note {
  align-items: center;
  background: #f4f8f5;
  border: 1px solid #e0e8e3;
  border-radius: 8px;
  color: #74888f;
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
