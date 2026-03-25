import { apiRequest } from "./http";

export type LeaderboardEntry = {
  user_id: string;
  display_name: string | null;
  total_xp: number;
  rank: number;
  level?: number;
  energy_points?: number;
  is_current_user?: boolean;
};

export const getLeaderboard = async (limit = 50): Promise<LeaderboardEntry[]> => {
  return apiRequest<LeaderboardEntry[]>(`/api/v1/leaderboard?limit=${limit}`);
};
