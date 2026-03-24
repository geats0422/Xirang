<template>
  <section class="panel">
    <div class="panel__header">
      <span class="panel__icon">⌘</span>
      <h3>The Forge Engine</h3>
    </div>

    <div class="forge-wrap">
      <div class="forge-head">
        <span>Active Intelligence Model</span>
        <span class="ai-powered">✦ AI POWERED</span>
      </div>

      <div class="model-grid">
        <article class="model-card model-card--active">
          <div class="model-card__title">Gemini 2.5 Flash</div>
          <p>Fast and efficient. Ideal for quick storytelling and standard quests.</p>
          <div class="tag-row">
            <span>High Speed</span>
            <span>Low Latency</span>
          </div>
        </article>

        <article class="model-card">
          <div class="model-card__title-row">
            <div class="model-card__title">Gemini 3.1 Pro</div>
            <span class="pro-chip">PRO</span>
          </div>
          <p>Advanced reasoning for complex campaigns and deep lore generation.</p>
          <div class="tag-row">
            <span>Deep Logic</span>
            <span>Creative</span>
          </div>
        </article>
      </div>

      <div class="forge-note">ⓘ The Forge Engine powers dynamic storytelling. Pro models may consume more energy (credits) but provide richer narrative depth.</div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: #ffffff;
  border: 1px solid #e6ece8;
  border-radius: 8px;
  margin-top: 16px;
  overflow: hidden;
}

.panel__header {
  align-items: center;
  border-bottom: 1px solid #edf1ee;
  display: flex;
  gap: 10px;
  padding: 14px 16px;
}

.panel__icon {
  color: #728a8d;
  font-size: 16px;
}

.panel__header h3 {
  color: #25333d;
  font-family: var(--font-serif);
  font-size: 24px;
  margin: 0;
}

.forge-wrap {
  padding: 14px 16px 16px;
}

.forge-head {
  align-items: center;
  color: #6c8087;
  display: flex;
  font-size: 12px;
  font-weight: 600;
  justify-content: space-between;
}

.ai-powered {
  color: #2a9ca7;
  font-size: 11px;
  letter-spacing: 0.04em;
}

.model-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 10px;
}

.model-card {
  background: #f7f9f8;
  border: 1px solid #dae3de;
  border-radius: 8px;
  padding: 14px;
}

.model-card--active {
  background: #f3fbfc;
  border-color: #26a0aa;
}

.model-card__title {
  color: #263640;
  font-family: var(--font-serif);
  font-size: 24px;
  line-height: 1;
}

.model-card p {
  color: #93a0a6;
  font-size: 11px;
  line-height: 1.35;
  margin: 8px 0 0;
}

.tag-row {
  display: flex;
  gap: 6px;
  margin-top: 10px;
}

.tag-row span {
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
}

.model-card--active .tag-row span:nth-child(1) {
  background: #d8f5d8;
  color: #498450;
}

.model-card--active .tag-row span:nth-child(2) {
  background: #ddebff;
  color: #5576ac;
}

.model-card:not(.model-card--active) .tag-row span:nth-child(1) {
  background: #ede3ff;
  color: #6b57a7;
}

.model-card:not(.model-card--active) .tag-row span:nth-child(2) {
  background: #ffe9cf;
  color: #b87426;
}

.model-card__title-row {
  align-items: center;
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.pro-chip {
  background: #ffe9c4;
  border-radius: 4px;
  color: #bf852f;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 5px;
}

.forge-note {
  align-items: center;
  background: #f4f8f5;
  border: 1px solid #e0e8e3;
  border-radius: 8px;
  color: #74888f;
  font-size: 12px;
  line-height: 1.45;
  margin-top: 12px;
  padding: 11px 12px;
}

@media (max-width: 1080px) {
  .model-grid {
    grid-template-columns: 1fr;
  }
}
</style>
