export type AnalyticsEventName =
  | "upload_started"
  | "upload_succeeded"
  | "upload_failed"
  | "mode_selected"
  | "run_started"
  | "run_completed"
  | "insufficient_balance_triggered"
  | "wrong_question_reported";

export interface AnalyticsEventPayload {
  upload_started?: { fileName: string; fileSize: number };
  upload_succeeded?: { fileName: string; questionCount: number };
  upload_failed?: { fileName: string; error: string };
  mode_selected?: { modeId: string; modeName: string };
  run_started?: { modeId: string; materialId: string };
  run_completed?: { modeId: string; xpGained: number; coinsEarned: number };
  insufficient_balance_triggered?: { itemId: string; itemName: string; required: number; current: number };
  wrong_question_reported?: { questionId: string; reason?: string };
}

export const ANALYTICS_EVENTS: Record<AnalyticsEventName, string> = {
  upload_started: "upload_started",
  upload_succeeded: "upload_succeeded",
  upload_failed: "upload_failed",
  mode_selected: "mode_selected",
  run_started: "run_started",
  run_completed: "run_completed",
  insufficient_balance_triggered: "insufficient_balance_triggered",
  wrong_question_reported: "wrong_question_reported",
};

let isAnalyticsEnabled = true;

export function setAnalyticsEnabled(enabled: boolean): void {
  isAnalyticsEnabled = enabled;
}

export function trackEvent<K extends AnalyticsEventName>(
  eventName: K,
  payload?: AnalyticsEventPayload[K]
): void {
  if (!isAnalyticsEnabled) {
    return;
  }

  const timestamp = new Date().toISOString();
  const eventData = {
    event: eventName,
    timestamp,
    ...(payload || {}),
  };

  console.log("[Analytics]", JSON.stringify(eventData));
}

export function useAnalytics() {
  return {
    trackEvent,
    ANALYTICS_EVENTS,
    setAnalyticsEnabled,
  };
}
