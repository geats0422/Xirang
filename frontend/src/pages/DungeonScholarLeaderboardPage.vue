<script setup lang="ts">
import { computed, onMounted } from "vue";
import LeaderboardStandingsTable from "../components/leaderboard/LeaderboardStandingsTable.vue";
import LeaderboardSummaryPanel from "../components/leaderboard/LeaderboardSummaryPanel.vue";
import AppSidebar from "../components/layout/AppSidebar.vue";
import { useRouteNavigation } from "../composables/useRouteNavigation";

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

onMounted(() => {
  document.title = "Xi Rang Leaderboard";
});

const standings: StandingRow[] = [
  {
    rank: "1",
    scholar: "Master Jin",
    guild: "Golden Dragon Sect",
    xp: "12,500",
    status: "Top Sage",
    tone: "gold",
  },
  {
    rank: "2",
    scholar: "Adept Mei",
    guild: "Silver Lotus Guild",
    xp: "11,200",
    status: "Rising",
    tone: "silver",
  },
  {
    rank: "3",
    scholar: "Scholar Kenji",
    guild: "Bronze Tiger Clan",
    xp: "10,800",
    status: "Steady",
    tone: "bronze",
  },
  {
    rank: "4",
    scholar: "Disciple Sarah",
    guild: "",
    xp: "9,500",
    tone: "normal",
    trend: "flat",
  },
  {
    rank: "5",
    scholar: "Scholar Li (You)",
    guild: "",
    xp: "9,200",
    tone: "current",
    trend: "up",
    isCurrent: true,
  },
  {
    rank: "6",
    scholar: "Novice Tom",
    guild: "",
    xp: "8,900",
    tone: "normal",
    trend: "down",
  },
  {
    rank: "40",
    scholar: "Wanderer X",
    guild: "",
    xp: "4,100",
    tone: "normal",
    trend: "flat",
  },
  {
    rank: "41",
    scholar: "Junior Sam",
    guild: "",
    xp: "3,900",
    status: "Danger",
    tone: "danger",
  },
  {
    rank: "45",
    scholar: "Sleepy Sage",
    guild: "",
    xp: "3,500",
    status: "Danger",
    tone: "danger",
  },
  {
    rank: "50",
    scholar: "Unknown",
    guild: "",
    xp: "3,100",
    status: "Danger",
    tone: "danger",
  },
];

const { currentPath, navigateTo, routingTarget } = useRouteNavigation();

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
        <button class="notify-btn" type="button" aria-label="Notifications">🔔</button>
      </header>

      <section class="content-grid">
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
