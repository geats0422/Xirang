<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import AppSidebar from "../components/layout/AppSidebar.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";
import { useScholarData } from "../composables/useScholarData";
import { listDocuments, type DocumentListItem } from "../api/documents";

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
  await loadDocuments();
});

// Update document title reactively when locale changes
watch(locale, () => {
  document.title = t("library.metaTitle");
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
    subtitle: t("library.awaitingSubtitle"),
    icon: "📖",
    format: "PDF",
    size: "",
    progressLabel: t("library.notStarted"),
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
      <section class="library-toolbar" :aria-label="t('library.controlsAria')">
        <label class="search-box">
          <span class="search-box__icon" aria-hidden="true">⌕</span>
          <input type="text" :placeholder="t('library.searchPlaceholder')" />
        </label>

        <button class="sort-btn" type="button">
          <span class="sort-btn__label">{{ t("library.sortBy") }}</span>
          <span class="sort-btn__value">{{ t("library.sortUnfinished") }}</span>
          <span class="sort-btn__caret" aria-hidden="true">▾</span>
        </button>

        <button class="upload-icon-btn" type="button" :aria-label="t('library.upload')">☁</button>
      </section>

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

          <div class="scroll-card__head">
            <span class="scroll-card__icon">{{ card.icon }}</span>
            <button class="scroll-card__edit" type="button" :aria-label="t('library.edit')">✎</button>
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
                  ? t("library.continueJourney")
                  : card.action === "begin"
                    ? t("library.beginStudy")
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
  background: var(--color-surface);
  border: 1px solid var(--color-border);
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
  background: var(--color-search-bg);
  border: 1px solid var(--color-search-border);
  border-radius: 8px;
  display: flex;
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 16px;
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
