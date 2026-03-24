import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type RunQuestionOption = {
  id: string;
  text: string;
};

export type RunQuestion = {
  id: string;
  text: string;
  options: RunQuestionOption[];
};

export type CreateRunResponse = {
  run_id: string;
  mode: string;
  status: string;
  questions: RunQuestion[];
};

export type SettlementPayload = {
  run_id: string;
  xp_earned: number;
  coins_earned: number;
  combo_max: number;
  accuracy: number;
  correct_count: number;
  total_count: number;
};

export type SubmitAnswerResponse = {
  is_correct: boolean;
  settlement: SettlementPayload | null;
};

export type RunListItem = {
  id: string;
  status: string;
  mode?: string;
  started_at?: string;
  ended_at?: string | null;
  score?: number;
};

export const createRun = async (
  documentId: string,
  mode: "endless" | "speed" | "draft",
  questionCount = 1,
): Promise<CreateRunResponse> => {
  return apiRequest<CreateRunResponse>("/api/v1/runs", {
    method: "POST",
    headers: getAuthHeaders(),
    body: {
      document_id: documentId,
      mode,
      question_count: questionCount,
    },
  });
};

export const submitAnswer = async (
  runId: string,
  questionId: string,
  selectedOptionIds: string[],
): Promise<SubmitAnswerResponse> => {
  return apiRequest<SubmitAnswerResponse>(`/api/v1/runs/${runId}/answers`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: {
      question_id: questionId,
      selected_option_ids: selectedOptionIds,
    },
  });
};

export const listRuns = async (): Promise<RunListItem[]> => {
  return apiRequest<RunListItem[]>("/api/v1/runs", {
    headers: getAuthHeaders(),
  });
};
