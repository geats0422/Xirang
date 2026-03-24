<script setup lang="ts">
import { onMounted, ref } from "vue";
import { listDocuments as getDocuments } from "../api/documents";
import AppSidebar from "../components/layout/AppSidebar.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";

type UploadState = "idle" | "loading" | "success" | "failure";

type HomeDocumentCard = {
  id: string;
  title: string;
  lastVisited: string;
  progress: number;
  icon: string;
};

type ApiDocument = {
  id: string;
  title?: string;
  filename?: string;
  updated_at?: string;
  progress?: number;
  type?: string;
};

const formatLastVisited = (dateStr: string | undefined): string => {
  if (!dateStr) return "Unknown";
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffHours < 1) return "Just now";
  if (diffHours < 24) return `${diffHours} hours ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString();
};

const getDocIcon = (type: string | undefined): string => {
  if (type?.includes("pdf")) return "📜";
  if (type?.includes("markdown") || type?.includes("md")) return "📝";
  if (type?.includes("text") || type?.includes("txt")) return "📘";
  return "📄";
};

const fetchDocuments = async () => {
  isLoading.value = true;
  try {
    const docs = (await getDocuments()) as ApiDocument[];
    documents.value = docs.map((doc) => ({
      id: doc.id,
      title: doc.title || doc.filename || "Untitled",
      lastVisited: formatLastVisited(doc.updated_at),
      progress: doc.progress || 0,
      icon: getDocIcon(doc.type),
    }));
  } catch (error) {
    console.error("Failed to fetch documents:", error);
    documents.value = [];
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  document.title = "Xi Rang Home";
  await fetchDocuments();
});

const shopRoute = ROUTES.shop;

const { currentPath, navigateTo, routingTarget } = useRouteNavigation();

const uploadState = ref<UploadState>("idle");
const documents = ref<HomeDocumentCard[]>([]);
const isLoading = ref(false);

const handleUpload = () => {
  uploadState.value = "loading";
  window.setTimeout(() => {
    uploadState.value = "success";
  }, 1500);
};

const handleRetry = () => {
  uploadState.value = "idle";
};

const setUploadFailure = () => {
  uploadState.value = "failure";
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
        <div class="status-pill status-pill--streak">🔥 {{ $t("home.streakLabel", { days: 12 }) }}</div>
        <button class="status-pill status-pill--coin" type="button" @click="navigateTo(shopRoute)">
          🪙 {{ $t("home.coinLabel", { amount: 350 }) }}
        </button>
        <button class="status-notify" type="button" :aria-label="$t('home.notifications')">🔔</button>
      </header>

      <section
        class="hero-upload"
        :class="{
          'hero-upload--idle': uploadState === 'idle',
          'hero-upload--loading': uploadState === 'loading',
          'hero-upload--success': uploadState === 'success',
          'hero-upload--failure': uploadState === 'failure',
        }"
        :aria-label="$t('home.uploadAria')"
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
          <button class="browse-btn" type="button" @click="handleUpload">☁ {{ $t("home.browseScrolls") }}</button>
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
          <button class="browse-btn browse-btn--success" type="button" @click="uploadState = 'idle'">
            ✓ {{ $t("home.successAction") }}
          </button>
        </template>

        <template v-else-if="uploadState === 'failure'">
          <h1>{{ $t("home.failureTitle") }}</h1>
          <p>{{ $t("home.failureDesc") }}</p>
          <button class="browse-btn hero-upload__retry" type="button" @click="handleRetry">
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
