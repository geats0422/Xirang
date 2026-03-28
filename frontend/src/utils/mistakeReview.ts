import type { MistakeReviewItem, RunAnswerFeedback, RunQuestion } from "../api/runs";
import { stripQuestionFormatting } from "./questionText";

const normalizeText = (value: string | null | undefined): string | null => {
  if (typeof value !== "string") {
    return null;
  }

  const normalized = stripQuestionFormatting(value).trim();
  return normalized ? normalized : null;
};

export const buildMistakeReviewItem = (
  question: RunQuestion,
  feedback: RunAnswerFeedback | null,
  selectedAnswerText?: string | null,
): MistakeReviewItem | null => {
  if (!feedback) {
    return null;
  }

  const correctAnswerText = feedback.correct_options
    .map((option) => normalizeText(option.text))
    .filter((option): option is string => Boolean(option))
    .join(" / ");

  return {
    question_id: question.id,
    question_text: normalizeText(question.text) ?? question.text,
    selected_answer_text: normalizeText(selectedAnswerText),
    correct_answer_text: correctAnswerText || null,
    explanation: normalizeText(feedback.explanation),
    source_locator: normalizeText(feedback.source_locator),
    supporting_excerpt: normalizeText(feedback.supporting_excerpt),
  };
};
