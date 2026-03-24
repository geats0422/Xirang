<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { getLeaderboard, type LeaderboardEntry } from "../api/leaderboard";
import LeaderboardStandingsTable from "../components/leaderboard/LeaderboardStandingsTable.vue";
import LeaderboardSummaryPanel from "../components/leaderboard/LeaderboardSummaryPanel.vue";
import AppSidebar from "../components/layout/AppSidebar.vue";
import NotificationPopover from "../components/NotificationPopover.vue";
import { useRouteNavigation } from "../composables/useRouteNavigation";

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
  document.title = "Xi Rang Leaderboard";
  await fetchLeaderboard();
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

const progress = computed(() => Math.round((15420 / 18000) * 100));

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
    <AppSidebar :current-path="currentPath" :routing-target="routingTarget" @navigate="navigateTo" />

    <main class="main-content">
      <header class="topbar">
        <p class="topbar__title">Hall of Sages</p>
        <label class="search-box">
          <span aria-hidden="true">⌕</span>
          <input
            type="text"
            aria-label="Search scholars"
            placeholder="Search for scrolls, scholars, or guilds..."
          />
        </label>
        <button class="notify-btn" type="button" aria-label="Notifications" @click="toggleNotifications">🔔</button>
      </header>

      <NotificationPopover :items="notifications" :visible="notificationVisible" @close="closeNotifications" />

      <section class="content-grid" :aria-busy="isLoading">
        <LeaderboardSummaryPanel :progress="progress" />
        <LeaderboardStandingsTable :standings="standings" :status-class="statusClass" />
      </section>
    </main>
  </div>
</template>

<style scoped>
.leaderboard-page {
  background: linear-gradient(180deg, #f7f9f8 0%, #f1f5f4 100%);
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
  color: #1e293b;
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
}

.search-box {
  align-items: center;
  background: #f8fafc;
  border: 1px solid #dbe2ea;
  border-radius: 999px;
  color: #94a3b8;
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
  color: #334155;
  flex: 1;
  font-size: 14px;
  outline: 0;
}

.search-box input::placeholder {
  color: #94a3b8;
}

.notify-btn {
  background: transparent;
  border: 0;
  color: #64748b;
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
