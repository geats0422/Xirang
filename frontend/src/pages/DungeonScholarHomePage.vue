<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import AppSidebar from "../components/layout/AppSidebar.vue";
import NotificationPopover from "../components/NotificationPopover.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";
import { useScholarData } from "../composables/useScholarData";

const { t, locale } = useI18n();

type UploadState = "idle" | "loading" | "success" | "failure";

type HomeDocumentCard = {
  id: string;
  title: string;
  lastVisited: string;
  progress: number;
  icon: string;
};

type NotificationItem = {
  id: string;
  title: string;
  time: string;
};

const getDocIcon = (): string => "📖";

const { streak, coins, documents: scholarDocs, uploadAndRefresh, hydrate } = useScholarData();

const documents = ref<HomeDocumentCard[]>([]);
const isLoading = ref(false);

const fetchDocuments = async () => {
  isLoading.value = true;
  try {
    documents.value = scholarDocs.value.map((doc) => ({
      id: doc.id,
      title: doc.title,
      lastVisited: "Just now",
      progress: 0,
      icon: getDocIcon(),
    }));
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

const { currentPath, navigateTo, routingTarget } = useRouteNavigation();

const uploadState = ref<UploadState>("idle");
const isDragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const notificationVisible = ref(false);
const notifications = ref<NotificationItem[]>([]);

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

defineExpose({
  uploadState,
  documents,
  isLoading,
  setUploadFailure,
});
</script>

<template>
  <div class="home-page">
    <AppSidebar :current-path="currentPath" :routing-target="routingTarget" @navigate="navigateTo" />

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
          <a href="#">{{ $t("home.viewAll") }}</a>
        </div>

        <div class="dungeon-grid">
          <article v-for="card in documents" :key="card.id" class="dungeon-card">
            <div class="dungeon-card__head">
              <span class="dungeon-card__icon">{{ card.icon }}</span>
              <button class="dungeon-card__menu" type="button" :aria-label="$t('home.moreOptions')">⋯</button>
            </div>
            <h3>{{ card.title }}</h3>
            <p>{{ $t("home.lastVisitedPrefix") }} {{ card.lastVisited }}</p>
            <div class="dungeon-card__progress">
              <div class="progress-track" role="presentation">
                <span class="progress-fill" :style="{ width: `${card.progress}%` }" />
              </div>
              <strong>{{ card.progress }}%</strong>
            </div>
          </article>
        </div>
      </section>
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

.recent-section__head {
  align-items: center;
  display: flex;
  justify-content: space-between;
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
