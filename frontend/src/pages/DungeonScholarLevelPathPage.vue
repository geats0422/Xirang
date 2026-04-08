<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { ApiError } from "../api/http";
import { ROUTES } from "../constants/routes";
import { listRunPathOptions, type RunPathOption } from "../api/runs";

type PathNode = {
  id: string;
  label: string;
  type: "battle" | "study" | "checkpoint" | "boss" | "speed" | "draft" | "review";
  description: string;
  floor?: number;
  done?: boolean;
};

type ModeId = "endless-abyss" | "speed-survival" | "knowledge-draft" | "review";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const mode = computed<ModeId>(() => {
  const rawMode = route.query.mode;
  if (rawMode === "speed-survival" || rawMode === "knowledge-draft" || rawMode === "review") {
    return rawMode;
  }
  return "endless-abyss";
});

const selectedNodeId = ref<string>("");

const modeRouteMap: Record<ModeId, string> = {
  "endless-abyss": ROUTES.endlessAbyss,
  "speed-survival": ROUTES.speedSurvival,
  "knowledge-draft": ROUTES.knowledgeDraft,
  review: ROUTES.review,
};

const modeApiMap: Record<ModeId, "endless" | "speed" | "draft" | "review"> = {
  "endless-abyss": "endless",
  "speed-survival": "speed",
  "knowledge-draft": "draft",
  review: "review",
};

const modeLabelMap = computed<Record<ModeId, string>>(() => ({
  "endless-abyss": t("levelPath.modeLabel.endlessAbyss"),
  "speed-survival": t("levelPath.modeLabel.speedSurvival"),
  "knowledge-draft": t("levelPath.modeLabel.knowledgeDraft"),
  review: t("levelPath.modeLabel.review"),
}));

const endlessNodes = computed<PathNode[]>(() => [
  { id: "F1", label: "F1", floor: 1, type: "battle", description: t("levelPath.nodeDescription.endless.f1"), done: true },
  { id: "F2", label: "F2", floor: 2, type: "study", description: t("levelPath.nodeDescription.endless.f2"), done: true },
  { id: "F3", label: "F3", floor: 3, type: "checkpoint", description: t("levelPath.nodeDescription.endless.f3") },
  { id: "F4", label: "F4", floor: 4, type: "study", description: t("levelPath.nodeDescription.endless.f4") },
  { id: "F5", label: "F5", floor: 5, type: "battle", description: t("levelPath.nodeDescription.endless.f5") },
  { id: "F6", label: "F6", floor: 6, type: "boss", description: t("levelPath.nodeDescription.endless.f6") },
]);

const speedNodes = computed<PathNode[]>(() => [
  {
    id: "speed-route-focus",
    label: "R1",
    type: "speed",
    description: t("levelPath.nodeDescription.speed.r1"),
    done: true,
  },
  {
    id: "speed-route-burst",
    label: "R2",
    type: "speed",
    description: t("levelPath.nodeDescription.speed.r2"),
  },
  {
    id: "speed-route-endurance",
    label: "R3",
    type: "speed",
    description: t("levelPath.nodeDescription.speed.r3"),
  },
]);

const draftNodes = computed<PathNode[]>(() => [
  {
    id: "draft-route-classic",
    label: "R1",
    type: "draft",
    description: t("levelPath.nodeDescription.draft.r1"),
    done: true,
  },
  {
    id: "draft-route-theory",
    label: "R2",
    type: "draft",
    description: t("levelPath.nodeDescription.draft.r2"),
  },
  {
    id: "draft-route-memory",
    label: "R3",
    type: "draft",
    description: t("levelPath.nodeDescription.draft.r3"),
  },
]);

const reviewNodes = computed<PathNode[]>(() => [
  {
    id: "review-stage-1",
    label: "R1",
    type: "review",
    description: t("levelPath.nodeDescription.review.r1"),
    done: true,
  },
  {
    id: "review-stage-2",
    label: "R2",
    type: "review",
    description: t("levelPath.nodeDescription.review.r2"),
  },
  {
    id: "review-stage-3",
    label: "R3",
    type: "review",
    description: t("levelPath.nodeDescription.review.r3"),
  },
]);

const fallbackNodes = computed<PathNode[]>(() => {
  if (mode.value === "endless-abyss") {
    return endlessNodes.value;
  }
  if (mode.value === "speed-survival") {
    return speedNodes.value;
  }
  if (mode.value === "knowledge-draft") {
    return draftNodes.value;
  }
  return reviewNodes.value;
});

const nodes = ref<PathNode[]>([]);

const noRoutesMessage = computed(() => {
  if (mode.value === "review") {
    return t("levelPath.reviewNoQuestions");
  }
  return t("levelPath.noRouteSelected");
});

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
    };
  }

  return {
    id: option.path_id,
    label: option.label,
    type:
      mode.value === "speed-survival"
        ? "speed"
        : mode.value === "knowledge-draft"
          ? "draft"
          : "review",
    description: option.description,
    done:
      option.path_id.endsWith("focus") ||
      option.path_id.endsWith("classic") ||
      option.path_id.endsWith("1"),
  };
};

const loadPathOptions = async () => {
  const rawDocumentId = route.query.documentId;
  const documentId = typeof rawDocumentId === "string" ? rawDocumentId : undefined;
  if (!documentId && mode.value !== "review") {
    nodes.value = fallbackNodes.value;
    return;
  }

  try {
    const response = await listRunPathOptions(documentId, modeApiMap[mode.value]);
    const mapped = response.options.map(mapOptionToNode);
    if (mode.value === "review") {
      nodes.value = mapped;
      return;
    }
    nodes.value = mapped.length ? mapped : fallbackNodes.value;
  } catch (error) {
    if (mode.value === "review" && error instanceof ApiError && error.status === 409) {
      nodes.value = [];
      return;
    }
    nodes.value = mode.value === "review" ? [] : fallbackNodes.value;
  }
};

watch(
  () => mode.value,
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

onMounted(async () => {
  await loadPathOptions();
});

const selectedNode = computed(() => nodes.value.find((node) => node.id === selectedNodeId.value) ?? null);

const pageEyebrow = computed(() => {
  if (mode.value === "review") {
    return flow.value === "review"
      ? t("levelPath.pageEyebrow.reviewMode")
      : t("levelPath.pageEyebrow.beginReviewMode");
  }

  if (flow.value === "review") {
    return mode.value === "endless-abyss"
      ? t("levelPath.pageEyebrow.reviewAbyss")
      : t("levelPath.pageEyebrow.reviewLearning");
  }
  return mode.value === "endless-abyss"
    ? t("levelPath.pageEyebrow.beginAbyss")
    : t("levelPath.pageEyebrow.beginLearning");
});

const actionLabel = computed(() => t("levelPath.enterAction", { mode: modeLabelMap.value[mode.value] }));

const guideLabel = computed(() => t("levelPath.guide"));
const backLabel = computed(() => t("levelPath.back"));
const pathSelectionAriaLabel = computed(() => t("levelPath.selectionAria"));

const selectedSummary = computed(() => {
  if (!selectedNode.value) {
    return t("levelPath.noRouteSelected");
  }

  const description = selectedNode.value.description.trim();

  if (mode.value === "endless-abyss") {
    return description
      ? t("levelPath.selectedSummary.floorWithDesc", {
          floor: selectedNode.value.floor ?? 1,
          description,
        })
      : t("levelPath.selectedSummary.floor", {
          floor: selectedNode.value.floor ?? 1,
        });
  }

  return description
    ? t("levelPath.selectedSummary.routeWithDesc", {
        route: selectedNode.value.label,
        description,
      })
    : t("levelPath.selectedSummary.route", {
        route: selectedNode.value.label,
      });
});

const title = computed(() => {
  const raw = route.query.title;
  return typeof raw === "string" && raw.trim() ? raw : t("levelPath.defaultTitle");
});

const flow = computed(() => (route.query.flow === "review" ? "review" : "begin"));

const nodeIcon = (type: PathNode["type"]) => {
  if (type === "battle") return "⚔";
  if (type === "study") return "📘";
  if (type === "checkpoint") return "✓";
  if (type === "speed") return "⚡";
  if (type === "draft") return "✎";
  if (type === "review") return "↺";
  return "♛";
};

const startLearning = async () => {
  if (!selectedNode.value) {
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
    <section class="path-shell" :aria-label="pathSelectionAriaLabel">
      <header class="path-header">
        <button class="path-back" type="button" :aria-label="backLabel" @click="backToModes">
          <span aria-hidden="true">←</span>
          <span class="path-back__label">{{ backLabel }}</span>
        </button>
        <div>
          <p class="path-sub">{{ pageEyebrow }}</p>
          <h1>{{ title }}</h1>
        </div>
        <button class="path-guide" type="button">{{ guideLabel }}</button>
      </header>

      <section class="path-map">
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
      </section>

      <p v-if="!nodes.length" class="path-empty">{{ noRoutesMessage }}</p>

      <footer class="path-actions">
        <p>{{ selectedSummary }}</p>
        <button class="path-start" type="button" :disabled="!selectedNode" @click="startLearning">{{ actionLabel }}</button>
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

.path-back {
  align-items: center;
  display: inline-flex;
  gap: 6px;
}

.path-back__label {
  font-size: 13px;
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

.path-empty {
  color: var(--color-text-muted);
  margin: 28px 0 0;
  text-align: center;
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

.path-start:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
