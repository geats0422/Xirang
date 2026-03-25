<script setup lang="ts">
import { useI18n } from "vue-i18n";

const { t } = useI18n();

type StandingRow = {
  rank: string;
  scholar: string;
  guild: string;
  xp: string;
  status?: string;
  tone: "gold" | "silver" | "bronze" | "normal" | "current" | "danger";
  trend?: "up" | "down" | "flat";
};

defineProps<{
  statusClass: (row: StandingRow) => string;
  standings: StandingRow[];
}>();
</script>

<template>
  <article class="board-panel" role="table" :aria-label="t('leaderboard.table.aria')">
    <header class="board-header">
      <div>
        <h2>{{ t("leaderboard.table.title") }}</h2>
        <p>{{ t("leaderboard.table.subtitle") }}</p>
      </div>
      <div class="switches" role="group" :aria-label="t('leaderboard.table.scopeAria')">
        <button class="scope-btn scope-btn--active" type="button">{{ t("leaderboard.table.global") }}</button>
        <button class="scope-btn" type="button">{{ t("leaderboard.table.friends") }}</button>
      </div>
    </header>

    <div class="table-head" role="rowgroup">
      <span role="columnheader">{{ t("leaderboard.table.rank") }}</span>
      <span role="columnheader">{{ t("leaderboard.table.scholar") }}</span>
      <span role="columnheader">{{ t("leaderboard.table.weeklyXp") }}</span>
      <span role="columnheader">{{ t("leaderboard.table.status") }}</span>
    </div>

    <div class="table-body" role="rowgroup">
      <div
        v-for="row in standings"
        :key="`${row.rank}-${row.scholar}`"
        class="table-row"
        role="row"
        :aria-label="`${row.rank} ${row.scholar} ${row.xp} XP`"
        :class="{
          'table-row--gold': row.tone === 'gold',
          'table-row--silver': row.tone === 'silver',
          'table-row--bronze': row.tone === 'bronze',
          'table-row--current': row.tone === 'current',
          'table-row--danger': row.tone === 'danger',
        }"
      >
        <div class="rank-col" role="cell">
          <span class="rank-badge">{{ row.rank }}</span>
        </div>

        <div class="scholar-col" role="cell">
          <div class="mini-avatar" :class="`mini-avatar--${row.tone}`">{{ row.scholar.charAt(0) }}</div>
          <div>
            <p>{{ row.scholar }}</p>
            <p v-if="row.guild">{{ row.guild }}</p>
          </div>
        </div>

        <div class="xp-col" role="cell">
          <span>{{ row.xp }}</span>
          <span>{{ t("leaderboard.table.xpSuffix") }}</span>
        </div>

        <div class="status-col" role="cell">
          <span v-if="row.status" :class="statusClass(row)">{{ row.status }}</span>
          <span v-else-if="row.trend === 'up'" class="trend trend--up">↑</span>
          <span v-else-if="row.trend === 'down'" class="trend trend--down">↓</span>
          <span v-else class="trend trend--flat">–</span>
        </div>
      </div>

      <div class="ellipsis-row">•••</div>
      <div class="demotion-row">{{ t("leaderboard.table.demotionZone") }}</div>
      <button class="load-more" type="button">{{ t("leaderboard.table.loadMore") }}</button>
    </div>
  </article>
</template>

<style scoped>
.board-panel {
  backdrop-filter: blur(4px);
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 20px 25px -20px rgba(15, 23, 42, 0.4);
  overflow: hidden;
}

.board-header {
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  padding: 18px 20px;
}

.board-header h2 {
  color: #0f172a;
  font-family: var(--font-serif);
  font-size: 20px;
  line-height: 1.4;
  margin: 0;
}

.board-header p {
  color: #64748b;
  font-size: 14px;
  margin: 4px 0 0;
}

.switches {
  align-items: center;
  display: flex;
  gap: 8px;
}

.scope-btn {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #475569;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  height: 28px;
  min-width: 58px;
  padding: 0 12px;
}

.scope-btn--active {
  background: #3a7d63;
  border-color: #3a7d63;
  color: #ffffff;
}

.table-head {
  background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
  color: #64748b;
  display: grid;
  font-size: 12px;
  font-weight: 700;
  grid-template-columns: 52px minmax(0, 1fr) 132px 86px;
  letter-spacing: 0.05em;
  padding: 12px 20px;
}

.table-body {
  display: grid;
}

.table-row {
  align-items: center;
  border-top: 1px solid #f1f5f9;
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr) 132px 86px;
  min-height: 61px;
  padding: 0 20px;
}

.table-row--gold {
  background: linear-gradient(90deg, rgba(254, 252, 232, 0.8) 0%, #ffffff 100%);
  border-left: 4px solid #d4af37;
  padding-left: 20px;
}

.table-row--silver {
  background: linear-gradient(90deg, rgba(248, 250, 252, 0.8) 0%, #ffffff 100%);
}

.table-row--bronze {
  background: linear-gradient(90deg, rgba(255, 247, 237, 0.62) 0%, #ffffff 100%);
}

.table-row--current {
  background: rgba(58, 125, 99, 0.06);
}

.table-row--danger {
  background: rgba(248, 113, 113, 0.04);
}

.rank-col {
  display: flex;
  justify-content: center;
}

.rank-badge {
  align-items: center;
  border-radius: 999px;
  color: #475569;
  display: inline-flex;
  font-family: var(--font-serif);
  font-size: 16px;
  height: 32px;
  justify-content: center;
  width: 32px;
}

.table-row--gold .rank-badge {
  background: rgba(212, 175, 55, 0.2);
  border: 1px solid rgba(212, 175, 55, 0.4);
  color: #a16207;
}

.table-row--silver .rank-badge {
  background: rgba(226, 232, 240, 0.55);
  border: 1px solid #cbd5e1;
}

.table-row--bronze .rank-badge {
  background: rgba(255, 237, 213, 0.5);
  border: 1px solid #fed7aa;
  color: #9a3412;
}

.scholar-col {
  align-items: center;
  display: flex;
  gap: 12px;
}

.mini-avatar {
  align-items: center;
  background: #e2e8f0;
  border-radius: 999px;
  color: #334155;
  display: inline-flex;
  font-size: 12px;
  font-weight: 700;
  height: 32px;
  justify-content: center;
  width: 32px;
}

.mini-avatar--gold {
  box-shadow: 0 0 0 2px #ffffff, 0 0 0 4px #d4af37;
}

.mini-avatar--silver {
  box-shadow: 0 0 0 2px #ffffff, 0 0 0 4px #c0c0c0;
}

.mini-avatar--bronze {
  box-shadow: 0 0 0 2px #ffffff, 0 0 0 4px #cd7f32;
}

.scholar-col p {
  margin: 0;
}

.scholar-col p:first-child {
  color: #0f172a;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.35;
}

.scholar-col p:last-child {
  color: #64748b;
  font-size: 12px;
  line-height: 1.3;
}

.table-row--gold .scholar-col p:last-child {
  color: #ca8a04;
}

.xp-col {
  align-items: baseline;
  color: #0f172a;
  display: inline-flex;
  font-size: 16px;
  font-weight: 700;
  gap: 4px;
  justify-self: end;
}

.xp-col span:last-child {
  color: #64748b;
  font-size: 12px;
  font-weight: 400;
}

.table-row--current .xp-col {
  color: #2f7b65;
}

.status-col {
  justify-self: center;
}

.status-chip {
  align-items: center;
  border-radius: 999px;
  display: inline-flex;
  font-size: 12px;
  font-weight: 600;
  min-height: 20px;
  padding: 2px 10px;
}

.status-chip--gold {
  background: #fef9c3;
  color: #854d0e;
}

.status-chip--silver {
  background: #f1f5f9;
  color: #1e293b;
}

.status-chip--bronze {
  background: #fff7ed;
  color: #9a3412;
}

.status-chip--danger {
  background: rgba(248, 113, 113, 0.16);
  color: #dc2626;
}

.trend {
  color: #94a3b8;
  font-size: 16px;
  font-weight: 700;
}

.trend--up {
  color: #15803d;
}

.trend--down {
  color: #ef4444;
}

.ellipsis-row {
  color: #cbd5e1;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.2em;
  padding: 8px 0;
  text-align: center;
}

.demotion-row {
  background: rgba(248, 113, 113, 0.1);
  color: #dc2626;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 8px 24px;
  text-align: center;
}

.load-more {
  background: #f8fafc;
  border: 0;
  border-top: 1px solid #e2e8f0;
  color: #2f7b65;
  cursor: pointer;
  font-family: var(--font-serif);
  font-size: 18px;
  font-weight: 700;
  height: 50px;
}

@media (max-width: 768px) {
  .board-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }

  .table-head,
  .table-row {
    grid-template-columns: 52px minmax(0, 1fr) 98px 84px;
    padding: 0 12px;
  }

  .table-head {
    font-size: 11px;
    padding-bottom: 10px;
    padding-top: 10px;
  }

  .scholar-col p:first-child {
    font-size: 16px;
  }

  .scholar-col p:last-child {
    font-size: 12px;
  }

  .xp-col {
    font-size: 16px;
  }

  .xp-col span:last-child {
    font-size: 11px;
  }

  .status-chip {
    font-size: 11px;
    padding: 2px 6px;
  }

  .load-more {
    font-size: 18px;
  }
}
</style>
