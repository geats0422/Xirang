import { describe, expect, it, beforeEach } from "vitest";
import { useFrontendProgressState } from "./useFrontendProgressState";

describe("useFrontendProgressState", () => {
  beforeEach(() => {
    const state = useFrontendProgressState();
    state.resetAll();
  });

  it("starts with default values", () => {
    const state = useFrontendProgressState();
    expect(state.xp.value).toBe(0);
    expect(state.coins.value).toBe(3450);
    expect(state.streak.value).toBe(0);
    expect(state.comboCount.value).toBe(0);
  });

  it("adds XP and tracks session XP", () => {
    const state = useFrontendProgressState();
    state.addXp(100);
    expect(state.xp.value).toBe(100);
    expect(state.sessionXpGained.value).toBe(100);
  });

  it("adds coins and tracks session coins", () => {
    const state = useFrontendProgressState();
    state.addCoins(50);
    expect(state.coins.value).toBe(3500);
    expect(state.sessionCoinsEarned.value).toBe(50);
  });

  it("spends coins if balance is sufficient", () => {
    const state = useFrontendProgressState();
    const result = state.spendCoins(500);
    expect(result).toBe(true);
    expect(state.coins.value).toBe(2950);
  });

  it("fails to spend coins if balance is insufficient", () => {
    const state = useFrontendProgressState();
    state.resetAll();
    state.coins.value = 100;
    const result = state.spendCoins(500);
    expect(result).toBe(false);
    expect(state.coins.value).toBe(100);
  });

  it("tracks and resets combo", () => {
    const state = useFrontendProgressState();
    state.setCombo(5);
    expect(state.comboCount.value).toBe(5);
    state.incrementCombo();
    expect(state.comboCount.value).toBe(6);
    state.resetCombo();
    expect(state.comboCount.value).toBe(0);
  });

  it("calculates goal progress percentage", () => {
    const state = useFrontendProgressState();
    state.setGoalProgress(5, 10);
    expect(state.goalProgress.value).toBe(50);
  });

  it("resets session without resetting total progress", () => {
    const state = useFrontendProgressState();
    state.addXp(100);
    state.addCoins(50);
    state.setCombo(5);
    state.resetSession();
    expect(state.xp.value).toBe(100);
    expect(state.coins.value).toBe(3500);
    expect(state.sessionXpGained.value).toBe(0);
    expect(state.sessionCoinsEarned.value).toBe(0);
    expect(state.comboCount.value).toBe(0);
  });
});
