import { apiRequest } from "./http";

export type LeaderboardEntry = {
  user_id: string;
  display_name: string | null;
  total_xp: number;
  rank: number;
  level: number;
  energy_points: number;
  is_current_user: boolean;
};

export type DailyFocusItem = {
  document_id: string | null;
  title: string;
  progress_current: number;
  progress_total: number;
  progress_text: string;
};

export type LeaderboardViewer = {
  user_id: string;
  display_name: string;
  total_xp: number;
  rank: number;
  level: number;
  energy_points: number;
  daily_focus: DailyFocusItem[];
};

export type LeaderboardSnapshot = {
  scope: string;
  limit: number;
  offset: number;
  has_more: boolean;
  entries: LeaderboardEntry[];
  viewer: LeaderboardViewer;
};

export const getLeaderboardSnapshot = async (
  limit = 25,
  offset = 0,
): Promise<LeaderboardSnapshot> => {
  return apiRequest<LeaderboardSnapshot>(
    `/api/v1/leaderboard?limit=${limit}&offset=${offset}`,
  );
};

export const getLeaderboard = async (limit = 50): Promise<LeaderboardEntry[]> => {
  const snapshot = await getLeaderboardSnapshot(limit, 0);
  return snapshot.entries;
};
