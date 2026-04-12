import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type StageStatus = "locked" | "unlocked" | "completed";

export type LearningPathStage = {
  stage_index: number;
  stage_id: string;
  status: StageStatus;
  best_run_id: string | null;
  best_score: number;
  completed_at: string | null;
};

export type LearningPathResponse = {
  document_id: string;
  mode: string;
  stages: LearningPathStage[];
  current_stage_index: number;
  completed_stages_count: number;
  total_stages_count: number;
};

export const getLearningPath = async (
  documentId: string,
  mode: "speed" | "draft" | "endless",
): Promise<LearningPathResponse> => {
  return apiRequest<LearningPathResponse>(
    `/api/v1/learning-paths?document_id=${encodeURIComponent(documentId)}&mode=${encodeURIComponent(mode)}`,
    { headers: getAuthHeaders() },
  );
};
