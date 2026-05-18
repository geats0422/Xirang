const BEIJING_OFFSET_MS = 8 * 60 * 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;

const toBeijingDate = (date: Date) => new Date(date.getTime() + BEIJING_OFFSET_MS);

export const getBeijingWeekEndsAt = (now = new Date()): Date => {
  const beijingNow = toBeijingDate(now);
  const utcDay = beijingNow.getUTCDay();
  const mondayBasedDay = utcDay === 0 ? 6 : utcDay - 1;
  const beijingWeekStartUtcMs = Date.UTC(
    beijingNow.getUTCFullYear(),
    beijingNow.getUTCMonth(),
    beijingNow.getUTCDate() - mondayBasedDay,
    0,
    0,
    0,
    0,
  );
  return new Date(beijingWeekStartUtcMs + 7 * DAY_MS - BEIJING_OFFSET_MS);
};

export const getCompetitionDaysRemaining = ({
  now = new Date(),
  weekEndsAt,
}: {
  now?: Date;
  weekEndsAt?: string | null;
}) => {
  const end = weekEndsAt ? new Date(weekEndsAt) : getBeijingWeekEndsAt(now);
  const remainingMs = end.getTime() - now.getTime();
  if (!Number.isFinite(remainingMs) || remainingMs <= DAY_MS) {
    return 0;
  }
  return Math.max(0, Math.ceil(remainingMs / DAY_MS) - 1);
};
