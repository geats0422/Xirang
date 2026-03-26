<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { getLeaderboard, type LeaderboardEntry } from "../api/leaderboard";
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

const toStandingRow = (entry: LeaderboardEntry): StandingRow => {
  let tone: StandingRow["tone"] = "normal";
  let status: StandingRow["status"];

  if (entry.rank === 1) {
    tone = "gold";
    status = "Top Sage";
  } else if (entry.rank === 2) {
    tone = "silver";
  } else if (entry.rank === 3) {
    tone = "bronze";
  } else if (entry.rank >= 41) {
    tone = "danger";
    status = "Danger";
  }

  return {
    rank: String(entry.rank),
    scholar: entry.display_name ?? `Scholar ${entry.user_id.slice(0, 6)}`,
    guild: "",
    xp: new Intl.NumberFormat("en-US").format(entry.total_xp),
    status,
    tone,
  };
};

const standings = computed<StandingRow[]>(() => leaderboardData.value.map(toStandingRow));

const fetchLeaderboard = async () => {
  isLoading.value = true;
  try {
    leaderboardData.value = await getLeaderboard();
  } catch (error) {
    console.error("Failed to fetch leaderboard:", error);
    leaderboardData.value = [];
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  await Promise.all([hydrate(), fetchLeaderboard()]);
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

// User progress - if no data or empty, show 0
const userXp = computed(() => {
  // When leaderboard is empty, user has 0 XP
  if (!leaderboardData.value || leaderboardData.value.length === 0) {
    return 0;
  }
  const entry = leaderboardData.value.find((e) => e.is_current_user);
  return entry?.total_xp ?? 0;
});
const progress = computed(() => {
  if (userXp.value === 0) return 0;
  return Math.round((userXp.value / 18000) * 100);
});

// User level - if no data, show 1 (novice)
const userLevel = computed(() => {
  if (!leaderboardData.value || leaderboardData.value.length === 0) {
    return 1;
  }
  const entry = leaderboardData.value.find((e) => e.is_current_user);
  return entry?.level ?? 1;
});

// User name - if no data, show default
const userName = computed(() => {
  if (!leaderboardData.value || leaderboardData.value.length === 0) {
    return profileName.value;
  }
  const entry = leaderboardData.value.find((e) => e.is_current_user);
  return entry?.display_name || profileName.value;
});

// Energy points - if no data, show 0
const energyPoints = computed(() => {
  if (!leaderboardData.value || leaderboardData.value.length === 0) {
    return 0;
  }
  const entry = leaderboardData.value.find((e) => e.is_current_user);
  return entry?.energy_points ?? 0;
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
          :energy-points="energyPoints"
        />
        <LeaderboardStandingsTable :standings="standings" :status-class="statusClass" />
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
