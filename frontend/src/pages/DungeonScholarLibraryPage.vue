<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import DocumentDeleteConfirmModal from "../components/documents/DocumentDeleteConfirmModal.vue";
import AppSidebar from "../components/layout/AppSidebar.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";
import { useScholarData } from "../composables/useScholarData";
import {
  batchDeleteDocuments,
  deleteDocument,
  getDocumentProgress,
  listDocuments,
  retryDocument,
  type DocumentListItem,
  type DocumentProgressResponse,
} from "../api/documents";
import { listMistakes } from "../api/mistakes";

const { t, locale } = useI18n();

type ScrollCard = {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
  format: string;
  size: string;
  progressLabel: string;
  progressValue: string;
  progress: number;
  action: "continue" | "begin" | "review" | "retry";
  tone: "teal" | "gold" | "muted";
  accent?: "gold" | "selected";
  mastered?: boolean;
  disabled?: boolean;
};

type UploadState = "idle" | "loading" | "success" | "failure";

const documents = ref<DocumentListItem[]>([]);
const isLoading = ref(true);
const progressMap = ref<Record<string, DocumentProgressResponse>>({});
const mistakeCount = ref(0);
let progressPollingInterval: ReturnType<typeof setInterval> | null = null;

// Search and filter state
const searchQuery = ref("");
const sortBy = ref<"newest" | "oldest" | "name" | "progress">("newest");
const isFilterDropdownOpen = ref(false);

const { profileName, profileLevel, uploadAndRefresh, hydrate } = useScholarData();

const uploadModalVisible = ref(false);
const uploadState = ref<UploadState>("idle");
const isDragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

onMounted(async () => {
  await Promise.all([hydrate(), loadDocuments(), loadMistakeCount()]);
  startProgressPolling();
});

onUnmounted(() => {
  stopProgressPolling();
});

const startProgressPolling = () => {
  stopProgressPolling();
  progressPollingInterval = setInterval(async () => {
    const processingDocs = documents.value.filter((doc) => doc.status === "processing");
    if (processingDocs.length === 0) return;
    await fetchProgressForProcessingDocuments();
  }, 2000);
};

const stopProgressPolling = () => {
  if (progressPollingInterval !== null) {
    clearInterval(progressPollingInterval);
    progressPollingInterval = null;
  }
};

const loadMistakeCount = async () => {
  try {
    const response = await listMistakes();
    mistakeCount.value = response.total;
  } catch {
    mistakeCount.value = 0;
  }
};

// Update document title reactively when locale changes
watch(locale, () => {
  document.title = t("library.metaTitle");
});

const loadDocuments = async () => {
  const timeoutId = setTimeout(() => {
    isLoading.value = false;
  }, 5000);

  try {
    const response = await listDocuments();
    documents.value = [...response].sort((left, right) => {
      const leftTime = Date.parse(left.created_at ?? "") || 0;
      const rightTime = Date.parse(right.created_at ?? "") || 0;
      return rightTime - leftTime;
    });
    // Fetch real progress for processing documents
    await fetchProgressForProcessingDocuments();
  } catch {
    documents.value = [];
  } finally {
    clearTimeout(timeoutId);
    isLoading.value = false;
  }
};

const fetchProgressForProcessingDocuments = async () => {
  const processingDocs = documents.value.filter((doc) => doc.status === "processing");
  if (processingDocs.length === 0) return;

  // Poll progress for each processing document
  await Promise.all(
    processingDocs.map(async (doc) => {
      try {
        const progress = await getDocumentProgress(doc.id);
        progressMap.value[doc.id] = progress;
        // Update local document status if it changed
        if (progress.status !== doc.status) {
          const docIndex = documents.value.findIndex((d) => d.id === doc.id);
          if (docIndex !== -1) {
            documents.value[docIndex] = { ...documents.value[docIndex], status: progress.status };
          }
        }
      } catch {
        // Silently ignore progress fetch errors
      }
    }),
  );
};

const getStatusLabel = (status?: string, stage?: string): string => {
  switch (status) {
    case "ready":
      return t("library.statusReady");
    case "processing":
      return stage ? t("library.statusProcessingWithStage", { stage }) : t("library.statusProcessing");
    case "failed":
      return t("library.statusFailed");
    default:
      return t("library.awaitingSubtitle");
  }
};

const getProgressLabel = (status?: string): string => {
  switch (status) {
    case "ready":
      return t("library.progressReady");
    case "processing":
      return t("library.progressProcessing");
    case "failed":
      return t("library.progressFailed");
    default:
      return t("library.notStarted");
  }
};

const getProgress = (doc: DocumentListItem): number => {
  const progress = progressMap.value[doc.id];
  if (progress) {
    return progress.progress;
  }
  switch (doc.status) {
    case "ready":
      return 100;
    case "processing":
      return 50;
    case "failed":
      return 0;
    default:
      return 0;
  }
};

const getAction = (status?: string): "continue" | "begin" | "review" | "retry" => {
  switch (status) {
    case "ready":
      return "begin";
    case "failed":
      return "retry";
    case "processing":
    default:
      return "continue";
  }
};

const isDisabled = (status?: string): boolean => {
  return status !== "ready" && status !== "failed";
};

const getDocumentFormat = (fileName: string): string => {
  const ext = fileName.split(".").pop()?.toLowerCase() ?? "";
  const formatMap: Record<string, string> = {
    pdf: "PDF",
    doc: "DOC",
    docx: "DOCX",
    ppt: "PPT",
    pptx: "PPTX",
    txt: "TXT",
    md: "MD",
    markdown: "MD",
  };
  return formatMap[ext] ?? ext.toUpperCase();
};

const getScrollCards = (): ScrollCard[] => {
  let filtered = [...documents.value];

  // Apply search filter
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim();
    filtered = filtered.filter((doc) => doc.title.toLowerCase().includes(query));
  }

  // Apply sorting
  filtered.sort((left, right) => {
    switch (sortBy.value) {
      case "oldest": {
        const leftTime = Date.parse(left.created_at ?? "") || 0;
        const rightTime = Date.parse(right.created_at ?? "") || 0;
        return leftTime - rightTime;
      }
      case "name":
        return left.title.localeCompare(right.title, "zh-CN");
      case "progress": {
        const leftProgress = getProgress(left);
        const rightProgress = getProgress(right);
        return rightProgress - leftProgress;
      }
      case "newest":
      default: {
        const leftTime = Date.parse(left.created_at ?? "") || 0;
        const rightTime = Date.parse(right.created_at ?? "") || 0;
        return rightTime - leftTime;
      }
    }
  });

  return filtered.map((doc) => {
    const progress = progressMap.value[doc.id];
    return {
      id: doc.id,
      title: doc.title,
      subtitle: getStatusLabel(doc.status, progress?.stage),
      icon: "📖",
      format: getDocumentFormat(doc.title),
      size: "",
      progressLabel: getProgressLabel(doc.status),
      progressValue: progress ? `${progress.progress}%` : "0%",
      progress: getProgress(doc),
      action: getAction(doc.status),
      disabled: isDisabled(doc.status),
      tone: "muted" as const,
    };
  });
};

const toggleFilterDropdown = () => {
  isFilterDropdownOpen.value = !isFilterDropdownOpen.value;
};

const setSortBy = (sort: "newest" | "oldest" | "name" | "progress") => {
  sortBy.value = sort;
  isFilterDropdownOpen.value = false;
};

const getSortLabel = (): string => {
  switch (sortBy.value) {
    case "oldest":
      return t("library.sortOldest");
    case "name":
      return t("library.sortName");
    case "progress":
      return t("library.sortProgress");
    case "newest":
    default:
      return t("library.sortNewest");
  }
};

const { currentPath, navigateTo, router, routingTarget } = useRouteNavigation();

const openingCard = ref<string | null>(null);
const activeCardMenuId = ref<string | null>(null);
const pendingDeleteCard = ref<ScrollCard | null>(null);
const pendingBatchDeleteIds = ref<string[]>([]);
const isDeleting = ref(false);
const isBatchDeleteMode = ref(false);
const selectedDocumentIds = ref<string[]>([]);

const selectedCount = computed(() => selectedDocumentIds.value.length);

const openModeSelection = async (card: ScrollCard) => {
  if (card.action === "continue" || card.disabled) {
    return;
  }

  openingCard.value = card.title;

  await router.push({
    path: ROUTES.gameModes,
    query: {
      flow: card.action,
      documentId: card.id,
      title: card.title,
      subtitle: card.subtitle,
      format: card.format,
    },
  });

  window.setTimeout(() => {
    if (openingCard.value === card.title) {
      openingCard.value = null;
    }
  }, 220);
};

const handleCardAction = async (card: ScrollCard) => {
  if (card.action === "retry") {
    await handleRetryDocument(card);
  } else {
    await openModeSelection(card);
  }
};

const handleRetryDocument = async (card: ScrollCard) => {
  openingCard.value = card.title;
  try {
    await retryDocument(card.id);
    // Refresh document list to show updated status
    await loadDocuments();
  } catch (error) {
    console.error("Failed to retry document:", error);
  } finally {
    window.setTimeout(() => {
      if (openingCard.value === card.title) {
        openingCard.value = null;
      }
    }, 220);
  }
};

const openMistakeReview = async () => {
  await router.push({
    path: ROUTES.levelPath,
    query: {
      flow: "review",
      mode: "review",
      title: t("library.mistakeReviewTitle"),
      subtitle: t("library.mistakeReviewSubtitle"),
      mistakeReview: "true",
    },
  });
};

const openUploadModal = () => {
  uploadModalVisible.value = true;
  uploadState.value = "idle";
};

const closeUploadModal = () => {
  uploadModalVisible.value = false;
  uploadState.value = "idle";
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
    await loadDocuments();
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
    await loadDocuments();
  } catch {
    uploadState.value = "failure";
  }
};

const handleRetry = () => {
  uploadState.value = "idle";
};

const toggleCardMenu = (cardId: string) => {
  if (isBatchDeleteMode.value) {
    return;
  }
  activeCardMenuId.value = activeCardMenuId.value === cardId ? null : cardId;
};

const requestDelete = (card: ScrollCard) => {
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
      await batchDeleteDocuments(batchDeleteIds);
      selectedDocumentIds.value = [];
      isBatchDeleteMode.value = false;
    } else if (singleDeleteId) {
      await deleteDocument(singleDeleteId);
    }
    await loadDocuments();
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
  openUploadModal,
});
</script>

<template>
  <div class="library-page">
    <AppSidebar
      :current-path="currentPath"
      :routing-target="routingTarget"
      :profile-name="profileName"
      :profile-level="profileLevel"
      @navigate="navigateTo"
    />

    <main class="library-main">
      <section class="library-toolbar" :aria-label="t('library.controlsAria')">
        <label class="search-box">
          <span class="search-box__icon" aria-hidden="true">⌕</span>
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="t('library.searchPlaceholder')"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="search-box__clear"
            :aria-label="t('library.clearSearch')"
            @click="searchQuery = ''"
          >
            ✕
          </button>
        </label>

        <div class="filter-dropdown-wrapper">
          <button class="sort-btn" type="button" @click="toggleFilterDropdown">
            <span class="sort-btn__label">{{ t("library.sortBy") }}</span>
            <span class="sort-btn__value">{{ getSortLabel() }}</span>
            <span class="sort-btn__caret" aria-hidden="true">▾</span>
          </button>

          <div v-if="isFilterDropdownOpen" class="filter-dropdown">
            <div class="filter-dropdown__section">
              <p class="filter-dropdown__title">{{ t("library.sortBy") }}</p>
              <button
                class="filter-dropdown__item"
                :class="{ 'filter-dropdown__item--active': sortBy === 'newest' }"
                @click="setSortBy('newest')"
              >
                {{ t("library.sortNewest") }}
              </button>
              <button
                class="filter-dropdown__item"
                :class="{ 'filter-dropdown__item--active': sortBy === 'oldest' }"
                @click="setSortBy('oldest')"
              >
                {{ t("library.sortOldest") }}
              </button>
              <button
                class="filter-dropdown__item"
                :class="{ 'filter-dropdown__item--active': sortBy === 'name' }"
                @click="setSortBy('name')"
              >
                {{ t("library.sortName") }}
              </button>
              <button
                class="filter-dropdown__item"
                :class="{ 'filter-dropdown__item--active': sortBy === 'progress' }"
                @click="setSortBy('progress')"
              >
                {{ t("library.sortProgress") }}
              </button>
            </div>
          </div>
        </div>

        <button class="sort-btn" type="button" @click="toggleBatchDeleteMode">
          {{ isBatchDeleteMode ? t("library.cancelBatch") : t("library.batchDelete") }}
        </button>

        <button
          v-if="isBatchDeleteMode"
          class="sort-btn sort-btn--danger"
          type="button"
          :disabled="selectedCount === 0"
          @click="openBatchDeleteConfirm"
        >
          {{ t("library.deleteSelected", { count: selectedCount }) }}
        </button>

        <button class="upload-icon-btn" type="button" :aria-label="t('library.upload')">☁</button>
      </section>

      <div class="library-content">
        <section
          v-if="isLoading"
          class="card-grid card-grid--loading"
          :aria-label="t('library.uploadingAria')"
        >
          <div class="library-loading">
            <div class="library-loading__spinner" :aria-label="t('library.uploadingAria')" />
            <p>{{ t("library.processingScroll") }}</p>
          </div>
        </section>

        <section v-else class="card-grid" :aria-label="t('library.cardsAria')">
          <!-- Mistake Review Card -->
          <article
            v-if="mistakeCount > 0"
            class="scroll-card scroll-card--mistake-review"
            @click="openMistakeReview"
          >
            <div class="scroll-card__head">
              <span class="scroll-card__icon">📝</span>
            </div>
            <div class="scroll-card__meta">
              <span class="scroll-card__format">{{ t("library.reviewTag") }}</span>
              <span class="scroll-card__size">{{ t("library.mistakeCount", { count: mistakeCount }) }}</span>
            </div>
            <h2>{{ t("library.mistakeReviewTitle") }}</h2>
            <p class="scroll-card__subtitle">{{ t("library.mistakeReviewSubtitle") }}</p>
            <div class="scroll-card__progress-track" role="presentation">
              <span class="scroll-card__progress-fill scroll-card__progress-fill--mistake" style="width: 100%" />
            </div>
            <button
              class="scroll-card__action scroll-card__action--review"
              type="button"
            >
              <span aria-hidden="true">↻</span>
              <span>{{ t("library.startReview") }}</span>
            </button>
          </article>

          <article
            v-for="card in getScrollCards()"
            :key="card.id"
            class="scroll-card"
            :class="{
              'scroll-card--gold': card.accent === 'gold',
              'scroll-card--selected': card.accent === 'selected',
              'scroll-card--mastered': card.mastered,
            }"
          >
            <p v-if="card.mastered" class="mastered-stamp">{{ t("library.mastered") }}</p>

            <div class="scroll-card__head" :class="{ 'scroll-card__head--batch': isBatchDeleteMode }">
              <span class="scroll-card__icon">{{ card.icon }}</span>
              <label v-if="isBatchDeleteMode" class="scroll-card__check-wrap">
                <input
                  type="checkbox"
                  class="scroll-card__check batch-select-checkbox"
                  :checked="selectedDocumentIds.includes(card.id)"
                  @change="toggleDocumentSelection(card.id)"
                />
              </label>
              <div class="scroll-card__menu-wrap">
                <button
                  v-if="!isBatchDeleteMode"
                  class="scroll-card__edit"
                  type="button"
                  :aria-label="t('library.edit')"
                  @click.stop="toggleCardMenu(card.id)"
                >
                  ✎
                </button>
                <div v-if="activeCardMenuId === card.id" class="scroll-card__menu-popover">
                  <button class="scroll-card__menu-action scroll-card__menu-action--danger" type="button" @click="requestDelete(card)">
                    {{ t("library.delete") }}
                  </button>
                </div>
              </div>
            </div>

            <div class="scroll-card__meta">
              <span class="scroll-card__format">{{ card.format }}</span>
              <span class="scroll-card__size">{{ card.size }}</span>
            </div>

            <h2>{{ card.title }}</h2>
            <p class="scroll-card__subtitle">{{ card.subtitle }}</p>

            <div class="scroll-card__progress-head">
              <span>{{ card.progressLabel }}</span>
              <span class="scroll-card__progress-value" :class="`scroll-card__progress-value--${card.tone}`">
                {{ card.progressValue }}
              </span>
            </div>

            <div class="scroll-card__progress-track" role="presentation">
              <span class="scroll-card__progress-fill" :style="{ width: `${card.progress}%` }" />
            </div>

            <button
              class="scroll-card__action"
              :class="[
                `scroll-card__action--${card.action}`,
                { 'scroll-card__action--routing': openingCard === card.title },
              ]"
              type="button"
              :disabled="card.disabled"
              @click="handleCardAction(card)"
            >
              <span aria-hidden="true">{{ card.action === "review" ? "↻" : card.action === "retry" ? "↺" : "▹" }}</span>
              <span>
                {{
                  card.action === "continue"
                    ? t("library.continueJourney")
                    : card.action === "begin"
                      ? t("library.beginStudy")
                      : card.action === "retry"
                        ? t("library.reprocessDocument")
                        : t("library.review")
                }}
              </span>
            </button>
          </article>

          <article
            class="scroll-card scroll-card--add"
            type="button"
            @click="openUploadModal"
          >
            <p class="scroll-card__add-icon">＋</p>
            <h2>{{ t("library.addNewScroll") }}</h2>
            <p class="scroll-card__add-text">{{ t("library.addScrollDesc") }}</p>
            <p class="scroll-card__add-disclaimer">
              <span class="scroll-card__beta-tag">BETA</span>
              {{ t("library.betaDisclaimer") }}
            </p>
          </article>
        </section>
      </div>
    </main>

    <!-- Upload Modal -->
    <div v-if="uploadModalVisible" class="upload-modal-overlay" @click.self="closeUploadModal">
      <section
        class="upload-modal hero-upload"
        :class="{
          'hero-upload--idle': uploadState === 'idle',
          'hero-upload--loading': uploadState === 'loading',
          'hero-upload--success': uploadState === 'success',
          'hero-upload--failure': uploadState === 'failure',
          'hero-upload--dragging': isDragging,
        }"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @drop="handleDrop"
      >
        <button class="upload-modal__close" type="button" :aria-label="t('common.closeAria')" @click="closeUploadModal">✕</button>

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
          <button class="browse-btn browse-btn--success" type="button" @click.stop="closeUploadModal">
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
    </div>

    <DocumentDeleteConfirmModal
      :visible="Boolean(pendingDeleteCard) || pendingBatchDeleteIds.length > 0"
      :title="pendingDeleteCard?.title || ''"
      :message="pendingBatchDeleteIds.length > 0 ? t('library.deleteSelectedConfirm', { count: pendingBatchDeleteIds.length }) : ''"
      :processing="isDeleting"
      @cancel="closeDeleteModal"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped>
.library-page {
  display: grid;
  gap: 24px;
  grid-template-columns: 256px minmax(0, 1fr);
  height: 100vh;
  min-height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 24px;
}

.library-main {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  padding: 18px;
}

.library-content {
  flex: 1;
  min-height: 0;
}

.library-toolbar {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.search-box {
  align-items: center;
  background: var(--color-search-bg);
  border: 1px solid var(--color-search-border);
  border-radius: 8px;
  display: flex;
  flex: 1 1 320px;
  gap: 8px;
  height: 40px;
  padding: 0 12px;
}

.search-box__icon {
  color: var(--color-text-muted);
  font-size: 16px;
}

.search-box input {
  background: transparent;
  border: 0;
  color: var(--color-text-tertiary);
  flex: 1;
  font-size: 15px;
  outline: 0;
}

.search-box input::placeholder {
  color: var(--color-text-muted);
}

.search-box__clear {
  align-items: center;
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  font-size: 12px;
  height: 20px;
  justify-content: center;
  padding: 0;
  width: 20px;
}

.search-box__clear:hover {
  color: var(--color-text-secondary);
}

.filter-dropdown-wrapper {
  position: relative;
}

.filter-dropdown {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  padding: 8px 0;
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 100;
}

.filter-dropdown__section {
  padding: 8px 12px;
}

.filter-dropdown__section + .filter-dropdown__section {
  border-top: 1px solid var(--color-border-soft);
}

.filter-dropdown__title {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 600;
  margin: 0 0 6px;
  text-transform: uppercase;
}

.filter-dropdown__item {
  background: transparent;
  border: 0;
  border-radius: 4px;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: block;
  font-size: 14px;
  padding: 6px 8px;
  text-align: left;
  width: 100%;
}

.filter-dropdown__item:hover {
  background: var(--color-surface-alt);
}

.filter-dropdown__item--active {
  background: var(--color-primary-50);
  color: var(--color-primary-600);
  font-weight: 600;
}

.sort-btn {
  align-items: center;
  background: var(--color-surface-alt);
  border: 1px solid var(--color-upload-border);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: inline-flex;
  font-size: 14px;
  gap: 6px;
  height: 40px;
  justify-content: center;
  padding: 0 12px;
}

.sort-btn__value {
  color: var(--color-text-strong);
  font-weight: 700;
}

.sort-btn__caret {
  color: var(--color-text-muted);
  font-size: 12px;
}

.sort-btn--danger {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #b91c1c;
}

.sort-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.upload-icon-btn {
  align-items: center;
  background: transparent;
  border: 0;
  color: var(--color-deep-teal);
  cursor: pointer;
  display: inline-flex;
  font-size: 20px;
  height: 34px;
  justify-content: center;
  width: 34px;
}

.card-grid {
  display: grid;
  gap: 14px;
  align-content: start;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 16px;
  min-height: 0;
}

.card-grid::-webkit-scrollbar {
  width: 6px;
}

.card-grid::-webkit-scrollbar-track {
  background: transparent;
}

.card-grid::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

.card-grid::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted);
}

.scroll-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-soft);
  border-radius: 12px;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  min-height: 262px;
  padding: 14px;
  position: relative;
}

.scroll-card--gold {
  border-left: 4px solid var(--color-muted-gold);
  padding-left: 10px;
}

.scroll-card--selected {
  border: 2px dashed var(--color-primary-500);
  padding: 13px;
}

.scroll-card--mastered {
  opacity: 0.66;
}

.mastered-stamp {
  border: 2px solid var(--color-upload-border);
  color: var(--color-upload-border);
  font-family: var(--font-serif);
  font-size: 16px;
  font-style: italic;
  margin: 0;
  padding: 1px 8px;
  position: absolute;
  right: 10px;
  top: 10px;
  transform: rotate(10deg);
}

.scroll-card__head {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.scroll-card__head--batch .scroll-card__menu-wrap {
  display: none;
}

.scroll-card__head--batch .scroll-card__check-wrap {
  margin-left: auto;
  margin-right: 2px;
}

.scroll-card__menu-wrap {
  position: relative;
}

.scroll-card__check-wrap {
  align-items: center;
  display: inline-flex;
  justify-content: center;
}

.scroll-card__check {
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

.scroll-card__icon {
  align-items: center;
  background: var(--color-search-bg);
  border-radius: 10px;
  color: var(--color-deep-teal);
  display: inline-flex;
  font-size: 20px;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.scroll-card__edit {
  background: transparent;
  border: 0;
  color: var(--color-text-light-slate);
  cursor: pointer;
  font-size: 14px;
  height: 20px;
  line-height: 1;
  width: 20px;
}

.scroll-card__menu-popover {
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

.scroll-card__menu-action {
    align-items: center;
    background: transparent;
    border: 0;
    border-radius: 6px;
    color: #1e293b;
    cursor: pointer;
    display: flex;
    font-size: 13px;
    font-weight: 600;
    gap: 6px;
    padding: 8px 10px;
    white-space: nowrap;
  }

  .scroll-card__menu-action--danger {
    color: #dc2626;
  }

.scroll-card__meta {
  align-items: center;
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.scroll-card__format {
  background: var(--color-primary-50);
  border-radius: 4px;
  color: var(--color-primary-500);
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  padding: 4px 6px;
}

.scroll-card__size {
  color: var(--color-text-muted);
  font-size: 13px;
}

.scroll-card h2 {
  font-family: var(--font-serif);
  font-size: 17px;
  line-height: 1.15;
  margin: 12px 0 0;
}

.scroll-card__subtitle {
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.35;
  margin: 8px 0 0;
  min-height: 35px;
}

.scroll-card__progress-head {
  align-items: baseline;
  color: var(--color-text-secondary);
  display: flex;
  font-size: 13px;
  font-weight: 700;
  justify-content: space-between;
  margin-top: auto;
}

.scroll-card__progress-value--teal {
  color: var(--color-primary-500);
}

.scroll-card__progress-value--gold {
  color: var(--color-muted-gold);
}

.scroll-card__progress-value--muted {
  color: var(--color-text-muted);
}

.scroll-card__progress-track {
  background: var(--color-progress-track);
  border-radius: 999px;
  height: 6px;
  margin-top: 6px;
  overflow: hidden;
}

.scroll-card__progress-fill {
  background: var(--color-primary-500);
  display: block;
  height: 100%;
}

.scroll-card--gold .scroll-card__progress-fill {
  background: var(--color-muted-gold);
}

.scroll-card__action {
  align-items: center;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 700;
  gap: 8px;
  height: 38px;
  justify-content: center;
  margin-top: 12px;
}

.scroll-card__action--routing {
  animation: sidebar-route-pulse 220ms ease;
}

.scroll-card__action--continue {
  background: var(--color-primary-500);
  color: var(--color-surface);
}

.scroll-card__action--begin {
  background: var(--color-primary-50);
  border-color: var(--color-primary-100);
  color: var(--color-primary-600);
}

.scroll-card__action--review {
    background: var(--color-border-soft);
    color: var(--color-text-muted);
  }

  .scroll-card__action--retry {
    background: #fef2f2;
    border-color: #fecaca;
    color: #b91c1c;
  }

  .scroll-card--add {
  align-items: center;
  background: var(--color-surface-alt);
  border: 2px dashed var(--color-border);
  justify-content: center;
  text-align: center;
}

.scroll-card__add-icon {
  color: var(--color-text-muted);
  font-size: 44px;
  line-height: 1;
  margin: 0;
}

.scroll-card--add h2 {
  color: var(--color-text-secondary);
  font-family: var(--font-serif);
  font-size: 30px;
  margin-top: 10px;
}

.scroll-card__add-text {
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.4;
  margin: 8px 0 0;
  max-width: 170px;
}

.scroll-card__add-disclaimer {
  background: var(--color-chip-gold-bg);
  border: 1px solid var(--color-muted-gold);
  border-radius: 6px;
  color: var(--color-chip-gold-text);
  font-size: 11px;
  margin: 12px 0 0;
  padding: 6px 10px;
}

.scroll-card__beta-tag {
  background: var(--color-muted-gold);
  border-radius: 3px;
  color: var(--color-surface);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-right: 4px;
  padding: 1px 4px;
}

.scroll-card--add--loading {
  border-color: var(--color-upload-border);
  border-style: solid;
}

.scroll-card__spinner {
  animation: spin 1s linear infinite;
  border: 3px solid var(--color-progress-track);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  height: 32px;
  width: 32px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1360px) {
  .card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.card-grid--loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.library-loading {
  align-items: center;
  color: var(--color-text-muted);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.library-loading__spinner {
  animation: spin 1s linear infinite;
  border: 3px solid var(--color-progress-track);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  height: 32px;
  width: 32px;
}

/* Hero Upload Styles */
.hero-upload {
  align-items: center;
  background: var(--color-surface);
  border: 2px dashed var(--color-upload-border);
  border-radius: 22px;
  display: flex;
  flex-direction: column;
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
  background: var(--color-primary-50);
  border: 1px solid var(--color-upload-border);
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
  background: var(--color-chip-gold-bg);
  border: 1px solid var(--color-muted-gold);
  border-radius: 8px;
  color: var(--color-chip-gold-text);
  font-size: 12px;
  margin: 0 0 12px;
  padding: 8px 14px;
}

.hero-upload__beta-tag {
  background: var(--color-muted-gold);
  border-radius: 4px;
  color: var(--color-surface);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-right: 6px;
  padding: 2px 6px;
}

.hero-upload--loading {
  border-color: var(--color-upload-border);
}

.hero-upload--success {
  border-color: var(--color-status-done);
  border-style: solid;
}

.hero-upload--failure {
  border-color: var(--color-danger-border);
  border-style: solid;
}

.hero-upload--dragging {
  border-color: var(--color-primary-500);
  border-style: solid;
  background: var(--color-primary-50);
}

.hero-upload__file-input {
  display: none;
}

.hero-upload__spinner {
  animation: spin 1s linear infinite;
  border: 3px solid var(--color-progress-track);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  height: 40px;
  margin-top: 20px;
  width: 40px;
}

.browse-btn--success {
  background: var(--color-primary-100);
  border-color: var(--color-status-done);
  color: var(--color-status-done);
}

.hero-upload__retry {
  background: var(--color-danger-surface);
  border-color: var(--color-danger-border);
  color: var(--color-danger-title);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1080px) {
  .library-page {
    grid-template-columns: 1fr;
  }

  .card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

/* Upload Modal */
.upload-modal-overlay {
  align-items: center;
  background: var(--color-overlay-fallback);
  display: flex;
  inset: 0;
  justify-content: center;
  padding: 24px;
  position: fixed;
  z-index: 1000;
}

.upload-modal {
  align-items: center;
  background: var(--color-surface);
  border: 2px dashed var(--color-upload-border);
  border-radius: 22px;
  display: flex;
  flex-direction: column;
  max-width: 560px;
  min-height: 380px;
  padding: 32px 24px;
  position: relative;
  text-align: center;
  width: 100%;
}

.upload-modal__close {
  background: transparent;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 20px;
  padding: 8px;
  position: absolute;
  right: 12px;
  top: 12px;
}

.upload-modal__close:hover {
  color: var(--color-text-secondary);
}

@media (max-width: 768px) {
  .library-page {
    padding: 14px;
  }

  .library-main {
    order: -1;
    padding: 12px;
  }

  .library-toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .sort-btn {
    justify-content: flex-start;
  }

  .upload-icon-btn {
    justify-self: end;
  }

  .card-grid {
    grid-template-columns: 1fr;
  }
}

/* Mistake Review Card Styles */
.scroll-card--mistake-review {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 2px solid #f59e0b;
  cursor: pointer;
  transition: transform 120ms ease, box-shadow 120ms ease;
}

.scroll-card--mistake-review:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(245, 158, 11, 0.25);
}

.scroll-card__progress-fill--mistake {
  background: linear-gradient(90deg, #f59e0b, #d97706);
}
</style>
