<script setup lang="ts">
defineProps<{
  progress: number;
}>();
</script>

<template>
  <div class="left-panel-wrap">
    <article class="profile-panel">
      <div class="hero-glow" aria-hidden="true" />
      <div class="avatar-wrap">
        <div class="avatar">🧑</div>
        <span class="energy-pill">✪ 850</span>
      </div>
      <h1>Scholar Li</h1>
      <p class="level">Level 42 • Wandering Sage</p>

      <div class="stat-card">
        <span>TOTAL XP</span>
        <strong>15,420</strong>
      </div>

      <div class="league-card">
        <div class="league-head">
          <span>♠</span>
          <span>Silver Jade League</span>
        </div>
        <div class="progress-track" role="presentation">
          <span class="progress-fill" :style="{ width: `${progress}%` }" />
        </div>
        <p>Next Tier: 18,000 XP</p>
      </div>

      <div class="badge-card">
        <span class="badge-icon">◉</span>
        <div>
          <p>Ghost Score</p>
          <p>Blue Flame Badge Acquired</p>
        </div>
      </div>
    </article>

    <article class="focus-card">
      <p class="focus-label">DAILY FOCUS</p>
      <div class="focus-body">
        <span class="focus-icon">📖</span>
        <div>
          <p>Read "The Art of War"</p>
          <p>Progress: 2/5 Chapters</p>
        </div>
      </div>
    </article>
  </div>
</template>

<style scoped>
.left-panel-wrap {
  align-content: start;
  display: grid;
  gap: 18px;
}

.profile-panel {
  background: linear-gradient(160deg, #6cb79f 0%, #4dd696 65%, #47b594 100%);
  border: 1px solid rgba(58, 125, 99, 0.35);
  border-radius: 12px;
  box-shadow: 0 12px 34px -22px rgba(15, 23, 42, 0.55);
  overflow: hidden;
  padding: 20px 18px 18px;
  position: relative;
}

.hero-glow {
  background: radial-gradient(circle, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0) 70%);
  height: 180px;
  left: 50%;
  pointer-events: none;
  position: absolute;
  top: 14px;
  transform: translateX(-50%);
  width: 180px;
}

.avatar-wrap {
  display: grid;
  justify-items: center;
  position: relative;
}

.avatar {
  align-items: center;
  background: linear-gradient(180deg, #fff 0%, #ebf3f2 100%);
  border: 3px solid rgba(17, 116, 111, 0.6);
  border-radius: 999px;
  box-shadow: 0 8px 20px -12px rgba(15, 23, 42, 0.4);
  display: inline-flex;
  font-size: 56px;
  height: 96px;
  justify-content: center;
  margin-top: 6px;
  width: 96px;
}

.energy-pill {
  align-items: center;
  background: #0f172a;
  border: 2px solid #ffffff;
  border-radius: 999px;
  color: #22d3ee;
  display: inline-flex;
  font-family: var(--font-serif);
  font-size: 12px;
  font-weight: 700;
  gap: 4px;
  height: 24px;
  padding: 0 8px;
  position: absolute;
  right: calc(50% - 58px);
  top: 82px;
}

.profile-panel h1 {
  color: #0f172a;
  font-family: var(--font-serif);
  font-size: 20px;
  line-height: 1.4;
  margin: 12px 0 0;
  text-align: center;
}

.level {
  color: #2f7663;
  font-size: 14px;
  line-height: 1.45;
  margin: 2px 0 0;
  text-align: center;
}

.stat-card,
.league-card,
.badge-card {
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 9px;
  margin-top: 12px;
}

.stat-card {
  align-items: center;
  display: flex;
  justify-content: space-between;
  padding: 13px 12px;
}

.stat-card span {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.stat-card strong {
  color: #3a7d63;
  font-family: "Liberation Mono", monospace;
  font-size: 18px;
}

.league-card {
  background: linear-gradient(90deg, rgba(248, 250, 252, 0.95), rgba(236, 253, 245, 0.65));
  padding: 12px;
}

.league-head {
  align-items: center;
  color: #334155;
  display: flex;
  font-size: 12px;
  font-weight: 700;
  gap: 6px;
}

.progress-track {
  background: #e2e8f0;
  border-radius: 999px;
  height: 6px;
  margin-top: 12px;
  overflow: hidden;
}

.progress-fill {
  background: linear-gradient(90deg, #108b96 0%, #3a7d63 100%);
  display: block;
  height: 100%;
}

.league-card p {
  color: #94a3b8;
  font-size: 10px;
  margin: 8px 0 0;
  text-align: right;
}

.badge-card {
  align-items: center;
  background: #eff6ff;
  border-color: #dbeafe;
  display: flex;
  gap: 12px;
  padding: 12px;
}

.badge-icon {
  align-items: center;
  background: #dbeafe;
  border-radius: 999px;
  color: #2563eb;
  display: inline-flex;
  font-size: 16px;
  height: 30px;
  justify-content: center;
  width: 30px;
}

.badge-card p {
  margin: 0;
}

.badge-card p:first-child {
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.badge-card p:last-child {
  color: rgba(37, 99, 235, 0.85);
  font-size: 10px;
}

.focus-card {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(58, 125, 99, 0.12);
  border-radius: 12px;
  padding: 14px;
}

.focus-label {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  margin: 0;
}

.focus-body {
  align-items: center;
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.focus-icon {
  align-items: center;
  background: #fdf3c7;
  border-radius: 8px;
  display: inline-flex;
  font-size: 20px;
  height: 30px;
  justify-content: center;
  width: 30px;
}

.focus-body p {
  margin: 0;
}

.focus-body p:first-child {
  color: #1e293b;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.4;
}

.focus-body p:last-child {
  color: #64748b;
  font-size: 12px;
  line-height: 1.35;
}
</style>
