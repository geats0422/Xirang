<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { getLeaderboardSnapshot, type DailyFocusItem, type LeaderboardEntry } from "../api/leaderboard";
import LeaderboardStandingsTable from "../components/leaderboard/LeaderboardStandingsTable.vue";
import LeaderboardSummaryPanel from "../components/leaderboard/LeaderboardSummaryPanel.vue";
import AppSidebar from "../components/layout/AppSidebar.vue";
import NotificationPopover from "../components/NotificationPopover.vue";
import { useRouteNavigation } from "../composables/useRouteNavigation";
import { useScholarData } from "../composables/useScholarData";

const { t, locale } = useI18n();
const { profileName, profileLevel, hydrate } = useScholarData();

type NotificationItem = {
  id: string;
  title: string;
  time: string;
};

type StandingRow = {
  rank: string;
  scholar: string;
  guild: string;
  xp: string;
  status?: string;
  tone: "gold" | "silver" | "bronze" | "normal" | "current" | "danger";
  trend?: "up" | "down" | "flat";
  isCurrent?: boolean;
};

const leaderboardData = ref<LeaderboardEntry[]>([]);
const isLoading = ref(false);
const hasMore = ref(false);
const scope = ref<"global" | "friends">("global");
const pageSize = 25;

const viewerName = ref<string>("");
const viewerXp = ref(0);
const viewerLevel = ref(1);
const viewerRank = ref(0);
const viewerEnergyPoints = ref(0);
const viewerDailyFocus = ref<DailyFocusItem[]>([]);
const refreshIntervalMs = 30 * 60 * 1000;
let refreshTimer: ReturnType<typeof setInterval> | null = null;

const toStandingRow = (entry: LeaderboardEntry): StandingRow => {
  let tone: StandingRow["tone"] = "normal";
  let status: StandingRow["status"];

  if (entry.rank === 1) {
    tone = "gold";
    status = t("leaderboard.status.topSage");
  } else if (entry.rank === 2) {
    tone = "silver";
  } else if (entry.rank === 3) {
    tone = "bronze";
  } else if (entry.rank >= 41) {
    tone = "danger";
    status = t("leaderboard.status.danger");
  }

  return {
    rank: String(entry.rank),
    scholar: entry.display_name || t("leaderboard.defaultScholar"),
    guild: "",
    xp: new Intl.NumberFormat(locale.value).format(entry.total_xp),
    status,
    tone,
  };
};

const standings = computed<StandingRow[]>(() => {
  const _ = locale.value;
  return leaderboardData.value.map(toStandingRow);
});

const fetchLeaderboard = async (reset = false) => {
  if (isLoading.value) {
    return;
  }
  isLoading.value = true;
  try {
    const offset = reset ? 0 : leaderboardData.value.length;
    const snapshot = await getLeaderboardSnapshot(pageSize, offset, scope.value);

    viewerName.value = snapshot.viewer.display_name;
    viewerXp.value = snapshot.viewer.total_xp;
    viewerLevel.value = snapshot.viewer.level;
    viewerRank.value = snapshot.viewer.rank;
    viewerEnergyPoints.value = snapshot.viewer.energy_points;
    viewerDailyFocus.value = snapshot.viewer.daily_focus;

    leaderboardData.value = reset
      ? snapshot.entries
      : [...leaderboardData.value, ...snapshot.entries];
    hasMore.value = snapshot.has_more;
  } catch (error) {
    console.error("Failed to fetch leaderboard:", error);
    if (reset) {
      leaderboardData.value = [];
      hasMore.value = false;
    }
  } finally {
    isLoading.value = false;
  }
};

const handleScopeChange = async (nextScope: "global" | "friends") => {
  scope.value = nextScope;
  await fetchLeaderboard(true);
};

const handleLoadMore = async () => {
  if (!hasMore.value) {
    return;
  }
  await fetchLeaderboard(false);
};

const handleVisibilityRefresh = async () => {
  if (!document.hidden) {
    await fetchLeaderboard(true);
  }
};

const handleWindowFocusRefresh = async () => {
  await fetchLeaderboard(true);
};

onMounted(async () => {
  await Promise.all([hydrate(), fetchLeaderboard(true)]);
  refreshTimer = setInterval(() => {
    void fetchLeaderboard(true);
  }, refreshIntervalMs);
  document.addEventListener("visibilitychange", handleVisibilityRefresh);
  window.addEventListener("focus", handleWindowFocusRefresh);
});

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
  document.removeEventListener("visibilitychange", handleVisibilityRefresh);
  window.removeEventListener("focus", handleWindowFocusRefresh);
});

// Update document title reactively when locale changes
watch(locale, () => {
  document.title = t("leaderboard.metaTitle");
});

const { currentPath, navigateTo, routingTarget } = useRouteNavigation();

const notificationVisible = ref(false);
const notifications = ref<NotificationItem[]>([]);

const toggleNotifications = () => {
  notificationVisible.value = !notificationVisible.value;
};

const closeNotifications = () => {
  notificationVisible.value = false;
};

const userXp = computed(() => {
  return viewerXp.value;
});
const progress = computed(() => {
  return userXp.value <= 0 ? 0 : Math.round(((userXp.value % 500) / 500) * 100);
});

const userLevel = computed(() => {
  return viewerLevel.value;
});

const userName = computed(() => {
  return viewerName.value || profileName.value;
});

const energyPoints = computed(() => {
  return viewerEnergyPoints.value;
});

const dailyFocusItems = computed(() => {
  return viewerDailyFocus.value.map((item) => ({
    title: item.title,
    progressText: item.progress_text,
  }));
});

const statusClass = (row: StandingRow) => {
  if (row.tone === "gold") {
    return "status-chip status-chip--gold";
  }
  if (row.tone === "silver") {
    return "status-chip status-chip--silver";
  }
  if (row.tone === "bronze") {
    return "status-chip status-chip--bronze";
  }
  if (row.tone === "danger") {
    return "status-chip status-chip--danger";
  }
  return "status-chip";
};
</script>

<template>
  <div class="leaderboard-page">
    <AppSidebar
      :current-path="currentPath"
      :routing-target="routingTarget"
      :profile-name="profileName"
      :profile-level="profileLevel"
      @navigate="navigateTo"
    />

    <main class="main-content">
      <header class="topbar">
        <p class="topbar__title">{{ t("leaderboard.topbarTitle") }}</p>
        <label class="search-box">
          <span aria-hidden="true">⌕</span>
          <input
            type="text"
            :aria-label="t('leaderboard.searchAria')"
            :placeholder="t('leaderboard.searchPlaceholder')"
          />
        </label>
        <button
          class="notify-btn"
          type="button"
          :aria-label="t('leaderboard.notifications')"
          @click="toggleNotifications"
        >
          🔔
        </button>
      </header>

      <NotificationPopover :items="notifications" :visible="notificationVisible" @close="closeNotifications" />

      <section class="content-grid" :aria-busy="isLoading">
        <LeaderboardSummaryPanel
          :progress="progress"
          :user-xp="userXp"
          :user-level="userLevel"
          :user-name="userName"
          :user-rank="viewerRank"
          :energy-points="energyPoints"
          :daily-focus="dailyFocusItems"
        />
        <LeaderboardStandingsTable
          :standings="standings"
          :status-class="statusClass"
          :active-scope="scope"
          :has-more="hasMore"
          :is-loading="isLoading"
          @scope-change="handleScopeChange"
          @load-more="handleLoadMore"
        />
      </section>
    </main>
  </div>
</template>

<style scoped>
.leaderboard-page {
  background: linear-gradient(180deg, var(--color-page-bg) 0%, var(--color-surface-alt) 100%);
  display: grid;
  gap: 24px;
  grid-template-columns: 256px minmax(0, 1fr);
  min-height: 100vh;
  padding: 24px;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-width: 0;
}

.topbar {
  align-items: center;
  display: grid;
  gap: 14px;
  grid-template-columns: auto minmax(0, 1fr) auto;
  min-height: 42px;
  padding: 0;
}

.topbar__title {
  color: var(--color-text-dark);
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
}

.search-box {
  align-items: center;
  background: var(--color-search-bg);
  border: 1px solid var(--color-search-border);
  border-radius: 999px;
  color: var(--color-text-light-slate);
  display: flex;
  font-size: 14px;
  gap: 10px;
  height: 40px;
  justify-self: end;
  max-width: 472px;
  padding: 0 14px;
  width: 100%;
}

.search-box input {
  background: transparent;
  border: 0;
  color: var(--color-text-slate);
  flex: 1;
  font-size: 14px;
  outline: 0;
}

.search-box input::placeholder {
  color: var(--color-text-light-slate);
}

.notify-btn {
  background: transparent;
  border: 0;
  color: var(--color-text-muted-slate);
  cursor: pointer;
  font-size: 18px;
}

.content-grid {
  display: grid;
  gap: 32px;
  grid-template-columns: 298px minmax(0, 1fr);
  margin: 0 auto;
  max-width: 1280px;
  width: 100%;
}

@media (max-width: 1280px) {
  .content-grid {
    grid-template-columns: 280px minmax(0, 1fr);
  }
}

@media (max-width: 1080px) {
  .leaderboard-page {
    grid-template-columns: 1fr;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .leaderboard-page {
    padding: 14px;
  }

  .topbar {
    grid-template-columns: 1fr;
  }

  .content-grid {
    margin: 14px auto;
  }

}
</style>
