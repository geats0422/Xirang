<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import AppSidebar from "../components/layout/AppSidebar.vue";
import NotificationPopover from "../components/NotificationPopover.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";
import { useScholarData } from "../composables/useScholarData";
import { getQuests, claimQuestReward, type QuestAssignment, type MonthlyProgress } from "../api/quests";
import { getDaysRemainingInMonth } from "../utils/questUtils";
import {
  getNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  type NotificationItem as ApiNotificationItem,
} from "../api/notifications";

type UploadState = "idle" | "loading" | "success" | "failure";

const { profileName, profileLevel, coins, hasCoinBalance, hydrate, uploadAndRefresh } = useScholarData();
const { t, locale } = useI18n();
const notificationVisible = ref(false);
const notifications = ref<ApiNotificationItem[]>([]);
const unreadCount = ref(0);
const questsError = ref<string | null>(null);

const questsData = ref<{
  daily_quests: QuestAssignment[];
  daily_refresh_at: string;
  monthly_progress: MonthlyProgress;
  streak_days: number;
} | null>(null);
const isLoading = ref(false);
const claimingQuestId = ref<string | null>(null);
const showUploadModal = ref(false);
const uploadState = ref<UploadState>("idle");
const isDragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

const shopRoute = ROUTES.shop;

const toDate = (value: unknown): Date | null => {
  if (typeof value !== "string") {
    return null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? null : parsed;
};

const formatTimeAgo = (dateStr: string): string => {
  const date = toDate(dateStr);
  if (!date) return "";
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return t("home.lastVisitedNow");
  if (diffMins < 60) return `${diffMins}m`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d`;
};

const loadQuests = async () => {
  try {
    isLoading.value = true;
    questsError.value = null;
    questsData.value = await getQuests();
  } catch (error) {
    console.error("Failed to load quests:", error);
    questsError.value = "任务数据加载失败，请稍后重试。";
  } finally {
    isLoading.value = false;
  }
};

const loadNotifications = async () => {
  try {
    const data = await getNotifications();
    notifications.value = data.items ?? [];
    unreadCount.value = data.unread_count;
  } catch (error) {
    console.error("Failed to load notifications:", error);
  }
};

onMounted(async () => {
  await hydrate();
  await Promise.all([loadQuests(), loadNotifications()]);
});

watch(locale, () => {
  document.title = t("quests.metaTitle");
});

const dailyQuests = computed(() => questsData.value?.daily_quests ?? []);
const monthlyProgress = computed(() => questsData.value?.monthly_progress);

const monthlyCompletedCount = computed(() => monthlyProgress.value?.current ?? 0);
const monthlyTarget = computed(() => monthlyProgress.value?.target ?? 30);
const monthlyProgressPercent = computed(() => {
  if (monthlyTarget.value <= 0) return 0;
  return Math.round((monthlyCompletedCount.value / monthlyTarget.value) * 100);
});

const daysRemaining = computed(() => {
  const calendarDays = getDaysRemainingInMonth(new Date());
  const apiDays = monthlyProgress.value?.days_remaining;
  if (typeof apiDays === "number") {
    return apiDays === 0 && calendarDays > 0 ? calendarDays : apiDays;
  }
  return calendarDays;
});

const streakLabel = computed(() => t("quests.streakLabel", { days: questsData.value?.streak_days ?? 0 }));
const coinLabel = computed(() => {
  const amount = hasCoinBalance.value
    ? new Intl.NumberFormat(locale.value).format(coins.value)
    : "--";
  return t("quests.coinLabel", { amount });
});

const monthlyDaysRemainingText = computed(() => t("quests.daysRemaining", { days: daysRemaining.value }));

const refreshInLabel = computed(() => {
  if (!questsData.value?.daily_refresh_at) return "";
  const refreshDate = toDate(questsData.value.daily_refresh_at);
  if (!refreshDate) return "";
  const now = new Date();
  const diffMs = Math.max(0, refreshDate.getTime() - now.getTime());
  const hours = Math.ceil(diffMs / (1000 * 60 * 60));
  return t("quests.refreshIn", { hours: Math.max(1, hours) });
});

const notificationItems = computed(() =>
  notifications.value.map((n) => ({
    id: n.id,
    title: n.title,
    time: formatTimeAgo(n.created_at),
  })),
);

const pushLocalNotification = (title: string) => {
  notifications.value = [
    {
      id: `local-${Date.now()}`,
      type: "system",
      title,
      body: null,
      is_read: false,
      related_quest_id: null,
      action_url: null,
      created_at: new Date().toISOString(),
    },
    ...notifications.value,
  ];
  unreadCount.value += 1;
};

const toggleNotifications = () => {
  notificationVisible.value = !notificationVisible.value;
};

const closeNotifications = async () => {
  notificationVisible.value = false;
};

const handleNotificationClick = async (item: { id: string }) => {
  try {
    await markNotificationAsRead(item.id);
    const notification = notifications.value.find((n) => n.id === item.id);
    if (notification) {
      notification.is_read = true;
    }
    unreadCount.value = Math.max(0, unreadCount.value - 1);
  } catch (error) {
    console.error("Failed to mark notification as read:", error);
  }
};

const handleMarkAllRead = async () => {
  try {
    await markAllNotificationsAsRead();
    notifications.value.forEach((n) => {
      n.is_read = true;
    });
    unreadCount.value = 0;
  } catch (error) {
    console.error("Failed to mark all as read:", error);
  }
};

const { currentPath, navigateTo, routingTarget } = useRouteNavigation();

const handleQuestAction = async (quest: QuestAssignment) => {
  if (quest.action_type === "navigate" && quest.navigate_to) {
    if (quest.quest_code === "quest-upload") {
      showUploadModal.value = true;
      uploadState.value = "idle";
      return;
    }
    navigateTo(quest.navigate_to);
    return;
  }

  if (quest.action_type === "claim" && quest.status === "completed") {
    try {
      claimingQuestId.value = quest.id;
      await claimQuestReward(quest.id);
      await loadQuests();
      await loadNotifications();
      pushLocalNotification(t("quests.notification.questRewardReceived", { reward: t(quest.reward_i18n_key) }));
    } catch (error) {
      console.error("Failed to claim reward:", error);
    } finally {
      claimingQuestId.value = null;
    }
  }
};

const closeUploadModal = () => {
  showUploadModal.value = false;
  uploadState.value = "idle";
};

const handleBrowseClick = () => {
  fileInput.value?.click();
};

const handleUploadFromQuest = async (files: FileList | null) => {
  if (!files || files.length === 0) {
    return;
  }

  uploadState.value = "loading";
  try {
    await uploadAndRefresh(files);
    uploadState.value = "success";
    await Promise.all([loadQuests(), loadNotifications()]);
    pushLocalNotification(t("quests.notification.questUploadDone"));
  } catch (error) {
    console.error("Failed to upload from quest modal:", error);
    uploadState.value = "failure";
  }
};

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  await handleUploadFromQuest(target.files);
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
  await handleUploadFromQuest(event.dataTransfer?.files ?? null);
};

const handleRetry = () => {
  uploadState.value = "idle";
};

const getQuestProgressPercent = (quest: QuestAssignment): number => {
  if (quest.target_value <= 0) return 0;
  return Math.min(100, (quest.progress_value / quest.target_value) * 100);
};

const getQuestProgressLabel = (quest: QuestAssignment): string => {
  if (quest.status === "claimed") return t("quests.completed");
  return t("quests.progressRatio", { current: quest.progress_value, total: quest.target_value });
};

const isQuestActionable = (quest: QuestAssignment): boolean => {
  return quest.action_type === "navigate" || (quest.action_type === "claim" && quest.status === "completed");
};
</script>

<template>
  <div class="quests-page">
    <AppSidebar
      :current-path="currentPath"
      :routing-target="routingTarget"
      :profile-name="profileName"
      :profile-level="profileLevel"
      @navigate="navigateTo"
    />

    <main class="quests-main">
      <section class="quests-shell">
        <header class="quests-statusbar" :aria-label="t('quests.statusAria')">
          <div class="status-pill status-pill--streak">🔥 {{ streakLabel }}</div>
          <button class="status-pill status-pill--coins" type="button" @click="navigateTo(shopRoute)">🪙 {{ coinLabel }}</button>
          <button class="notify-btn" type="button" :aria-label="t('quests.notifications')" @click="toggleNotifications">
            🔔
            <span v-if="unreadCount > 0" class="notify-btn__dot" aria-hidden="true" />
          </button>
        </header>

        <NotificationPopover
          :items="notificationItems"
          :visible="notificationVisible"
          @close="closeNotifications"
          @item-click="handleNotificationClick"
          @mark-all-read="handleMarkAllRead"
        />

        <section class="monthly-banner" :aria-label="t('quests.monthlyAria')">
          <p class="monthly-banner__eyebrow">{{ t("quests.monthlyEyebrow") }}</p>
          <h1>{{ t("quests.monthlyTitle") }}</h1>
          <p class="monthly-banner__copy">{{ t("quests.monthlyDesc") }}</p>

          <div class="monthly-banner__progress-head">
            <span>{{ t("quests.progressRatio", { current: monthlyCompletedCount, total: monthlyTarget }) }}</span>
          </div>

          <div class="progress-track progress-track--banner" role="presentation">
            <span class="progress-fill progress-fill--banner" :style="{ width: `${monthlyProgressPercent}%` }" />
          </div>

          <div class="monthly-banner__footer">
            <span>{{ monthlyDaysRemainingText }}</span>
          </div>
        </section>

        <section class="missions-section" :aria-label="t('quests.dailyAria')">
          <div class="section-head">
            <h2>{{ t("quests.dailyTitle") }}</h2>
            <span>{{ refreshInLabel }}</span>
          </div>

          <div v-if="isLoading" class="loading-state">
            <span>Loading...</span>
          </div>

          <div v-else-if="questsError" class="loading-state loading-state--error">
            <span>{{ questsError }}</span>
            <button class="mission-card__action mission-card__action--solid" type="button" @click="loadQuests">
              {{ t("quests.retryLoad") }}
            </button>
          </div>

          <div v-else-if="dailyQuests.length === 0" class="loading-state">
            <span>{{ t("quests.emptyDaily") }}</span>
          </div>

          <div v-else class="mission-list">
            <article
              v-for="quest in dailyQuests"
              :key="quest.id"
              class="mission-card"
              :class="{ 'mission-card--locked': quest.locked }"
            >
              <div class="mission-card__left">
                <div class="mission-card__icon" :class="`mission-card__icon--${quest.icon_tone}`">{{ quest.icon }}</div>

                <div class="mission-card__body">
                  <h3>{{ t(quest.title_i18n_key) }}</h3>

                  <div class="mission-card__progress-row">
                    <div class="progress-track progress-track--mission" role="presentation">
                      <span class="progress-fill" :style="{ width: `${getQuestProgressPercent(quest)}%` }" />
                    </div>
                    <span :class="{ 'mission-card__progress-label--done': quest.status === 'claimed' }">
                      {{ getQuestProgressLabel(quest) }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="mission-card__right">
                <p class="mission-card__reward">
                  <span>{{ quest.reward_icon }}</span>{{ t(quest.reward_i18n_key) }}
                </p>
                <button
                  class="mission-card__action"
                  :class="{
                    'mission-card__action--solid': isQuestActionable(quest),
                    'mission-card__action--disabled': quest.locked || claimingQuestId === quest.id,
                  }"
                  type="button"
                  :disabled="quest.locked || claimingQuestId === quest.id"
                  @click="handleQuestAction(quest)"
                >
                  {{ claimingQuestId === quest.id ? "..." : t(quest.action_i18n_key) }}
                </button>
              </div>
            </article>
          </div>
        </section>

        <transition name="modal-fade">
          <div v-if="showUploadModal" class="upload-modal-overlay" @click.self="closeUploadModal">
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
                {{ t("home.uploadDisclaimer") }}
              </p>

              <template v-if="uploadState === 'idle'">
                <h1>{{ t("home.idleTitle") }}</h1>
                <p>{{ t("home.idleDesc") }}</p>
                <input
                  ref="fileInput"
                  type="file"
                  accept=".pdf,.txt,.md,.markdown,.doc,.docx,.ppt,.pptx"
                  multiple
                  class="hero-upload__file-input"
                  @change="handleFileSelect"
                />
                <button class="browse-btn" type="button" @click.stop="handleBrowseClick">
                  ☁ {{ t("home.browseScrolls") }}
                </button>
                <span class="support-text">{{ t("home.supportText") }}</span>
              </template>

              <template v-else-if="uploadState === 'loading'">
                <h1>{{ t("home.loadingTitle") }}</h1>
                <p>{{ t("home.loadingDesc") }}</p>
                <div class="hero-upload__spinner" :aria-label="t('home.loadingAria')" />
              </template>

              <template v-else-if="uploadState === 'success'">
                <h1>{{ t("home.successTitle") }}</h1>
                <p>{{ t("home.successDesc") }}</p>
                <button class="browse-btn browse-btn--success" type="button" @click.stop="closeUploadModal">
                  ✓ {{ t("home.successAction") }}
                </button>
              </template>

              <template v-else-if="uploadState === 'failure'">
                <h1>{{ t("home.failureTitle") }}</h1>
                <p>{{ t("home.failureDesc") }}</p>
                <button class="browse-btn hero-upload__retry" type="button" @click.stop="handleRetry">
                  ↻ {{ t("home.retryUpload") }}
                </button>
              </template>
            </section>
          </div>
        </transition>
      </section>
    </main>
  </div>
</template>

<style scoped>
.quests-page {
  background: linear-gradient(180deg, var(--color-page-bg) 0%, var(--color-surface-alt) 100%);
  display: grid;
  gap: 24px;
  grid-template-columns: 256px minmax(0, 1fr);
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;
  padding: 24px;
}

.quests-main {
  min-height: 0;
  min-width: 0;
  overflow-y: auto;
}

.quests-shell {
  display: grid;
  gap: 28px;
  margin: 0 auto;
  max-width: 1280px;
}

.quests-statusbar {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.status-pill {
  align-items: center;
  border: 0;
  border-radius: 999px;
  display: inline-flex;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  min-height: 36px;
  padding: 0 14px;
}

.status-pill--streak {
  background: var(--color-streak-bg);
  color: var(--color-streak-text);
}

.status-pill--coins {
  background: var(--color-status-coins-bg);
  color: var(--color-status-amber);
  cursor: pointer;
}

.notify-btn {
  align-items: center;
  background: transparent;
  border: 0;
  color: var(--color-icon-amber);
  cursor: pointer;
  display: inline-flex;
  font-size: 18px;
  height: 36px;
  justify-content: center;
  position: relative;
  width: 36px;
}

.notify-btn__dot {
  background: var(--color-icon-red);
  border-radius: 999px;
  height: 8px;
  position: absolute;
  right: 6px;
  top: 6px;
  width: 8px;
}

.monthly-banner {
  background:
    radial-gradient(circle at 85% 26%, var(--color-overlay-glass), transparent 22%),
    linear-gradient(90deg, var(--color-primary-500) 0%, var(--color-icon-blue) 48%, var(--color-icon-violet) 100%);
  border-radius: 24px;
  color: var(--color-surface);
  overflow: hidden;
  padding: 26px 28px 24px;
  position: relative;
}

.monthly-banner::after {
  background: radial-gradient(circle, var(--color-overlay-glass) 0%, transparent 70%);
  content: "";
  height: 240px;
  position: absolute;
  right: -40px;
  top: -30px;
  width: 240px;
}

.monthly-banner__eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin: 0;
  opacity: 0.82;
}

.monthly-banner h1,
.section-head h2,
.mission-card h3 {
  font-family: var(--font-serif);
}

.monthly-banner h1 {
  color: var(--color-surface);
  font-size: 34px;
  line-height: 1.14;
  margin: 10px 0 0;
  max-width: 520px;
}

.monthly-banner__copy {
  font-size: 16px;
  margin: 10px 0 0;
  opacity: 0.92;
}

.monthly-banner__progress-head {
  display: flex;
  justify-content: flex-end;
  margin-top: 22px;
}

.monthly-banner__progress-head span,
.monthly-banner__footer span {
  font-size: 15px;
  font-weight: 700;
}

.progress-track {
  background: var(--color-progress-track);
  border-radius: 999px;
  overflow: hidden;
}

.progress-track--banner {
  background: var(--color-overlay-glass);
  height: 14px;
  margin-top: 10px;
}

.progress-track--mission {
  flex: 1;
  height: 6px;
}

.progress-fill {
  background: linear-gradient(90deg, var(--color-icon-violet) 0%, var(--color-icon-blue) 100%);
  display: block;
  height: 100%;
}

.progress-fill--banner {
  background: var(--color-surface);
}

.monthly-banner__footer {
  margin-top: 16px;
}

.missions-section {
  display: grid;
  gap: 16px;
}

.section-head {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.section-head h2 {
  color: var(--color-mission-text);
  font-size: 32px;
  margin: 0;
}

.section-head span {
  color: var(--color-mission-progress-text);
  font-size: 13px;
  font-weight: 700;
}

.loading-state {
  align-items: center;
  color: var(--color-text-secondary);
  display: flex;
  flex-direction: column;
  gap: 12px;
  justify-content: center;
  padding: 48px;
}

.loading-state--error {
  color: var(--color-icon-red);
}

.mission-list {
  display: grid;
  gap: 14px;
}

.mission-card {
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  box-shadow: var(--shadow-card);
  display: flex;
  justify-content: space-between;
  padding: 18px 20px;
}

.mission-card--locked {
  opacity: 0.6;
}

.mission-card__left {
  align-items: center;
  display: flex;
  gap: 16px;
  min-width: 0;
}

.mission-card__icon {
  align-items: center;
  border-radius: 12px;
  color: var(--color-surface);
  display: inline-flex;
  flex: 0 0 auto;
  font-size: 20px;
  height: 44px;
  justify-content: center;
  width: 44px;
}

.mission-card__icon--violet {
  background: var(--color-icon-violet);
}

.mission-card__icon--green {
  background: var(--color-icon-green);
}

.mission-card__icon--blue {
  background: var(--color-icon-blue);
}

.mission-card__icon--amber {
  background: var(--color-icon-amber);
}

.mission-card__body {
  min-width: 0;
}

.mission-card h3 {
  color: var(--color-mission-text);
  font-size: 15px;
  margin: 0;
  max-width: 560px;
}

.mission-card__progress-row {
  align-items: center;
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.mission-card__progress-row span {
  color: var(--color-mission-progress-text);
  font-size: 12px;
  font-weight: 700;
}

.mission-card__progress-label--done {
  color: var(--color-status-done);
}

.mission-card__right {
  align-items: flex-end;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-left: 18px;
}

.mission-card__reward {
  align-items: center;
  color: var(--color-icon-amber);
  display: inline-flex;
  font-size: 14px;
  font-weight: 700;
  gap: 6px;
  margin: 0;
}

.mission-card__reward span {
  font-size: 15px;
}

.mission-card__action {
  align-items: center;
  background: var(--color-action-secondary-bg);
  border: 0;
  border-radius: 12px;
  color: var(--color-action-secondary-text);
  cursor: pointer;
  display: inline-flex;
  font-size: 13px;
  font-weight: 700;
  height: 38px;
  justify-content: center;
  min-width: 126px;
  padding: 0 16px;
}

.mission-card__action--solid {
  background: var(--color-primary-500);
  color: var(--color-surface);
}

.mission-card__action--ghost {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
}

.mission-card__action--disabled {
  cursor: not-allowed;
  opacity: 0.64;
}

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
  background: var(--color-primary-50);
  border-color: var(--color-primary-500);
  border-style: solid;
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
  .quests-page {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .quests-page {
    height: 100vh;
    padding: 14px;
  }

  .quests-main {
    order: -1;
  }

  .quests-statusbar,
  .mission-card,
  .mission-card__left {
    align-items: flex-start;
    flex-direction: column;
  }

  .monthly-banner {
    padding: 22px 18px;
  }

  .monthly-banner h1,
  .section-head h2 {
    font-size: 28px;
  }

  .mission-card__right {
    align-items: flex-start;
    margin-left: 0;
    margin-top: 14px;
  }
}
</style>
