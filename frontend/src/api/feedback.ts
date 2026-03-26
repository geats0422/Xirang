import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type FeedbackType = "typo" | "wrong_answer" | "confusing" | "other";

export type FeedbackCreateInput = {
  question_id: string;
  document_id: string;
  run_id?: string;
  feedback_type: FeedbackType;
  detail_text?: string;
};

export type FeedbackResponse = {
  id: string;
  feedback_type: string;
  detail_text: string | null;
  status: string;
  question_id?: string;
  document_id?: string;
  run_id?: string | null;
  created_at?: string;
};

export type FeedbackListResponse = {
  items: FeedbackResponse[];
  total: number;
};

export type SummarizeFeedbackInput = {
  feedback_ids: string[];
};

export type SummarizeFeedbackResponse = {
  summary: string;
  feedback_count: number;
};

export const submitFeedback = async (input: FeedbackCreateInput): Promise<FeedbackResponse> => {
  return apiRequest<FeedbackResponse>("/api/v1/feedback", {
    method: "POST",
    headers: getAuthHeaders(),
    body: {
      question_id: input.question_id,
      document_id: input.document_id,
      run_id: input.run_id,
      feedback_type: input.feedback_type,
      detail_text: input.detail_text,
    },
  });
};

export const getFeedback = async (feedbackId: string): Promise<FeedbackResponse> => {
  return apiRequest<FeedbackResponse>(`/api/v1/feedback/${encodeURIComponent(feedbackId)}`, {
    headers: getAuthHeaders(),
  });
};

export const listFeedback = async (): Promise<FeedbackListResponse> => {
  return apiRequest<FeedbackListResponse>("/api/v1/feedback", {
    headers: getAuthHeaders(),
  });
};

export const summarizeFeedback = async (
  feedbackIds: string[],
): Promise<SummarizeFeedbackResponse> => {
  return apiRequest<SummarizeFeedbackResponse>("/api/v1/feedback/summarize", {
    method: "POST",
    headers: getAuthHeaders(),
    body: {
      feedback_ids: feedbackIds,
    },
  });
};
