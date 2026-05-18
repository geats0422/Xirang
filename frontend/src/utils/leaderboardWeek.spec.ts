import { describe, expect, it } from "vitest";

import { getBeijingWeekEndsAt, getCompetitionDaysRemaining } from "./leaderboardWeek";

describe("leaderboardWeek", () => {
  it("returns next Monday midnight in Beijing time for a Monday", () => {
    const endsAt = getBeijingWeekEndsAt(new Date("2026-05-18T00:30:00+08:00"));

    expect(endsAt.toISOString()).toBe("2026-05-24T16:00:00.000Z");
  });

  it("reports 6 days remaining on Monday in Beijing time", () => {
    const days = getCompetitionDaysRemaining({ now: new Date("2026-05-18T08:00:00+08:00") });

    expect(days).toBe(6);
  });

  it("reports 0 days remaining on Sunday in Beijing time", () => {
    const days = getCompetitionDaysRemaining({ now: new Date("2026-05-24T08:00:00+08:00") });

    expect(days).toBe(0);
  });

  it("uses backend week end time when provided", () => {
    const days = getCompetitionDaysRemaining({
      now: new Date("2026-05-20T08:00:00+08:00"),
      weekEndsAt: "2026-05-22T00:00:00+08:00",
    });

    expect(days).toBe(1);
  });
});
