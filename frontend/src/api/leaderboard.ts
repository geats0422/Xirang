import { apiRequest } from "./http";

export type LeaderboardEntry = {
  user_id: string;
  display_name: string | null;
  total_xp: number;
  weekly_xp?: number;
  rank: number;
  level: number;
  tier_key?: string;
  tier_name?: string;
  projected_tier_name?: string;
  energy_points: number;
  is_current_user: boolean;
  is_promotion_zone?: boolean;
  is_demotion_zone?: boolean;
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
  weekly_xp?: number;
  rank: number;
  level: number;
  tier_key?: string;
  tier_name?: string;
  projected_tier_name?: string;
  energy_points: number;
  is_promotion_zone?: boolean;
  is_demotion_zone?: boolean;
  daily_focus: DailyFocusItem[];
};

export type LeaderboardSnapshot = {
  scope: string;
  limit: number;
  offset: number;
  week_starts_at?: string | null;
  week_ends_at?: string | null;
  promotion_cutoff_rank?: number;
  demotion_count?: number;
  participants_count?: number;
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
