import { apiRequest } from "./http";

export type LeaderboardEntry = {
  user_id: string;
  display_name: string | null;
  total_xp: number;
  rank: number;
};

export const getLeaderboard = async (limit = 50): Promise<LeaderboardEntry[]> => {
  return apiRequest<LeaderboardEntry[]>(`/api/v1/leaderboard?limit=${limit}`);
};
