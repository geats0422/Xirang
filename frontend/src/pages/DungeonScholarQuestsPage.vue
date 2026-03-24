<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { listDocuments } from "../api/documents";
import { getShopBalance } from "../api/shop";
import AppSidebar from "../components/layout/AppSidebar.vue";
import { ROUTES } from "../constants/routes";
import { useRouteNavigation } from "../composables/useRouteNavigation";

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

onMounted(() => {
  document.title = "Xi Rang Quests";
});

const coinAmount = ref<string>("350");

const hydrateCoinBalance = async () => {
  try {
    const balance = await getShopBalance();
    coinAmount.value = Number(balance.balance).toLocaleString();
  } catch {
    coinAmount.value = "--";
  }
};

const quests = ref<DailyQuest[]>([
  {
    id: "quest-upload",
    title: "Upload and parse 1 new document in the Scroll Archive",
    type: "upload",
    completed: false,
  },
  {
    id: "quest-streak",
    title: "Maintain your learning streak",
    type: "streak",
    completed: false,
  },
  {
    id: "quest-abyss",
    title: "Complete 2 challenges in 'Endless Abyss' mode",
    type: "abyss",
    completed: false,
    locked: true,
  },
]);

const hydrateDailyQuests = async () => {
  try {
    const documents = await listDocuments();
    const hasUploadedDocuments = Array.isArray(documents) && documents.length > 0;

    quests.value = quests.value.map((quest) => {
      if (quest.type === "upload") {
        return {
          ...quest,
          completed: hasUploadedDocuments,
        };
      }

      if (quest.type === "abyss") {
        return {
          ...quest,
          locked: !hasUploadedDocuments,
        };
      }

      return quest;
    });
  } catch {
    quests.value = quests.value.map((quest) => {
      if (quest.type === "abyss") {
        return {
          ...quest,
          locked: true,
        };
      }
      return quest;
    });
  }
};

onMounted(async () => {
  await Promise.all([hydrateCoinBalance(), hydrateDailyQuests()]);
});

const coinLabel = computed(() => `${coinAmount.value} Coins`);

const shopRoute = ROUTES.shop;

const missionCards = computed<MissionCard[]>(() =>
  quests.value.map((quest) => {
    if (quest.type === "abyss") {
      const isLocked = quest.locked === true;
      return {
        id: quest.id,
        title: quest.title,
        icon: "⚔",
        iconTone: "violet",
        progress: isLocked ? 0 : 50,
        progressLabel: isLocked ? "Locked" : "1/2",
        reward: "Experience Double Card",
        rewardIcon: "🎁",
        action: isLocked ? "Locked" : "Continue",
        actionTone: "ghost",
        disabled: isLocked,
      };
    }

    if (quest.type === "streak") {
      return {
        id: quest.id,
        title: quest.title,
        icon: "✓",
        iconTone: "green",
        progress: quest.completed ? 100 : 0,
        progressLabel: quest.completed ? "Completed" : "In progress",
        reward: "+50",
        rewardIcon: "🪙",
        action: quest.completed ? "Claim Reward" : "Continue",
        actionTone: quest.completed ? "solid" : "ghost",
        disabled: false,
      };
    }

    return {
      id: quest.id,
      title: quest.title,
      icon: "⤴",
      iconTone: "blue",
      progress: quest.completed ? 100 : 0,
      progressLabel: quest.completed ? "Completed" : "0/1",
      reward: "Gold Chest",
      rewardIcon: "🧰",
      action: quest.completed ? "Claim Reward" : "Upload",
      actionTone: "solid",
      disabled: false,
    };
  }),
);

const { currentPath, navigateTo, routingTarget } = useRouteNavigation();
</script>

<template>
  <div class="quests-page">
    <AppSidebar :current-path="currentPath" :routing-target="routingTarget" @navigate="navigateTo" />

    <main class="quests-main">
      <section class="quests-shell">
        <header class="quests-statusbar" aria-label="Quest status">
          <div class="status-pill status-pill--streak">🔥 12 Day Streak</div>
          <button class="status-pill status-pill--coins" type="button" @click="navigateTo(shopRoute)">🪙 {{ coinLabel }}</button>
          <button class="notify-btn" type="button" aria-label="Notifications">
            🔔
            <span class="notify-btn__dot" aria-hidden="true" />
          </button>
        </header>

        <section class="monthly-banner" aria-label="Monthly challenge banner">
          <p class="monthly-banner__eyebrow">MONTHLY CHALLENGE</p>
          <h1>March Special Mission: Spring Voyage</h1>
          <p class="monthly-banner__copy">Complete 30 daily missions to earn a monthly badge</p>

          <div class="monthly-banner__progress-head">
            <span>12 / 30</span>
          </div>

          <div class="progress-track progress-track--banner" role="presentation">
            <span class="progress-fill progress-fill--banner" style="width: 40%" />
          </div>

          <div class="monthly-banner__footer">
            <span>⏰ 20 days remaining</span>
          </div>
        </section>

        <section class="missions-section" aria-label="Daily special missions">
          <div class="section-head">
            <h2>Daily Special Missions</h2>
            <span>↻ Refreshes in 13 hours</span>
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
  background: linear-gradient(180deg, #f7f9f8 0%, #f1f5f4 100%);
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
  background: #fff3e4;
  color: #ea8a2f;
}

.status-pill--coins {
  background: #fff8d6;
  color: #c48a0b;
  cursor: pointer;
}

.notify-btn {
  align-items: center;
  background: transparent;
  border: 0;
  color: #d19b1e;
  cursor: pointer;
  display: inline-flex;
  font-size: 18px;
  height: 36px;
  justify-content: center;
  position: relative;
  width: 36px;
}

.notify-btn__dot {
  background: #ef4444;
  border-radius: 999px;
  height: 8px;
  position: absolute;
  right: 6px;
  top: 6px;
  width: 8px;
}

.monthly-banner {
  background:
    radial-gradient(circle at 85% 26%, rgba(255, 255, 255, 0.22), transparent 22%),
    linear-gradient(90deg, #f17b72 0%, #f17d7b 26%, #c468d8 100%);
  border-radius: 24px;
  color: #ffffff;
  overflow: hidden;
  padding: 26px 28px 24px;
  position: relative;
}

.monthly-banner::after {
  background: radial-gradient(circle, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0) 70%);
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
  color: #ffffff;
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
  background: #e5ecea;
  border-radius: 999px;
  overflow: hidden;
}

.progress-track--banner {
  background: rgba(255, 255, 255, 0.28);
  height: 14px;
  margin-top: 10px;
}

.progress-track--mission {
  flex: 1;
  height: 6px;
}

.progress-fill {
  background: linear-gradient(90deg, #7d58ff 0%, #9f73ff 100%);
  display: block;
  height: 100%;
}

.progress-fill--banner {
  background: #ffffff;
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
  color: #22313c;
  font-size: 32px;
  margin: 0;
}

.section-head span {
  color: #7a8e97;
  font-size: 13px;
  font-weight: 700;
}

.mission-list {
  display: grid;
  gap: 14px;
}

.mission-card {
  align-items: center;
  background: #ffffff;
  border: 1px solid #e3e9e7;
  border-radius: 16px;
  box-shadow: 0 12px 24px -28px rgba(15, 23, 42, 0.45);
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
  color: #ffffff;
  display: inline-flex;
  flex: 0 0 auto;
  font-size: 20px;
  height: 44px;
  justify-content: center;
  width: 44px;
}

.mission-card__icon--violet {
  background: #8b5cf6;
}

.mission-card__icon--green {
  background: #22c55e;
}

.mission-card__icon--blue {
  background: #3b82f6;
}

.mission-card__body {
  min-width: 0;
}

.mission-card h3 {
  color: #22313c;
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
  color: #8a98a0;
  font-size: 12px;
  font-weight: 700;
}

.mission-card__progress-label--done {
  color: #16a34a;
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
  color: #e58b1a;
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
  background: #f2f5f7;
  border: 0;
  border-radius: 12px;
  color: #4d5a64;
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
  background: #0f8a95;
  color: #ffffff;
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
