import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type RunQuestionOption = {
  id: string;
  text: string;
};

export type RunQuestion = {
  id: string;
  text: string;
  question_type?: string;
  blank_count?: number | null;
  options: RunQuestionOption[];
};

export type RunMode = "endless" | "speed" | "draft" | "review";

export type CreateRunResponse = {
  run_id: string;
  mode: string;
  status: string;
  run_state: Record<string, unknown>;
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
  path_id?: string | null;
  goal_current?: number;
  goal_total?: number | null;
};

export type RunPathOption = {
  path_id: string;
  label: string;
  kind: string;
  description: string;
  goal_total: number;
  status?: "locked" | "unlocked" | "completed";
};

export type RunPathOptionsResponse = {
  mode: RunMode;
  options: RunPathOption[];
};

export type QuestionFeedback = {
  correct_answer: string | null;
  correct_option_ids: string[];
  explanation: string | null;
};

export type SubmitAnswerResponse = {
  is_correct: boolean;
  answer: {
    id: string;
    question_id: string;
    selected_option_ids: string[];
    is_correct: boolean;
  };
  feedback: QuestionFeedback;
  run: {
    id: string;
    status: string;
    score: number;
    state: Record<string, unknown>;
  };
  settlement: SettlementPayload | null;
};

export type UseReviveResponse = {
  run: {
    id: string;
    status: string;
    score: number;
    state: Record<string, unknown>;
  };
  coin_balance: number;
  revive_cost: number;
};

export type RunListItem = {
  id: string;
  status: string;
  mode?: string;
  run_state?: Record<string, unknown>;
  started_at?: string;
  ended_at?: string | null;
  score?: number;
};

export const createRun = async (
  documentId: string | undefined,
  mode: RunMode,
  questionCount = 1,
  pathId?: string,
  mistakeReview?: boolean,
): Promise<CreateRunResponse> => {
  const body: Record<string, unknown> = {
    mode,
    question_count: questionCount,
    path_id: pathId,
    mistake_review: mistakeReview,
  };

  if (documentId) {
    body.document_id = documentId;
  }

  return apiRequest<CreateRunResponse>("/api/v1/runs", {
    method: "POST",
    headers: getAuthHeaders(),
    body,
  });
};

export const listRunPathOptions = async (
  documentId: string | undefined,
  mode: RunMode,
): Promise<RunPathOptionsResponse> => {
  const encodedMode = encodeURIComponent(mode);
  const documentQuery = documentId
    ? `&document_id=${encodeURIComponent(documentId)}`
    : "";
  return apiRequest<RunPathOptionsResponse>(
    `/api/v1/runs/path-options?mode=${encodedMode}${documentQuery}`,
    {
      headers: getAuthHeaders(),
    },
  );
};

export const submitAnswer = async (
  runId: string,
  questionId: string,
  selectedOptionIds: string[],
  answerTimeMs?: number,
  textAnswer?: string,
): Promise<SubmitAnswerResponse> => {
  return apiRequest<SubmitAnswerResponse>(`/api/v1/runs/${runId}/answers`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: {
      question_id: questionId,
      selected_option_ids: selectedOptionIds,
      answer_time_ms: answerTimeMs,
      text_answer: textAnswer,
    },
  });
};

export const listRuns = async (): Promise<RunListItem[]> => {
  return apiRequest<RunListItem[]>("/api/v1/runs", {
    headers: getAuthHeaders(),
  });
};

export const useRunRevive = async (runId: string): Promise<UseReviveResponse> => {
  return apiRequest<UseReviveResponse>(`/api/v1/runs/${runId}/revive`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
};
