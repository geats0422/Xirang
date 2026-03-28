<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ApiError } from "../api/http";
import { listRunPathOptions, regenerateRunPath, type RunPathOption } from "../api/runs";
import { ROUTES } from "../constants/routes";

type PathNode = {
  id: string;
  label: string;
  type: "battle" | "study" | "checkpoint" | "boss" | "speed" | "draft";
  description: string;
  floor?: number;
  done?: boolean;
  pathVersionId?: string;
  levelNodeId?: string;
};

type ModeId = "endless-abyss" | "speed-survival" | "knowledge-draft";
type PathLoadState = "idle" | "loading" | "generating" | "ready" | "not_ready" | "error";

const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 15;

const route = useRoute();
const router = useRouter();

const mode = computed<ModeId>(() => {
  const rawMode = route.query.mode;
  if (rawMode === "speed-survival" || rawMode === "knowledge-draft") {
    return rawMode;
  }
  return "endless-abyss";
});

const selectedNodeId = ref<string>("");
const loadState = ref<PathLoadState>("idle");
const loadMessage = ref<string>("");
const isRegenerating = ref(false);
let pollTimer: number | null = null;
let pollAttempts = 0;

const modeRouteMap: Record<ModeId, string> = {
  "endless-abyss": ROUTES.endlessAbyss,
  "speed-survival": ROUTES.speedSurvival,
  "knowledge-draft": ROUTES.knowledgeDraft,
};

const modeApiMap: Record<ModeId, "endless" | "speed" | "draft"> = {
  "endless-abyss": "endless",
  "speed-survival": "speed",
  "knowledge-draft": "draft",
};

const modeLabelMap: Record<ModeId, string> = {
  "endless-abyss": "Endless Abyss",
  "speed-survival": "Speed Survival",
  "knowledge-draft": "Knowledge Draft",
};

const endlessNodes: PathNode[] = [
  { id: "F1", label: "F1", floor: 1, type: "battle", description: "Warm-up floor", done: true },
  { id: "F2", label: "F2", floor: 2, type: "study", description: "Steady learning", done: true },
  { id: "F3", label: "F3", floor: 3, type: "checkpoint", description: "Risk check" },
  { id: "F4", label: "F4", floor: 4, type: "study", description: "Pattern practice" },
  { id: "F5", label: "F5", floor: 5, type: "battle", description: "High pressure" },
  { id: "F6", label: "F6", floor: 6, type: "boss", description: "Abyss boss" },
];

const speedNodes: PathNode[] = [
  {
    id: "speed-route-focus",
    label: "R1",
    type: "speed",
    description: "Short rounds, higher accuracy bonus",
    done: true,
  },
  {
    id: "speed-route-burst",
    label: "R2",
    type: "speed",
    description: "Fast tempo with combo scaling",
  },
  {
    id: "speed-route-endurance",
    label: "R3",
    type: "speed",
    description: "Long timer, stable output",
  },
];

const draftNodes: PathNode[] = [
  {
    id: "draft-route-classic",
    label: "R1",
    type: "draft",
    description: "Balanced drafting journey",
    done: true,
  },
  {
    id: "draft-route-theory",
    label: "R2",
    type: "draft",
    description: "Focus on concept-heavy cards",
  },
  {
    id: "draft-route-memory",
    label: "R3",
    type: "draft",
    description: "Retention-oriented drafting",
  },
];

const fallbackNodesForMode = (): PathNode[] => {
  if (mode.value === "endless-abyss") {
    return endlessNodes;
  }
  if (mode.value === "speed-survival") {
    return speedNodes;
  }
  return draftNodes;
};

const clearPollTimer = () => {
  if (pollTimer !== null) {
    window.clearTimeout(pollTimer);
    pollTimer = null;
  }
};

const schedulePoll = () => {
  clearPollTimer();
  if (pollAttempts >= MAX_POLL_ATTEMPTS) {
    loadState.value = "error";
    loadMessage.value = "Path generation timed out. Please retry.";
    return;
  }

  pollTimer = window.setTimeout(async () => {
    pollAttempts += 1;
    await loadPathOptions({ fromPoll: true });
  }, POLL_INTERVAL_MS);
};

const toUserMessage = (error: unknown): { state: PathLoadState; message: string } => {
  if (error instanceof ApiError && error.status === 409) {
    const detail = typeof error.detail === "object" && error.detail && "detail" in error.detail
      ? (error.detail as { detail?: unknown }).detail
      : error.detail;

    if (detail === "document_not_ready") {
      return { state: "not_ready", message: "Document is still processing. Please wait and retry." };
    }
    if (detail === "question_set_not_ready") {
      return { state: "not_ready", message: "Questions are still generating for this document." };
    }
    if (detail === "document_not_found") {
      return { state: "error", message: "Document not found." };
    }
    if (typeof detail === "string" && detail.trim().length > 0) {
      return { state: "error", message: detail };
    }
  }

  if (error instanceof ApiError && error.status === 429) {
    return { state: "error", message: "Regeneration limit reached (3 times in 24h)." };
  }

  return { state: "error", message: "Failed to load learning path. Please retry." };
};

const nodes = ref<PathNode[]>([]);

const mapOptionToNode = (option: RunPathOption): PathNode => {
  if (mode.value === "endless-abyss") {
    const floor = Number(option.path_id.replace("F", ""));
    const validFloor = Number.isFinite(floor) ? floor : 1;
    return {
      id: option.path_id,
      label: option.label,
      floor: validFloor,
      type: option.kind === "floor" ? "battle" : "checkpoint",
      description: option.description,
      done: option.path_id === "F1",
      pathVersionId: option.path_version_id,
      levelNodeId: option.level_node_id,
    };
  }

  return {
    id: option.path_id,
    label: option.label,
    type: mode.value === "speed-survival" ? "speed" : "draft",
    description: option.description,
    done: option.path_id.endsWith("focus") || option.path_id.endsWith("classic"),
    pathVersionId: option.path_version_id,
    levelNodeId: option.level_node_id,
  };
};

const loadPathOptions = async ({ fromPoll = false }: { fromPoll?: boolean } = {}) => {
  const rawDocumentId = route.query.documentId;
  const documentId = typeof rawDocumentId === "string" ? rawDocumentId : "";
  if (!documentId) {
    clearPollTimer();
    pollAttempts = 0;
    nodes.value = fallbackNodesForMode();
    loadState.value = "ready";
    loadMessage.value = "";
    return;
  }

  if (!fromPoll) {
    clearPollTimer();
    pollAttempts = 0;
    loadState.value = "loading";
    loadMessage.value = "Loading learning path...";
  }

  try {
    const response = await listRunPathOptions(documentId, modeApiMap[mode.value]);

    if (response.generation_status === "generating") {
      nodes.value = [];
      selectedNodeId.value = "";
      loadState.value = "generating";
      loadMessage.value = "Generating learning path...";
      schedulePoll();
      return;
    }

    const mapped = response.options.map(mapOptionToNode);
    clearPollTimer();
    pollAttempts = 0;

    if (!mapped.length) {
      nodes.value = [];
      selectedNodeId.value = "";
      loadState.value = "error";
      loadMessage.value = "No path options generated yet. Please retry.";
      return;
    }

    nodes.value = mapped;
    loadState.value = "ready";
    loadMessage.value = "";
  } catch (error) {
    clearPollTimer();
    nodes.value = [];
    selectedNodeId.value = "";
    const { state, message } = toUserMessage(error);
    loadState.value = state;
    loadMessage.value = message;
  }
};

const triggerRegeneration = async () => {
  const rawDocumentId = route.query.documentId;
  const documentId = typeof rawDocumentId === "string" ? rawDocumentId : "";
  if (!documentId || isRegenerating.value) {
    return;
  }

  isRegenerating.value = true;
  try {
    await regenerateRunPath(documentId, modeApiMap[mode.value]);
    loadState.value = "generating";
    loadMessage.value = "Regenerating learning path...";
    pollAttempts = 0;
    schedulePoll();
  } catch (error) {
    const { state, message } = toUserMessage(error);
    loadState.value = state;
    loadMessage.value = message;
  } finally {
    isRegenerating.value = false;
  }
};

watch(
  [() => mode.value, () => route.query.documentId],
  async () => {
    await loadPathOptions();
  },
  { immediate: true },
);

watch(
  nodes,
  (value) => {
    if (!value.length) {
      selectedNodeId.value = "";
      return;
    }
    if (!value.some((node) => node.id === selectedNodeId.value)) {
      selectedNodeId.value = value[0].id;
    }
  },
  { immediate: true },
);


const selectedNode = computed(() => nodes.value.find((node) => node.id === selectedNodeId.value) ?? null);

onUnmounted(() => {
  clearPollTimer();
});

const hasDocumentId = computed(() => typeof route.query.documentId === "string" && route.query.documentId.length > 0);
const canStart = computed(() => loadState.value === "ready" && !!selectedNode.value);

const pageEyebrow = computed(() =>
  mode.value === "endless-abyss"
    ? flow.value === "review"
      ? "Review Abyss Route"
      : "Begin Abyss Route"
    : flow.value === "review"
      ? "Review Learning Route"
      : "Begin Learning Route",
);

const actionLabel = computed(() => `进入 ${modeLabelMap[mode.value]}`);

const selectedSummary = computed(() => {
  if (loadState.value === "generating") {
    return "Learning path is generating...";
  }
  if (loadState.value === "not_ready" || loadState.value === "error") {
    return loadMessage.value;
  }
  if (!selectedNode.value) {
    return "No route selected";
  }
  if (mode.value === "endless-abyss") {
    return `Selected Floor ${selectedNode.value.floor ?? 1}`;
  }
  return `Selected Route: ${selectedNode.value.description}`;
});

const title = computed(() => {
  const raw = route.query.title;
  return typeof raw === "string" && raw.trim() ? raw : "Scroll Trial";
});

const flow = computed(() => (route.query.flow === "review" ? "review" : "begin"));

const nodeIcon = (type: PathNode["type"]) => {
  if (type === "battle") return "⚔";
  if (type === "study") return "📘";
  if (type === "checkpoint") return "✓";
  if (type === "speed") return "⚡";
  if (type === "draft") return "✎";
  return "♛";
};

const startLearning = async () => {
  if (!selectedNode.value || !canStart.value) {
    return;
  }
  await router.push({
    path: modeRouteMap[mode.value],
    query: {
      ...route.query,
      flow: flow.value,
      mode: mode.value,
      pathId: selectedNode.value.id,
      floor: mode.value === "endless-abyss" ? String(selectedNode.value.floor ?? 1) : undefined,
      pathVersionId: selectedNode.value.pathVersionId,
      levelNodeId: selectedNode.value.levelNodeId,
      title: title.value,
    },
  });
};

const backToModes = async () => {
  await router.push({
    path: ROUTES.gameModes,
    query: {
      ...route.query,
      title: title.value,
    },
  });
};
</script>

<template>
  <main class="path-page">
    <section class="path-shell" aria-label="Dungeon level path selection">
      <header class="path-header">
        <button class="path-back" type="button" @click="backToModes">←</button>
        <div>
          <p class="path-sub">{{ pageEyebrow }}</p>
          <h1>{{ title }}</h1>
        </div>
        <button class="path-guide" type="button">指南</button>
      </header>

      <section class="path-map">
        <div v-if="loadState === 'loading'" class="path-status path-status--loading">Loading path...</div>
        <div v-else-if="loadState === 'generating'" class="path-status path-status--loading">{{ loadMessage }}</div>
        <div v-else-if="loadState === 'not_ready' || loadState === 'error'" class="path-status">
          <p>{{ loadMessage }}</p>
          <div class="path-status__actions">
            <button class="path-secondary" type="button" @click="loadPathOptions()">Retry</button>
            <button
              v-if="hasDocumentId"
              class="path-secondary"
              type="button"
              :disabled="isRegenerating"
              @click="triggerRegeneration"
            >
              {{ isRegenerating ? "Regenerating..." : "Regenerate Path" }}
            </button>
          </div>
        </div>
        <template v-else>
          <button
            v-for="node in nodes"
            :key="node.id"
            class="path-node"
            :class="[
              `path-node--${node.type}`,
              {
                'path-node--done': node.done,
                'path-node--active': selectedNodeId === node.id,
              },
            ]"
            type="button"
            @click="selectedNodeId = node.id"
          >
            <span class="path-node__icon">{{ nodeIcon(node.type) }}</span>
            <span class="path-node__floor">{{ node.label }}</span>
          </button>
        </template>
      </section>

      <footer class="path-actions">
        <p>{{ selectedSummary }}</p>
        <div class="path-actions__right">
          <button
            v-if="hasDocumentId"
            class="path-secondary"
            type="button"
            :disabled="isRegenerating"
            @click="triggerRegeneration"
          >
            {{ isRegenerating ? "Regenerating..." : "Regenerate Path" }}
          </button>
          <button class="path-start" type="button" :disabled="!canStart" @click="startLearning">
            {{ actionLabel }}
          </button>
        </div>
      </footer>
    </section>
  </main>
</template>

<style scoped>
.path-page {
  background: var(--color-page-bg);
  min-height: 100vh;
  padding: 24px;
}

.path-shell {
  background: color-mix(in srgb, var(--color-surface) 86%, var(--color-surface-alt) 14%);
  border: 1px solid var(--color-border);
  border-radius: 22px;
  margin: 0 auto;
  max-width: 980px;
  min-height: 740px;
  padding: 22px;
}

.path-header {
  align-items: center;
  background: linear-gradient(90deg, var(--color-primary-500), var(--color-primary-600));
  border-radius: 16px;
  color: var(--color-surface);
  display: grid;
  gap: 14px;
  grid-template-columns: auto 1fr auto;
  padding: 14px 16px;
}

.path-back,
.path-guide {
  background: color-mix(in srgb, var(--color-surface) 16%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-surface) 52%, transparent);
  border-radius: 12px;
  color: var(--color-surface);
  cursor: pointer;
  font-weight: 700;
  min-height: 40px;
  min-width: 40px;
  padding: 0 12px;
}

.path-sub {
  color: color-mix(in srgb, var(--color-surface) 84%, transparent);
  font-size: 13px;
  margin: 0;
}

.path-header h1 {
  font-family: var(--font-serif);
  font-size: 34px;
  margin: 4px 0 0;
}

.path-map {
  align-content: start;
  column-gap: 120px;
  display: grid;
  grid-auto-flow: column;
  grid-template-rows: repeat(3, minmax(0, 1fr));
  justify-content: center;
  margin: 46px auto 0;
  max-width: 560px;
  row-gap: 40px;
}

.path-node {
  align-items: center;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: 999px;
  color: var(--color-text-strong);
  cursor: pointer;
  display: inline-flex;
  flex-direction: column;
  gap: 4px;
  height: 86px;
  justify-content: center;
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
  width: 86px;
}

.path-node:hover {
  transform: translateY(-2px);
}

.path-node--done {
  border-color: var(--color-primary-500);
}

.path-node--active {
  border-color: var(--color-muted-gold);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-muted-gold) 20%, transparent);
}

.path-node__icon {
  font-size: 22px;
}

.path-node__floor {
  font-size: 11px;
  font-weight: 800;
}

.path-actions {
  align-items: center;
  border-top: 1px solid var(--color-border-soft);
  display: flex;
  justify-content: space-between;
  margin-top: 56px;
  padding-top: 18px;
}

.path-actions p {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin: 0;
}

.path-start {
  background: linear-gradient(90deg, var(--color-primary-600), var(--color-primary-500));
  border: 0;
  border-radius: 12px;
  color: var(--color-surface);
  cursor: pointer;
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 700;
  min-height: 44px;
  padding: 0 20px;
}

.path-status {
  align-items: center;
  color: var(--color-text-secondary);
  display: flex;
  flex-direction: column;
  font-size: 14px;
  gap: 12px;
  grid-column: 1 / -1;
  justify-content: center;
  min-height: 220px;
  text-align: center;
}

.path-status--loading {
  color: var(--color-primary-600);
  font-weight: 700;
}

.path-status p {
  margin: 0;
}

.path-status__actions {
  display: flex;
  gap: 10px;
}

.path-actions__right {
  align-items: center;
  display: flex;
  gap: 10px;
}

.path-secondary {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  min-height: 44px;
  padding: 0 16px;
}

.path-start:disabled,
.path-secondary:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

</style>
