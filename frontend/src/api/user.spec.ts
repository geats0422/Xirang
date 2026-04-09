import { describe, it, expect, vi, beforeEach } from "vitest";
import { getDailyGoal } from "./user";
import { apiRequest } from "./http";

vi.mock("./http", () => ({
  apiRequest: vi.fn(),
}));

vi.mock("./authHeaders", () => ({
  getAuthHeaders: vi.fn(() => ({ Authorization: "Bearer test" })),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("getDailyGoal", () => {
  it("should return daily goal data", async () => {
    const mockResponse = {
      goal_current: 25,
      goal_total: 60,
      goal_unit: "minutes",
      is_completed: false,
      streak_days: 7,
    };

    (apiRequest as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    const result = await getDailyGoal();

    expect(apiRequest).toHaveBeenCalledWith("/api/v1/user/daily-goal", {
      method: "GET",
      headers: { Authorization: "Bearer test" },
    });

    expect(result.goal_current).toBe(25);
    expect(result.goal_total).toBe(60);
    expect(result.goal_unit).toBe("minutes");
    expect(result.is_completed).toBe(false);
    expect(result.streak_days).toBe(7);
  });

  it("should return completed goal data", async () => {
    const mockResponse = {
      goal_current: 60,
      goal_total: 60,
      goal_unit: "minutes",
      is_completed: true,
      streak_days: 15,
    };

    (apiRequest as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    const result = await getDailyGoal();

    expect(result.is_completed).toBe(true);
    expect(result.streak_days).toBe(15);
  });

  it("should propagate API errors", async () => {
    const error = new Error("Unauthorized");
    (apiRequest as ReturnType<typeof vi.fn>).mockRejectedValue(error);

    await expect(getDailyGoal()).rejects.toThrow("Unauthorized");
  });
});
