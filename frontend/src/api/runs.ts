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
  path_version_id?: string;
  level_node_id?: string;
};

export type RunPathOptionsResponse = {
  mode: "endless" | "speed" | "draft";
  generation_status?: "ready" | "generating" | "failed";
  path_version_id?: string;
  version_no?: number;
  job_id?: string | null;
  options: RunPathOption[];
};

export type RunPathRegenerationResponse = {
  generation_status: "generating" | "ready" | "failed";
  mode: "endless" | "speed" | "draft";
  path_version_id?: string;
  next_version_no?: number;
  job_id?: string | null;
};

export type CreateRunOptions = {
  pathId?: string;
  pathVersionId?: string;
  levelNodeId?: string;
  isLegendReview?: boolean;
};

export type SubmitAnswerResponse = {
  is_correct: boolean;
  run: {
    id: string;
    status: string;
    score: number;
    state: Record<string, unknown>;
  };
  settlement: SettlementPayload | null;
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
  documentId: string,
  mode: "endless" | "speed" | "draft",
  questionCount = 1,
  options: CreateRunOptions = {},
): Promise<CreateRunResponse> => {
  return apiRequest<CreateRunResponse>("/api/v1/runs", {
    method: "POST",
    headers: getAuthHeaders(),
    body: {
      document_id: documentId,
      mode,
      question_count: questionCount,
      path_id: options.pathId,
      path_version_id: options.pathVersionId,
      level_node_id: options.levelNodeId,
      is_legend_review: options.isLegendReview ?? false,
    },
  });
};

export const listRunPathOptions = async (
  documentId: string,
  mode: "endless" | "speed" | "draft",
): Promise<RunPathOptionsResponse> => {
  const encodedDocumentId = encodeURIComponent(documentId);
  const encodedMode = encodeURIComponent(mode);
  return apiRequest<RunPathOptionsResponse>(
    `/api/v1/runs/path-options?mode=${encodedMode}&document_id=${encodedDocumentId}`,
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
): Promise<SubmitAnswerResponse> => {
  return apiRequest<SubmitAnswerResponse>(`/api/v1/runs/${runId}/answers`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: {
      question_id: questionId,
      selected_option_ids: selectedOptionIds,
      answer_time_ms: answerTimeMs,
    },
  });
};

export const listRuns = async (): Promise<RunListItem[]> => {
  return apiRequest<RunListItem[]>("/api/v1/runs", {
    headers: getAuthHeaders(),
  });
};


export const regenerateRunPath = async (
  documentId: string,
  mode: "endless" | "speed" | "draft",
): Promise<RunPathRegenerationResponse> => {
  return apiRequest<RunPathRegenerationResponse>("/api/v1/runs/path-regenerations", {
    method: "POST",
    headers: getAuthHeaders(),
    body: {
      document_id: documentId,
      mode,
    },
  });
};
