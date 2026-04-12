export const toDate = (value: unknown): Date | null => {
  if (typeof value !== "string") {
    return null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? null : parsed;
};

export const isSameLocalDay = (left: Date, right: Date): boolean => {
  return left.getFullYear() === right.getFullYear()
    && left.getMonth() === right.getMonth()
    && left.getDate() === right.getDate();
};

export const getDaysRemainingInMonth = (date: Date): number => {
  const totalDaysInMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  return Math.max(0, totalDaysInMonth - date.getDate());
};

export const getNextDailyResetTime = (date: Date): Date => {
  const next = new Date(date);
  next.setHours(24, 0, 0, 0);
  return next;
};

export const getHoursUntilReset = (date: Date): number => {
  const nextReset = getNextDailyResetTime(date);
  const diffMs = Math.max(0, nextReset.getTime() - date.getTime());
  return Math.ceil(diffMs / (1000 * 60 * 60));
};

export const MONTHLY_PROGRESS_STORAGE_PREFIX = "xirang:quests:monthly-progress";
export const MONTHLY_PROGRESS_TARGET = 30;

export const getMonthlyStorageKey = (date: Date): string => {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${MONTHLY_PROGRESS_STORAGE_PREFIX}:${date.getFullYear()}-${month}`;
};

export const readMonthlyDailyMap = (date: Date): Record<string, number> => {
  if (typeof window === "undefined") {
    return {};
  }
  const key = getMonthlyStorageKey(date);
  const raw = window.localStorage.getItem(key);
  if (!raw) {
    return {};
  }
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    return Object.entries(parsed).reduce<Record<string, number>>((acc, [day, count]) => {
      if (typeof count === "number" && Number.isFinite(count) && count >= 0) {
        acc[day] = Math.min(MONTHLY_PROGRESS_TARGET, Math.floor(count));
      }
      return acc;
    }, {});
  } catch {
    return {};
  }
};

export const writeMonthlyDailyMap = (date: Date, map: Record<string, number>) => {
  if (typeof window === "undefined") {
    return;
  }
  const key = getMonthlyStorageKey(date);
  window.localStorage.setItem(key, JSON.stringify(map));
};
