import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type MistakeRecord = {
  id: string;
  user_id: string;
  question_id: string;
  document_id: string;
  run_id: string;
  explanation: string | null;
  created_at: string;
};

export type MistakeListResponse = {
  items: MistakeRecord[];
  total: number;
};

export type ExplainMistakeRequest = {
  question_text: string;
  document_context?: string;
};

export type ExplainMistakeResponse = {
  mistake_id: string;
  explanation: string;
};

// Create a new mistake record
export const createMistake = async (
  questionId: string,
  documentId: string,
  runId: string,
): Promise<MistakeRecord> => {
  return apiRequest<MistakeRecord>(
    `/api/v1/review/mistakes?question_id=${encodeURIComponent(questionId)}&document_id=${encodeURIComponent(documentId)}&run_id=${encodeURIComponent(runId)}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
};

// Get a specific mistake
export const getMistake = async (mistakeId: string): Promise<MistakeRecord> => {
  return apiRequest<MistakeRecord>(`/api/v1/review/mistakes/${encodeURIComponent(mistakeId)}`, {
    headers: getAuthHeaders(),
  });
};

// List all mistakes for the current user
export const listMistakes = async (): Promise<MistakeListResponse> => {
  return apiRequest<MistakeListResponse>("/api/v1/review/mistakes", {
    headers: getAuthHeaders(),
  });
};

// Explain a mistake (get LLM-generated explanation)
export const explainMistake = async (
  mistakeId: string,
  request: ExplainMistakeRequest,
): Promise<ExplainMistakeResponse> => {
  return apiRequest<ExplainMistakeResponse>(
    `/api/v1/review/mistakes/${encodeURIComponent(mistakeId)}/explain`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: request,
    },
  );
};
