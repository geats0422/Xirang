import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type QuestType = "daily" | "monthly" | "special";
export type QuestStatus = "in_progress" | "completed" | "claimed" | "expired";
export type RewardType = "asset" | "item";
export type ActionType = "claim" | "navigate" | "continue";
export type IconTone = "violet" | "green" | "blue" | "amber";

export type QuestAssignment = {
  id: string;
  quest_code: string;
  quest_type: QuestType;
  title_i18n_key: string;
  description_i18n_key: string;
  target_metric: string;
  target_value: number;
  progress_value: number;
  status: QuestStatus;
  reward_type: RewardType;
  reward_asset_code: string | null;
  reward_quantity: number;
  reward_item_code: string | null;
  reward_i18n_key: string;
  reward_icon: string;
  action_i18n_key: string;
  action_type: ActionType;
  navigate_to: string | null;
  icon: string;
  icon_tone: IconTone;
  expires_at: string | null;
  locked: boolean;
};

export type MonthlyProgress = {
  current: number;
  target: number;
  year_month: string;
  days_remaining: number;
  completed_day_keys: string[];
};

export type QuestListResponse = {
  daily_quests: QuestAssignment[];
  daily_refresh_at: string;
  monthly_progress: MonthlyProgress;
  streak_days: number;
  streak_milestone: Record<string, string> | null;
};

export type QuestClaimResponse = {
  assignment_id: string;
  status: "claimed";
  reward_type: string;
  reward_asset_code: string | null;
  reward_quantity: number;
  reward_item_code: string | null;
  coin_balance_after: number | null;
  item_quantity_after: number | null;
};

export const getQuests = async (): Promise<QuestListResponse> => {
  return apiRequest<QuestListResponse>("/api/v1/quests", {
    method: "GET",
    headers: getAuthHeaders(),
  });
};

export const claimQuestReward = async (assignmentId: string): Promise<QuestClaimResponse> => {
  return apiRequest<QuestClaimResponse>(`/api/v1/quests/${assignmentId}/claim`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
};
