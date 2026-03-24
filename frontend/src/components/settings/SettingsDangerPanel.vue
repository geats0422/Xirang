<template>
  <section class="danger-panel">
    <div class="danger-panel__head">⚠ Danger Zone</div>

    <div class="danger-row">
      <div>
        <p class="danger-row__title">Clear Game Data</p>
        <p class="danger-row__desc">This will reset your current quest progress but keep your account.</p>
      </div>
      <button class="danger-btn danger-btn--ghost" type="button">Clear All Data</button>
    </div>

    <div class="danger-row">
      <div>
        <p class="danger-row__title">Delete Account</p>
        <p class="danger-row__desc">Permanently remove your profile and all achievements. This cannot be undone.</p>
      </div>
      <button class="danger-btn danger-btn--solid" type="button">Delete Account</button>
    </div>

    <div class="danger-row">
      <div>
        <p class="danger-row__title">Log Out</p>
        <p class="danger-row__desc">End your current session safely.</p>
      </div>
      <button class="danger-btn danger-btn--logout" type="button">↪ Log Out</button>
    </div>
  </section>
</template>

<style scoped>
.danger-panel {
  background: #fff;
  border: 1px solid #f1d0d0;
  border-radius: 8px;
  margin-top: 16px;
  overflow: hidden;
}

.danger-panel__head {
  background: #fff2f2;
  border-bottom: 1px solid #f1d0d0;
  color: #d24141;
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 700;
  padding: 10px 14px;
}

.danger-row {
  align-items: center;
  border-bottom: 1px solid #f1e0e0;
  display: flex;
  justify-content: space-between;
  padding: 12px 14px;
}

.danger-row:last-child {
  border-bottom: 0;
}

.danger-row__title {
  color: #293640;
  font-size: 14px;
  font-weight: 700;
  margin: 0;
}

.danger-row__desc {
  color: #85949b;
  font-size: 12px;
  margin: 2px 0 0;
}

.danger-btn {
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  height: 32px;
  padding: 0 12px;
}

.danger-btn--ghost {
  background: #fff;
  border: 1px solid #f0bcbc;
  color: #df6a6a;
}

.danger-btn--solid {
  background: #e94a4a;
  border: 1px solid #e94a4a;
  color: #fff;
}

.danger-btn--logout {
  background: #fff;
  border: 1px solid #d8dddf;
  color: #3f4d59;
}

@media (max-width: 768px) {
  .danger-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }
}
</style>
