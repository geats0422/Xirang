<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import DocumentDeleteConfirmModal from "../components/documents/DocumentDeleteConfirmModal.vue";
import AppSidebar from "../components/layout/AppSidebar.vue";
import NotificationPopover from "../components/NotificationPopover.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";
import { useScholarData } from "../composables/useScholarData";

const { t, locale } = useI18n();

type UploadState = "idle" | "loading" | "success" | "failure";
type HomeDocumentStatus = "ready" | "processing" | "failed";

type HomeDocumentCard = {
  id: string;
  title: string;
  createdAt: string;
  lastVisited: string;
  progress: number;
  icon: string;
  status: HomeDocumentStatus;
  actionLabel: string;
};

type NotificationItem = {
  id: string;
  title: string;
  time: string;
};

const getDocIcon = (): string => "📖";

const normalizeHomeDocumentStatus = (status: string | undefined): HomeDocumentStatus => {
  if (status === "ready" || status === "failed") {
    return status;
  }
  return "processing";
};

const {
  profileName,
  profileLevel,
  streak,
  coins,
  documents: scholarDocs,
  uploadAndRefresh,
  deleteAndRefresh,
  deleteManyAndRefresh,
  hydrate,
} = useScholarData();

const documents = ref<HomeDocumentCard[]>([]);
const isLoading = ref(false);

const fetchDocuments = async () => {
  isLoading.value = true;
  try {
    const sortedRecentDocs = [...scholarDocs.value]
      .sort((left, right) => {
        const leftTime = Date.parse(left.created_at ?? "") || 0;
        const rightTime = Date.parse(right.created_at ?? "") || 0;
        return rightTime - leftTime;
      })
      .slice(0, 9);

    documents.value = sortedRecentDocs.map((doc) => {
      const status = normalizeHomeDocumentStatus(doc.status);
      const actionLabel = status === "ready"
        ? "Begin Study"
        : status === "failed"
          ? "Go to Library"
          : "Processing...";

      return {
        id: doc.id,
        title: doc.title,
        createdAt: doc.created_at ?? "",
        lastVisited: "Just now",
        progress: 0,
        icon: getDocIcon(),
        status,
        actionLabel,
      };
    });
  } catch (error) {
    console.error("Failed to fetch documents:", error);
    documents.value = [];
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  await hydrate();
  await fetchDocuments();
});

// Update document title reactively when locale changes
watch(locale, () => {
  document.title = t("home.metaTitle");
});

const shopRoute = ROUTES.shop;

const { currentPath, navigateTo, router, routingTarget } = useRouteNavigation();

const uploadState = ref<UploadState>("idle");
const isDragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const notificationVisible = ref(false);
const notifications = ref<NotificationItem[]>([]);
const activeCardMenuId = ref<string | null>(null);
const pendingDeleteCard = ref<HomeDocumentCard | null>(null);
const pendingBatchDeleteIds = ref<string[]>([]);
const isDeleting = ref(false);
const isBatchDeleteMode = ref(false);
const selectedDocumentIds = ref<string[]>([]);

const selectedCount = computed(() => selectedDocumentIds.value.length);
const cardNotice = ref<string | null>(null);

const openHomeDocument = async (card: HomeDocumentCard) => {
  if (card.status === "processing") {
    cardNotice.value = "This document is still processing. Please wait.";
    return;
  }

  if (card.status === "failed") {
    cardNotice.value = "Document parsing failed. Please retry from Library.";
    await navigateTo(ROUTES.library);
    return;
  }

  cardNotice.value = null;
  await router.push({
    path: ROUTES.gameModes,
    query: {
      flow: "begin",
      documentId: card.id,
      title: card.title,
      format: "SCROLL",
    },
  });
};

const handleBrowseClick = () => {
  fileInput.value?.click();
};

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  if (!files || files.length === 0) return;

  uploadState.value = "loading";
  try {
    await uploadAndRefresh(files);
    uploadState.value = "success";
    await fetchDocuments();
  } catch {
    uploadState.value = "failure";
  }
  target.value = "";
};

const handleDragOver = (event: DragEvent) => {
  event.preventDefault();
  isDragging.value = true;
};

const handleDragLeave = () => {
  isDragging.value = false;
};

const handleDrop = async (event: DragEvent) => {
  event.preventDefault();
  isDragging.value = false;
  const files = event.dataTransfer?.files;
  if (!files || files.length === 0) return;

  uploadState.value = "loading";
  try {
    await uploadAndRefresh(files);
    uploadState.value = "success";
    await fetchDocuments();
  } catch {
    uploadState.value = "failure";
  }
};

const handleRetry = () => {
  uploadState.value = "idle";
};

const setUploadFailure = () => {
  uploadState.value = "failure";
};

const toggleNotifications = () => {
  notificationVisible.value = !notificationVisible.value;
};

const closeNotifications = () => {
  notificationVisible.value = false;
};

const toggleCardMenu = (documentId: string) => {
  if (isBatchDeleteMode.value) {
    return;
  }
  activeCardMenuId.value = activeCardMenuId.value === documentId ? null : documentId;
};

const requestDelete = (card: HomeDocumentCard) => {
  activeCardMenuId.value = null;
  pendingDeleteCard.value = card;
};

const closeDeleteModal = () => {
  pendingBatchDeleteIds.value = [];
  pendingDeleteCard.value = null;
};

const confirmDelete = async () => {
  const singleDeleteId = pendingDeleteCard.value?.id;
  const batchDeleteIds = pendingBatchDeleteIds.value;
  if (!singleDeleteId && batchDeleteIds.length === 0) {
    return;
  }

  isDeleting.value = true;
  try {
    if (batchDeleteIds.length > 0) {
      await deleteManyAndRefresh(batchDeleteIds);
      selectedDocumentIds.value = [];
      isBatchDeleteMode.value = false;
    } else if (singleDeleteId) {
      await deleteAndRefresh(singleDeleteId);
    }
    await fetchDocuments();
    closeDeleteModal();
  } catch {
    closeDeleteModal();
  } finally {
    isDeleting.value = false;
  }
};

const toggleBatchDeleteMode = () => {
  activeCardMenuId.value = null;
  pendingDeleteCard.value = null;
  pendingBatchDeleteIds.value = [];
  isBatchDeleteMode.value = !isBatchDeleteMode.value;
  if (!isBatchDeleteMode.value) {
    selectedDocumentIds.value = [];
  }
};

const toggleDocumentSelection = (documentId: string) => {
  if (!isBatchDeleteMode.value) {
    return;
  }
  if (selectedDocumentIds.value.includes(documentId)) {
    selectedDocumentIds.value = selectedDocumentIds.value.filter((item) => item !== documentId);
    return;
  }
  selectedDocumentIds.value = [...selectedDocumentIds.value, documentId];
};

const openBatchDeleteConfirm = () => {
  if (selectedDocumentIds.value.length === 0) {
    return;
  }
  pendingDeleteCard.value = null;
  pendingBatchDeleteIds.value = [...selectedDocumentIds.value];
};

defineExpose({
  uploadState,
  documents,
  isLoading,
  setUploadFailure,
});
</script>

<template>
  <div class="home-page">
    <AppSidebar
      :current-path="currentPath"
      :routing-target="routingTarget"
      :profile-name="profileName"
      :profile-level="profileLevel"
      @navigate="navigateTo"
    />

    <main class="main-content">
      <header class="status-bar" :aria-label="$t('home.statusBarAria')">
        <div class="status-pill status-pill--streak">🔥 {{ $t("home.streakLabel", { days: streak }) }}</div>
        <button class="status-pill status-pill--coin" type="button" @click="navigateTo(shopRoute)">
          🪙 {{ $t("home.coinLabel", { amount: coins }) }}
        </button>
        <button class="status-notify" type="button" :aria-label="$t('home.notifications')" @click="toggleNotifications">🔔</button>
      </header>

      <NotificationPopover :items="notifications" :visible="notificationVisible" @close="closeNotifications" />

      <section
        class="hero-upload"
        :class="{
          'hero-upload--idle': uploadState === 'idle',
          'hero-upload--loading': uploadState === 'loading',
          'hero-upload--success': uploadState === 'success',
          'hero-upload--failure': uploadState === 'failure',
          'hero-upload--dragging': isDragging,
        }"
        :aria-label="$t('home.uploadAria')"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @drop="handleDrop"
        @click="uploadState === 'idle' && handleBrowseClick()"
      >
        <div class="hero-upload__mascot" aria-hidden="true">
          <img src="/taotie-main.svg" alt="" />
        </div>

        <p class="hero-upload__disclaimer">
          <span class="hero-upload__beta-tag">BETA</span>
          {{ $t("home.uploadDisclaimer") }}
        </p>

        <template v-if="uploadState === 'idle'">
          <h1>{{ $t("home.idleTitle") }}</h1>
          <p>{{ $t("home.idleDesc") }}</p>
          <input
            ref="fileInput"
            type="file"
            accept=".pdf,.txt,.md,.markdown,.doc,.docx,.ppt,.pptx"
            multiple
            class="hero-upload__file-input"
            @change="handleFileSelect"
          />
          <button class="browse-btn" type="button" @click.stop="handleBrowseClick">
            ☁ {{ $t("home.browseScrolls") }}
          </button>
          <span class="support-text">{{ $t("home.supportText") }}</span>
        </template>

        <template v-else-if="uploadState === 'loading'">
          <h1>{{ $t("home.loadingTitle") }}</h1>
          <p>{{ $t("home.loadingDesc") }}</p>
          <div class="hero-upload__spinner" :aria-label="$t('home.loadingAria')" />
        </template>

        <template v-else-if="uploadState === 'success'">
          <h1>{{ $t("home.successTitle") }}</h1>
          <p>{{ $t("home.successDesc") }}</p>
          <button class="browse-btn browse-btn--success" type="button" @click.stop="uploadState = 'idle'">
            ✓ {{ $t("home.successAction") }}
          </button>
        </template>

        <template v-else-if="uploadState === 'failure'">
          <h1>{{ $t("home.failureTitle") }}</h1>
          <p>{{ $t("home.failureDesc") }}</p>
          <button class="browse-btn hero-upload__retry" type="button" @click.stop="handleRetry">
            ↻ {{ $t("home.retryUpload") }}
          </button>
        </template>
      </section>

      <section class="recent-section" :aria-label="$t('home.recentAria')">
        <div class="recent-section__head">
          <h2>{{ $t("home.recentTitle") }}</h2>
          <div class="recent-section__actions">
            <button class="recent-section__batch-btn" type="button" @click="toggleBatchDeleteMode">
              {{ isBatchDeleteMode ? "Cancel Batch" : "Batch Delete" }}
            </button>
            <button
              v-if="isBatchDeleteMode"
              class="recent-section__batch-btn recent-section__batch-btn--danger"
              type="button"
              :disabled="selectedCount === 0"
              @click="openBatchDeleteConfirm"
            >
              Delete Selected ({{ selectedCount }})
            </button>
            <a href="#">{{ $t("home.viewAll") }}</a>
          </div>
        </div>

        <p v-if="cardNotice" class="recent-section__notice">{{ cardNotice }}</p>

        <div class="dungeon-grid">
          <article v-for="card in documents" :key="card.id" class="dungeon-card">
            <div class="dungeon-card__head" :class="{ 'dungeon-card__head--batch': isBatchDeleteMode }">
              <span class="dungeon-card__icon">{{ card.icon }}</span>
              <label v-if="isBatchDeleteMode" class="dungeon-card__check-wrap">
                <input
                  type="checkbox"
                  class="dungeon-card__check batch-select-checkbox"
                  :checked="selectedDocumentIds.includes(card.id)"
                  @change="toggleDocumentSelection(card.id)"
                />
              </label>
              <div class="dungeon-card__menu-wrap">
                <button
                  v-if="!isBatchDeleteMode"
                  class="dungeon-card__menu"
                  type="button"
                  :aria-label="$t('home.moreOptions')"
                  @click.stop="toggleCardMenu(card.id)"
                >
                  ⋯
                </button>
                <div v-if="activeCardMenuId === card.id" class="dungeon-card__menu-popover">
                  <button class="dungeon-card__menu-action dungeon-card__menu-action--danger" type="button" @click="requestDelete(card)">
                    Delete
                  </button>
                </div>
              </div>
            </div>
            <h3>{{ card.title }}</h3>
            <p>{{ $t("home.lastVisitedPrefix") }} {{ card.lastVisited }}</p>
            <span class="dungeon-card__status" :class="`dungeon-card__status--${card.status}`">{{ card.status }}</span>
            <div class="dungeon-card__progress">
              <div class="progress-track" role="presentation">
                <span class="progress-fill" :style="{ width: `${card.progress}%` }" />
              </div>
              <strong>{{ card.progress }}%</strong>
            </div>
            <button
              class="dungeon-card__action"
              :class="`dungeon-card__action--${card.status}`"
              type="button"
              @click="openHomeDocument(card)"
            >
              {{ card.actionLabel }}
            </button>
          </article>
        </div>
      </section>

      <DocumentDeleteConfirmModal
        :visible="Boolean(pendingDeleteCard) || pendingBatchDeleteIds.length > 0"
        :title="pendingDeleteCard?.title || ''"
        :message="pendingBatchDeleteIds.length > 0 ? `Are you sure you want to delete ${pendingBatchDeleteIds.length} selected documents?` : ''"
        :processing="isDeleting"
        @cancel="closeDeleteModal"
        @confirm="confirmDelete"
      />
    </main>
  </div>
</template>

<style scoped>
.home-page {
  display: grid;
  gap: 24px;
  grid-template-columns: 256px minmax(0, 1fr);
  min-height: 100vh;
  padding: 24px;
}

.main-content {
  display: flex;
  flex-direction: column;
}

.status-bar {
  align-items: center;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.status-pill {
  border: 0;
  border-radius: var(--radius-pill);
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 14px;
}

.status-pill--streak {
  background: #ffedd5;
  color: #9a3412;
}

.status-pill--coin {
  background: #fef3c7;
  color: #92400e;
  cursor: pointer;
}

.status-notify {
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  cursor: pointer;
  height: 34px;
  width: 34px;
}

.hero-upload {
  align-items: center;
  background: var(--color-surface);
  border: 2px dashed #b9d8dc;
  border-radius: 22px;
  display: flex;
  flex-direction: column;
  margin-top: 18px;
  min-height: 340px;
  padding: 32px 24px;
  text-align: center;
}

.hero-upload__mascot {
  align-items: center;
  display: flex;
  justify-content: center;
  margin-bottom: 6px;
}

.hero-upload__mascot img {
  display: block;
  height: auto;
  max-width: min(240px, 28vw);
  width: clamp(150px, 18vw, 220px);
}

.hero-upload h1 {
  font-family: var(--font-serif);
  font-size: clamp(38px, 5vw, 52px);
  line-height: 1.05;
  margin: 12px 0 0;
}

.hero-upload p {
  color: var(--color-text-secondary);
  font-size: 16px;
  line-height: 1.7;
  margin: 14px 0 0;
  max-width: 720px;
}

.browse-btn {
  align-items: center;
  background: #f4fbfb;
  border: 1px solid #b9d8dc;
  border-radius: 999px;
  color: var(--color-deep-teal);
  cursor: pointer;
  display: inline-flex;
  font-family: var(--font-serif);
  font-size: 15px;
  font-weight: 700;
  gap: 8px;
  margin-top: 20px;
  min-height: 44px;
  padding: 0 20px;
}

.support-text {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-top: 12px;
}

.hero-upload__disclaimer {
  background: #fef9e7;
  border: 1px solid #f5e6a3;
  border-radius: 8px;
  color: #8a6d1b;
  font-size: 12px;
  margin: 0 0 12px;
  padding: 8px 14px;
}

.hero-upload__beta-tag {
  background: #f0ad4e;
  border-radius: 4px;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-right: 6px;
  padding: 2px 6px;
}

.hero-upload--loading {
  border-color: #a0d2db;
}

.hero-upload--success {
  border-color: #6ecf9c;
  border-style: solid;
}

.hero-upload--failure {
  border-color: #e8a0a0;
  border-style: solid;
}

.hero-upload--dragging {
  border-color: #1f9aa4;
  border-style: solid;
  background: #f0fafa;
}

.hero-upload__file-input {
  display: none;
}

.hero-upload__spinner {
  animation: spin 1s linear infinite;
  border: 3px solid #e0f0f0;
  border-top-color: #1f9aa4;
  border-radius: 50%;
  height: 40px;
  margin-top: 20px;
  width: 40px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.browse-btn--success {
  background: #e8f8f0;
  border-color: #6ecf9c;
  color: #22863a;
}

.recent-section {
  margin-top: 22px;
}

.recent-section__notice {
  background: var(--color-chip-gold-bg);
  border: 1px solid var(--color-muted-gold);
  border-radius: 8px;
  color: var(--color-chip-gold-text);
  font-size: 13px;
  margin: 10px 0 0;
  padding: 10px 12px;
}

.recent-section__head {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.recent-section__actions {
  align-items: center;
  display: flex;
  gap: 10px;
}

.recent-section__batch-btn {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  color: #334155;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  min-height: 34px;
  padding: 0 12px;
}

.recent-section__batch-btn--danger {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #b91c1c;
}

.recent-section__batch-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.recent-section__head h2 {
  font-family: var(--font-serif);
  font-size: 34px;
  line-height: 1.1;
  margin: 0;
}

.recent-section__head a {
  color: var(--color-primary-600);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
}

.dungeon-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 14px;
}

.dungeon-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 14px;
}

.dungeon-card__head {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.dungeon-card__head--batch .dungeon-card__menu-wrap {
  display: none;
}

.dungeon-card__head--batch .dungeon-card__check-wrap {
  margin-left: auto;
  margin-right: 2px;
}

.dungeon-card__menu-wrap {
  position: relative;
}

.dungeon-card__check-wrap {
  align-items: center;
  display: inline-flex;
  justify-content: center;
}

.dungeon-card__check {
  cursor: pointer;
}

.batch-select-checkbox {
  appearance: none;
  background: var(--color-batch-checkbox-bg);
  border: 1.5px solid var(--color-batch-checkbox-border);
  border-radius: 5px;
  display: grid;
  height: 16px;
  margin: 0;
  place-content: center;
  transition: border-color 120ms ease, background-color 120ms ease, box-shadow 120ms ease;
  width: 16px;
}

.batch-select-checkbox::before {
  border: solid var(--color-batch-checkbox-check);
  border-width: 0 1.5px 1.5px 0;
  content: "";
  height: 7px;
  opacity: 0;
  transform: rotate(45deg);
  transition: opacity 120ms ease;
  width: 4px;
}

.batch-select-checkbox:hover {
  border-color: var(--color-batch-checkbox-border-checked);
}

.batch-select-checkbox:checked {
  background: var(--color-batch-checkbox-bg-checked);
  border-color: var(--color-batch-checkbox-border-checked);
}

.batch-select-checkbox:checked::before {
  opacity: 1;
}

.batch-select-checkbox:focus-visible {
  box-shadow: 0 0 0 3px var(--color-batch-checkbox-shadow-focus);
  outline: none;
}

.dungeon-card__icon {
  align-items: center;
  background: #f2f8f8;
  border-radius: 10px;
  display: inline-flex;
  font-size: 20px;
  height: 36px;
  justify-content: center;
  width: 36px;
}

.dungeon-card__menu {
  background: transparent;
  border: 0;
  color: #94a3b8;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
  padding: 0;
}

.dungeon-card__menu-popover {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.14);
  padding: 6px;
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  z-index: 20;
}

.dungeon-card__menu-action {
  background: transparent;
  border: 0;
  border-radius: 6px;
  color: #1e293b;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  padding: 8px 10px;
}

.dungeon-card__menu-action--danger {
  color: #dc2626;
}

.dungeon-card h3 {
  font-family: var(--font-serif);
  font-size: 22px;
  line-height: 1.2;
  margin: 14px 0 0;
}

.dungeon-card p {
  color: var(--color-text-muted);
  font-size: 13px;
  margin: 8px 0 0;
}

.dungeon-card__status {
  align-self: flex-start;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  margin-top: 10px;
  padding: 4px 10px;
  text-transform: capitalize;
}

.dungeon-card__status--ready {
  background: color-mix(in srgb, var(--color-status-done) 14%, transparent);
  color: var(--color-status-done);
}

.dungeon-card__status--processing {
  background: color-mix(in srgb, var(--color-primary-500) 12%, transparent);
  color: var(--color-primary-600);
}

.dungeon-card__status--failed {
  background: color-mix(in srgb, var(--color-danger-title) 12%, transparent);
  color: var(--color-danger-title);
}

.dungeon-card__progress {
  align-items: center;
  display: grid;
  gap: 10px;
  grid-template-columns: minmax(0, 1fr) auto;
  margin-top: 14px;
}

.progress-track {
  background: #edf2f7;
  border-radius: 999px;
  height: 8px;
  overflow: hidden;
}

.progress-fill {
  background: linear-gradient(90deg, var(--color-primary-500), #14b8a6);
  display: block;
  height: 100%;
}

.dungeon-card__progress strong {
  color: #475569;
  font-size: 13px;
}

.dungeon-card__action {
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  margin-top: 12px;
  min-height: 36px;
}

.dungeon-card__action--ready {
  background: var(--color-primary-50);
  border-color: var(--color-primary-100);
  color: var(--color-primary-600);
}

.dungeon-card__action--processing {
  background: var(--color-border-soft);
  color: var(--color-text-muted);
}

.dungeon-card__action--failed {
  background: color-mix(in srgb, var(--color-danger-surface) 80%, transparent);
  border-color: var(--color-danger-border);
  color: var(--color-danger-title);
}

@media (max-width: 1080px) {
  .home-page {
    grid-template-columns: 1fr;
  }

  .dungeon-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .home-page {
    padding: 14px;
  }

  .main-content {
    order: -1;
  }

  .status-bar {
    justify-content: flex-start;
  }

  .hero-upload {
    min-height: 300px;
    padding: 26px 16px;
  }

  .hero-upload h1 {
    font-size: clamp(34px, 9vw, 42px);
  }

  .recent-section__head h2 {
    font-size: 28px;
  }

  .dungeon-grid {
    grid-template-columns: 1fr;
  }
}
</style>
