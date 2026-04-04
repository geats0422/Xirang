<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import AppSidebar from "../components/layout/AppSidebar.vue";
import NotificationPopover from "../components/NotificationPopover.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";
import { useScholarData } from "../composables/useScholarData";

type DailyQuest = {
  id: string;
  title: string;
  type: "upload" | "streak" | "abyss";
  completed: boolean;
  locked?: boolean;
};

type MissionCard = {
  id: string;
  title: string;
  icon: string;
  iconTone: "violet" | "green" | "blue";
  progress: number;
  progressLabel: string;
  reward: string;
  rewardIcon: string;
  action: string;
  actionTone: "ghost" | "solid";
  disabled: boolean;
};

type NotificationItem = {
  id: string;
  title: string;
  time: string;
};

const { profileName, profileLevel, streak, coins, hasCoinBalance, documents, runs, hydrate } = useScholarData();
const { t, locale } = useI18n();
const notificationVisible = ref(false);
const notifications = ref<NotificationItem[]>([]);

const MONTHLY_PROGRESS_STORAGE_PREFIX = "xirang:quests:monthly-progress";
const MONTHLY_PROGRESS_TARGET = 30;

const toggleNotifications = () => {
  notificationVisible.value = !notificationVisible.value;
};

const closeNotifications = () => {
  notificationVisible.value = false;
};

const toDate = (value: unknown): Date | null => {
  if (typeof value !== "string") {
    return null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? null : parsed;
};

const isSameLocalDay = (left: Date, right: Date): boolean => {
  return left.getFullYear() === right.getFullYear()
    && left.getMonth() === right.getMonth()
    && left.getDate() === right.getDate();
};

const getMonthlyStorageKey = (date: Date): string => {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${MONTHLY_PROGRESS_STORAGE_PREFIX}:${date.getFullYear()}-${month}`;
};

const readMonthlyDailyMap = (date: Date): Record<string, number> => {
  if (typeof window === "undefined") {
    return {};
  }
  const key = getMonthlyStorageKey(date);
  const raw = window.localStorage.getItem(key);
  if (!raw) {
    return {};
  }
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return Object.entries(parsed).reduce<Record<string, number>>((acc, [day, count]) => {
      if (typeof count === "number" && Number.isFinite(count) && count >= 0) {
        acc[day] = Math.min(MONTHLY_PROGRESS_TARGET, Math.floor(count));
      }
      return acc;
    }, {});
  } catch {
    return {};
  }
};

const writeMonthlyDailyMap = (date: Date, map: Record<string, number>) => {
  if (typeof window === "undefined") {
    return;
  }
  const key = getMonthlyStorageKey(date);
  window.localStorage.setItem(key, JSON.stringify(map));
};

onMounted(async () => {
  await hydrate();
  await hydrateDailyQuests();
});

watch([documents, runs, streak], () => {
  void hydrateDailyQuests();
}, { deep: true });

// Update document title reactively when locale changes
watch(locale, () => {
  document.title = t("quests.metaTitle");
});

const quests = ref<DailyQuest[]>([
  {
    id: "quest-upload",
    title: t("quests.missionUploadTitle"),
    type: "upload",
    completed: false,
  },
  {
    id: "quest-streak",
    title: t("quests.missionStreakTitle"),
    type: "streak",
    completed: false,
  },
  {
    id: "quest-abyss",
    title: t("quests.missionAbyssTitle"),
    type: "abyss",
    completed: false,
    locked: true,
  },
]);

const today = computed(() => new Date());

const todayUploadCompleted = computed(() => {
  const now = today.value;
  return documents.value.some((doc) => {
    const createdAt = toDate(doc.created_at);
    return createdAt !== null && isSameLocalDay(createdAt, now);
  });
});

const todayEndlessCompletedCount = computed(() => {
  const now = today.value;
  return runs.value.filter((run) => {
    if (run.status !== "completed" || run.mode !== "endless") {
      return false;
    }
    const endedAt = toDate(run.ended_at ?? null);
    return endedAt !== null && isSameLocalDay(endedAt, now);
  }).length;
});

const todayStreakCompleted = computed(() => streak.value > 0);

const completedDailyQuestCount = computed(() => {
  return [todayUploadCompleted.value, todayStreakCompleted.value, todayEndlessCompletedCount.value >= 2].filter(Boolean).length;
});

const monthlyCompletedCount = computed(() => {
  const now = today.value;
  const monthMap = readMonthlyDailyMap(now);
  const dayKey = String(now.getDate());
  const currentDayCount = Math.min(MONTHLY_PROGRESS_TARGET, completedDailyQuestCount.value);

  if (monthMap[dayKey] !== currentDayCount) {
    monthMap[dayKey] = currentDayCount;
    writeMonthlyDailyMap(now, monthMap);
  }

  const total = Object.values(monthMap).reduce((acc, count) => acc + count, 0);
  return Math.min(MONTHLY_PROGRESS_TARGET, total);
});

const monthlyProgressPercent = computed(() => {
  if (MONTHLY_PROGRESS_TARGET <= 0) {
    return 0;
  }
  return Math.round((monthlyCompletedCount.value / MONTHLY_PROGRESS_TARGET) * 100);
});

const hydrateDailyQuests = async () => {
  const hasAnyDocuments = documents.value.length > 0;
  const uploadCompleted = todayUploadCompleted.value;
  const streakCompleted = todayStreakCompleted.value;
  const abyssCompleted = todayEndlessCompletedCount.value >= 2;

  quests.value = quests.value.map((quest) => {
    if (quest.type === "upload") {
      return {
        ...quest,
        completed: uploadCompleted,
      };
    }

    if (quest.type === "streak") {
      return {
        ...quest,
        completed: streakCompleted,
      };
    }

    if (quest.type === "abyss") {
      return {
        ...quest,
        completed: abyssCompleted,
        locked: !hasAnyDocuments,
      };
    }

    return quest;
  });
};

const streakLabel = computed(() => t("quests.streakLabel", { days: streak.value }));
const coinLabel = computed(() => {
  const amount = hasCoinBalance.value
    ? new Intl.NumberFormat(locale.value).format(coins.value)
    : "--";
  return t("quests.coinLabel", { amount });
});

const monthlyDaysRemaining = computed(() => {
  const now = today.value;
  const totalDaysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const days = Math.max(0, totalDaysInMonth - now.getDate());
  return t("quests.daysRemaining", { days });
});

const refreshInLabel = computed(() => {
  const now = today.value;
  const nextReset = new Date(now);
  nextReset.setHours(24, 0, 0, 0);
  const diffMs = Math.max(0, nextReset.getTime() - now.getTime());
  const hours = Math.ceil(diffMs / (1000 * 60 * 60));
  return t("quests.refreshIn", { hours: Math.max(1, hours) });
});

const shopRoute = ROUTES.shop;

const missionCards = computed<MissionCard[]>(() =>
  quests.value.map((quest) => {
    if (quest.type === "abyss") {
      const isLocked = quest.locked === true;
      const completedCount = isLocked ? 0 : Math.min(2, todayEndlessCompletedCount.value);
      return {
        id: quest.id,
        title: t("quests.missionAbyssTitle"),
        icon: "⚔",
        iconTone: "violet",
        progress: (completedCount / 2) * 100,
        progressLabel: isLocked
          ? t("quests.progressRatio", { current: 0, total: 2 })
          : t("quests.progressRatio", { current: completedCount, total: 2 }),
        reward: t("quests.rewardDoubleCard"),
        rewardIcon: "🎁",
        action: completedCount >= 2 ? t("quests.claimReward") : t("quests.continue"),
        actionTone: completedCount >= 2 ? "solid" : "ghost",
        disabled: isLocked,
      };
    }

    if (quest.type === "streak") {
      return {
        id: quest.id,
        title: t("quests.missionStreakTitle"),
        icon: "✓",
        iconTone: "green",
        progress: quest.completed ? 100 : 0,
        progressLabel: quest.completed
          ? t("quests.completed")
          : t("quests.progressRatio", { current: 0, total: 1 }),
        reward: "+50",
        rewardIcon: "🪙",
        action: quest.completed ? t("quests.claimReward") : t("quests.continue"),
        actionTone: quest.completed ? "solid" : "ghost",
        disabled: false,
      };
    }

    return {
      id: quest.id,
      title: t("quests.missionUploadTitle"),
      icon: "⤴",
      iconTone: "blue",
      progress: quest.completed ? 100 : 0,
      progressLabel: quest.completed
        ? t("quests.completed")
        : t("quests.progressRatio", { current: 0, total: 1 }),
      reward: t("quests.rewardGoldChest"),
      rewardIcon: "🧰",
      action: quest.completed ? t("quests.claimReward") : t("quests.upload"),
      actionTone: "solid",
      disabled: false,
    };
  }),
);

const { currentPath, navigateTo, routingTarget } = useRouteNavigation();
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
            <span class="notify-btn__dot" aria-hidden="true" />
          </button>
        </header>

        <NotificationPopover :items="notifications" :visible="notificationVisible" @close="closeNotifications" />

        <section class="monthly-banner" :aria-label="t('quests.monthlyAria')">
          <p class="monthly-banner__eyebrow">{{ t("quests.monthlyEyebrow") }}</p>
          <h1>{{ t("quests.monthlyTitle") }}</h1>
          <p class="monthly-banner__copy">{{ t("quests.monthlyDesc") }}</p>

          <div class="monthly-banner__progress-head">
            <span>{{ t("quests.progressRatio", { current: monthlyCompletedCount, total: 30 }) }}</span>
          </div>

          <div class="progress-track progress-track--banner" role="presentation">
            <span class="progress-fill progress-fill--banner" :style="{ width: `${monthlyProgressPercent}%` }" />
          </div>

          <div class="monthly-banner__footer">
            <span>{{ monthlyDaysRemaining }}</span>
          </div>
        </section>

        <section class="missions-section" :aria-label="t('quests.dailyAria')">
          <div class="section-head">
            <h2>{{ t("quests.dailyTitle") }}</h2>
            <span>{{ refreshInLabel }}</span>
          </div>

          <div class="mission-list">
            <article v-for="mission in missionCards" :key="mission.id" class="mission-card">
              <div class="mission-card__left">
                <div class="mission-card__icon" :class="`mission-card__icon--${mission.iconTone}`">{{ mission.icon }}</div>

                <div class="mission-card__body">
                  <h3>{{ mission.title }}</h3>

                  <div class="mission-card__progress-row">
                    <div class="progress-track progress-track--mission" role="presentation">
                      <span class="progress-fill" :style="{ width: `${mission.progress}%` }" />
                    </div>
                    <span :class="{ 'mission-card__progress-label--done': mission.progress === 100 }">
                      {{ mission.progressLabel }}
                    </span>
                  </div>
                </div>
              </div>

              <div class="mission-card__right">
                <p class="mission-card__reward"><span>{{ mission.rewardIcon }}</span>{{ mission.reward }}</p>
                <button
                  class="mission-card__action"
                  :class="{
                    'mission-card__action--solid': mission.actionTone === 'solid',
                    'mission-card__action--disabled': mission.disabled,
                  }"
                  type="button"
                  :disabled="mission.disabled"
                >
                  {{ mission.action }}
                </button>
              </div>
            </article>
          </div>
        </section>
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

.mission-card__action--disabled {
  cursor: not-allowed;
  opacity: 0.64;
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
