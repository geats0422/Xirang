<script setup lang="ts">
import { onMounted, ref } from "vue";
import AppSidebar from "../components/layout/AppSidebar.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";
import { useScholarData } from "../composables/useScholarData";
import { listDocuments, type DocumentListItem } from "../api/documents";

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
  action: "continue" | "begin" | "review";
  tone: "teal" | "gold" | "muted";
  accent?: "gold" | "selected";
  mastered?: boolean;
};

type UploadState = "idle" | "loading" | "success" | "failure";

const documents = ref<DocumentListItem[]>([]);
const isLoading = ref(true);

const { uploadAndRefresh } = useScholarData();

const uploadModalVisible = ref(false);
const uploadState = ref<UploadState>("idle");
const isDragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

onMounted(async () => {
  document.title = "Xi Rang Library";
  await loadDocuments();
});

const loadDocuments = async () => {
  const timeoutId = setTimeout(() => {
    isLoading.value = false;
  }, 5000);

  try {
    documents.value = await listDocuments();
  } catch {
    documents.value = [];
  } finally {
    clearTimeout(timeoutId);
    isLoading.value = false;
  }
};

const getScrollCards = (): ScrollCard[] => {
  return documents.value.map((doc) => ({
    id: doc.id,
    title: doc.title,
    subtitle: "Document awaiting digestion.",
    icon: "📖",
    format: "PDF",
    size: "",
    progressLabel: "Not Started",
    progressValue: "0%",
    progress: 0,
    action: "begin" as const,
    tone: "muted" as const,
  }));
};

const gameModesRoute = ROUTES.gameModes;

const { currentPath, navigateTo, router, routingTarget } = useRouteNavigation();

const openingCard = ref<string | null>(null);

const openModeSelection = async (card: ScrollCard) => {
  if (card.action === "continue") {
    return;
  }

  openingCard.value = card.title;

  await router.push({
    path: gameModesRoute,
    query: {
      flow: card.action,
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

defineExpose({
  openUploadModal,
});
</script>

<template>
  <div class="library-page">
    <AppSidebar :current-path="currentPath" :routing-target="routingTarget" @navigate="navigateTo" />

    <main class="library-main">
      <section class="library-toolbar" aria-label="Library controls">
        <label class="search-box">
          <span class="search-box__icon" aria-hidden="true">⌕</span>
          <input type="text" placeholder="Search scrolls, scriptures, and texts..." />
        </label>

        <button class="sort-btn" type="button">
          <span class="sort-btn__label">Sort by:</span>
          <span class="sort-btn__value">Unfinished</span>
          <span class="sort-btn__caret" aria-hidden="true">▾</span>
        </button>

        <button class="upload-icon-btn" type="button" aria-label="Upload">☁</button>
      </section>

      <section v-if="isLoading" class="card-grid card-grid--loading" aria-label="Loading">
        <div class="library-loading">
          <div class="library-loading__spinner" aria-label="Loading library" />
          <p>Loading your scrolls...</p>
        </div>
      </section>

      <section v-else class="card-grid" aria-label="Library cards">
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
          <p v-if="card.mastered" class="mastered-stamp">MASTERED</p>

          <div class="scroll-card__head">
            <span class="scroll-card__icon">{{ card.icon }}</span>
            <button class="scroll-card__edit" type="button" aria-label="Edit">✎</button>
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
            @click="openModeSelection(card)"
          >
            <span aria-hidden="true">{{ card.action === "review" ? "↻" : "▹" }}</span>
            <span>
              {{
                card.action === "continue"
                  ? "Continue Journey"
                  : card.action === "begin"
                    ? "Begin Study"
                    : "Review"
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
          <h2>Add New Scroll</h2>
          <p class="scroll-card__add-text">Upload PDF, TXT, or EPUB to begin a new digestion.</p>
          <p class="scroll-card__add-disclaimer">
            <span class="scroll-card__beta-tag">BETA</span>
            Free uploads during beta period.
          </p>
        </article>
      </section>
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
        <button class="upload-modal__close" type="button" aria-label="Close" @click="closeUploadModal">✕</button>

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
            accept=".pdf,.txt,.md,.markdown"
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
  </div>
</template>

<style scoped>
.library-page {
  display: grid;
  gap: 24px;
  grid-template-columns: 256px minmax(0, 1fr);
  min-height: 100vh;
  padding: 24px;
}

.library-main {
  background: #fbfbf8;
  border: 1px solid #eceeea;
  border-radius: 14px;
  padding: 18px;
}

.library-toolbar {
  align-items: center;
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1fr) 180px 34px;
}

.search-box {
  align-items: center;
  background: #f4f5f1;
  border: 1px solid #e2e5df;
  border-radius: 8px;
  display: flex;
  gap: 8px;
  height: 40px;
  padding: 0 12px;
}

.search-box__icon {
  color: #9aa2ab;
  font-size: 16px;
}

.search-box input {
  background: transparent;
  border: 0;
  color: #3d4650;
  flex: 1;
  font-size: 15px;
  outline: 0;
}

.search-box input::placeholder {
  color: #9aa2ab;
}

.sort-btn {
  align-items: center;
  background: #f9faf7;
  border: 1px solid #bad8d8;
  border-radius: 8px;
  color: #4f5d6f;
  cursor: pointer;
  display: inline-flex;
  font-size: 14px;
  gap: 6px;
  height: 40px;
  justify-content: center;
  padding: 0 12px;
}

.sort-btn__value {
  color: #2f3b48;
  font-weight: 700;
}

.sort-btn__caret {
  color: #6b7280;
  font-size: 12px;
}

.upload-icon-btn {
  align-items: center;
  background: transparent;
  border: 0;
  color: #1f9aa4;
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 16px;
}

.scroll-card {
  background: #ffffff;
  border: 1px solid #e8ebe6;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(26, 26, 26, 0.04);
  display: flex;
  flex-direction: column;
  min-height: 262px;
  padding: 14px;
  position: relative;
}

.scroll-card--gold {
  border-left: 4px solid #f1bb33;
  padding-left: 10px;
}

.scroll-card--selected {
  border: 2px dashed #2ea4ff;
  padding: 13px;
}

.scroll-card--mastered {
  opacity: 0.66;
}

.mastered-stamp {
  border: 2px solid #8ecdd4;
  color: #8ecdd4;
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

.scroll-card__icon {
  align-items: center;
  background: #f0f2ef;
  border-radius: 10px;
  color: #169aa5;
  display: inline-flex;
  font-size: 20px;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.scroll-card__edit {
  background: transparent;
  border: 0;
  color: #c2c7cf;
  cursor: pointer;
  font-size: 14px;
  height: 20px;
  line-height: 1;
  width: 20px;
}

.scroll-card__meta {
  align-items: center;
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.scroll-card__format {
  background: #e9f4f4;
  border-radius: 4px;
  color: #299da7;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  padding: 4px 6px;
}

.scroll-card__size {
  color: #9aa2ab;
  font-size: 13px;
}

.scroll-card h2 {
  font-family: var(--font-serif);
  font-size: 17px;
  line-height: 1.15;
  margin: 12px 0 0;
}

.scroll-card__subtitle {
  color: #8d95a0;
  font-size: 13px;
  line-height: 1.35;
  margin: 8px 0 0;
  min-height: 35px;
}

.scroll-card__progress-head {
  align-items: baseline;
  color: #5a6573;
  display: flex;
  font-size: 13px;
  font-weight: 700;
  justify-content: space-between;
  margin-top: auto;
}

.scroll-card__progress-value--teal {
  color: #1f9aa4;
}

.scroll-card__progress-value--gold {
  color: #d39e1a;
}

.scroll-card__progress-value--muted {
  color: #9aa2ab;
}

.scroll-card__progress-track {
  background: #e8ecf0;
  border-radius: 999px;
  height: 6px;
  margin-top: 6px;
  overflow: hidden;
}

.scroll-card__progress-fill {
  background: #1f9aa4;
  display: block;
  height: 100%;
}

.scroll-card--gold .scroll-card__progress-fill {
  background: #e5b03a;
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
  background: #1f9aa4;
  color: #ffffff;
}

.scroll-card__action--begin {
  background: #f7fbfb;
  border-color: #8ecdd4;
  color: #1f9aa4;
}

.scroll-card__action--review {
  background: #ececec;
  color: #707784;
}

.scroll-card--add {
  align-items: center;
  background: #fafaf7;
  border: 2px dashed #d6d8d2;
  justify-content: center;
  text-align: center;
}

.scroll-card__add-icon {
  color: #8f959d;
  font-size: 44px;
  line-height: 1;
  margin: 0;
}

.scroll-card--add h2 {
  color: #5c5a5a;
  font-family: var(--font-serif);
  font-size: 30px;
  margin-top: 10px;
}

.scroll-card__add-text {
  color: #9a9da3;
  font-size: 13px;
  line-height: 1.4;
  margin: 8px 0 0;
  max-width: 170px;
}

.scroll-card__add-disclaimer {
  background: #fef9e7;
  border: 1px solid #f5e6a3;
  border-radius: 6px;
  color: #8a6d1b;
  font-size: 11px;
  margin: 12px 0 0;
  padding: 6px 10px;
}

.scroll-card__beta-tag {
  background: #f0ad4e;
  border-radius: 3px;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-right: 4px;
  padding: 1px 4px;
}

.scroll-card--add--loading {
  border-color: #a0d2db;
  border-style: solid;
}

.scroll-card__spinner {
  animation: spin 1s linear infinite;
  border: 3px solid #e0f0f0;
  border-top-color: #1f9aa4;
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
    grid-template-columns: repeat(3, minmax(0, 1fr));
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
  color: #9aa2ab;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.library-loading__spinner {
  animation: spin 1s linear infinite;
  border: 3px solid #e0f0f0;
  border-top-color: #1f9aa4;
  border-radius: 50%;
  height: 32px;
  width: 32px;
}

/* Hero Upload Styles */
.hero-upload {
  align-items: center;
  background: #ffffff;
  border: 2px dashed #b9d8dc;
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
  color: var(--color-text-secondary, #5a6573);
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
  color: #1f9aa4;
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
  color: var(--color-text-muted, #9aa2ab);
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

.browse-btn--success {
  background: #e8f8f0;
  border-color: #6ecf9c;
  color: #22863a;
}

.hero-upload__retry {
  background: #fff5f5;
  border-color: #e8a0a0;
  color: #c53030;
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
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  inset: 0;
  justify-content: center;
  padding: 24px;
  position: fixed;
  z-index: 1000;
}

.upload-modal {
  align-items: center;
  background: var(--color-surface, #ffffff);
  border: 2px dashed #b9d8dc;
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
  color: #9aa2ab;
  cursor: pointer;
  font-size: 20px;
  padding: 8px;
  position: absolute;
  right: 12px;
  top: 12px;
}

.upload-modal__close:hover {
  color: #5a6573;
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
    grid-template-columns: minmax(0, 1fr);
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
</style>
