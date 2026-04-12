type WakeupState = "idle" | "waking" | "ready";

let state: WakeupState = "idle";
let wakeupPromise: Promise<boolean> | null = null;

const COLD_START_GRACE_MS = 90_000;

export const getServerWakeupState = (): WakeupState => state;

export const wakeupServer = async (): Promise<boolean> => {
  if (state === "ready") {
    return true;
  }

  if (wakeupPromise) {
    return wakeupPromise;
  }

  wakeupPromise = _doWakeup();
  return wakeupPromise;
};

async function _doWakeup(): Promise<boolean> {
  state = "waking";

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), COLD_START_GRACE_MS);

    const resp = await fetch("/health", {
      method: "GET",
      signal: controller.signal,
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (resp.ok) {
      state = "ready";
      return true;
    }

    state = "idle";
    wakeupPromise = null;
    return false;
  } catch {
    state = "idle";
    wakeupPromise = null;
    return false;
  }
}
