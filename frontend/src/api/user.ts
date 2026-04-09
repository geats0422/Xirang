import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type DailyGoalResponse = {
  goal_current: number;
  goal_total: number;
  goal_unit: string;
  is_completed: boolean;
  streak_days: number;
};

export const getDailyGoal = async (): Promise<DailyGoalResponse> => {
  return apiRequest<DailyGoalResponse>("/api/v1/user/daily-goal", {
    method: "GET",
    headers: getAuthHeaders(),
  });
};
