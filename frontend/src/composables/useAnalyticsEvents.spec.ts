import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import {
  trackEvent,
  useAnalytics,
  ANALYTICS_EVENTS,
  setAnalyticsEnabled,
  type AnalyticsEventName,
} from "./useAnalyticsEvents";

describe("useAnalyticsEvents", () => {
  let consoleLogSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleLogSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    setAnalyticsEnabled(true);
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
  });

  it("defines all required event names", () => {
    const requiredEvents: AnalyticsEventName[] = [
      "upload_started",
      "upload_succeeded",
      "upload_failed",
      "mode_selected",
      "run_started",
      "run_completed",
      "insufficient_balance_triggered",
      "wrong_question_reported",
    ];

    requiredEvents.forEach((eventName) => {
      expect(ANALYTICS_EVENTS[eventName]).toBe(eventName);
    });
  });

  it("trackEvent logs to console with event name", () => {
    trackEvent("mode_selected", { modeId: "speed", modeName: "Speed Survival" });

    expect(console.log).toHaveBeenCalledWith(
      "[Analytics]",
      expect.stringContaining('"event":"mode_selected"')
    );
  });

  it("trackEvent includes timestamp", () => {
    trackEvent("run_started", { modeId: "speed", materialId: "abc123" });

    expect(console.log).toHaveBeenCalledWith(
      "[Analytics]",
      expect.stringContaining('"timestamp"')
    );
  });

  it("trackEvent accepts optional payload", () => {
    trackEvent("upload_started", { fileName: "test.pdf", fileSize: 1024 });

    expect(console.log).toHaveBeenCalledWith(
      "[Analytics]",
      expect.stringContaining('"fileName":"test.pdf"')
    );
  });

  it("trackEvent does nothing when analytics is disabled", () => {
    setAnalyticsEnabled(false);
    trackEvent("mode_selected", { modeId: "speed", modeName: "Speed" });

    expect(console.log).not.toHaveBeenCalled();
  });

  it("useAnalytics returns tracking functions", () => {
    const analytics = useAnalytics();

    expect(analytics.trackEvent).toBe(trackEvent);
    expect(analytics.ANALYTICS_EVENTS).toBe(ANALYTICS_EVENTS);
    expect(analytics.setAnalyticsEnabled).toBe(setAnalyticsEnabled);
  });
});
