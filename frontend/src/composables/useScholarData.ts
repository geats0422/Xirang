import { computed, ref } from "vue";
import { type DocumentListItem, listDocuments, uploadDocument } from "../api/documents";
import { ApiError } from "../api/http";
import { getLeaderboard, type LeaderboardEntry } from "../api/leaderboard";
import { getMyProfile } from "../api/profile";
import { listRuns, type RunListItem } from "../api/runs";
import { getSettings, updateSettings, type ThemeKey } from "../api/settings";
import { getShopBalance } from "../api/shop";
import { i18n, SUPPORTED_LOCALES, type SupportedLocale } from "../i18n";

type ProviderConfig = {
  provider: string;
  baseUrl: string;
  models: string[];
};

const DEFAULT_DISPLAY_NAME = "Default User";
const DEFAULT_LEVEL_LABEL = "Level 1 Scholar";

const profileName = ref(DEFAULT_DISPLAY_NAME);
const profileLevel = ref(DEFAULT_LEVEL_LABEL);
const coins = ref(0);
const hasCoinBalance = ref(false);
const streak = ref(0);
const documents = ref<DocumentListItem[]>([]);
const runs = ref<RunListItem[]>([]);
const leaderboard = ref<LeaderboardEntry[]>([]);

const theme = ref<ThemeKey>("system");
const language = ref<SupportedLocale>("en");
const soundEnabled = ref(true);
const hapticEnabled = ref(true);
const dailyReminderEnabled = ref(false);

const modelOptions = ref<string[]>([]);
const activeModel = ref(import.meta.env.VITE_DEFAULT_MODEL || "gpt-4o-mini");
const LANGUAGE_STORAGE_KEY = "xirang:language";
const ACTIVE_MODEL_KEY = "xirang:activeModel";

const applyLanguage = (value: SupportedLocale) => {
  language.value = value;
  i18n.global.locale.value = value as typeof i18n.global.locale.value;
  if (typeof document !== "undefined") {
    document.documentElement.lang = value;
  }
  // Persist language preference to localStorage
  if (typeof window !== "undefined") {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, value);
  }
};

// Restore language preference from localStorage on app initialization
const restoreLanguage = () => {
  if (typeof window === "undefined") {
    return;
  }
  const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (stored && (SUPPORTED_LOCALES as readonly string[]).includes(stored)) {
    applyLanguage(stored as SupportedLocale);
  }
};

const isBootstrapped = ref(false);
let pendingSettingsWrite: Promise<unknown> | null = null;

const normalizeLanguage = (code: unknown, fallback: SupportedLocale = "en"): SupportedLocale => {
  if (typeof code !== "string") {
    return fallback;
  }

  const normalized = code.trim();
  if (normalized.length === 0) {
    return fallback;
  }

  if ((SUPPORTED_LOCALES as readonly string[]).includes(normalized)) {
    return normalized as SupportedLocale;
  }
  const lc = normalized.replace(/_/g, "-").toLowerCase();
  if (lc.startsWith("zh")) {
    return lc.includes("tw") || lc.includes("hant") ? "zh-TW" : "zh-CN";
  }
  if (lc.startsWith("pt")) {
    return "pt";
  }
  if (lc.startsWith("es")) {
    return "es";
  }
  if (lc.startsWith("fr")) {
    return "fr";
  }
  if (lc.startsWith("ru")) {
    return "ru";
  }
  if (lc === "ko-kp") {
    return "ko-KP";
  }
  if (lc.startsWith("ko")) {
    return "ko-KR";
  }
  return fallback;
};

const parseProviderConfig = (): ProviderConfig[] => {
  const raw = import.meta.env.VITE_MODEL_PROVIDER_CONFIG;
  if (!raw || raw.trim().length === 0) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as ProviderConfig[];
    return parsed.filter((item) => item.provider && item.baseUrl && Array.isArray(item.models));
  } catch {
    return [];
  }
};

const isProviderConfigured = (provider: ProviderConfig): boolean => {
  return provider.baseUrl.trim().length > 0 && provider.models.length > 0;
};

const refreshModelOptions = () => {
  const providers = parseProviderConfig();
  const options = providers
    .filter(isProviderConfigured)
    .flatMap((provider) => provider.models)
    .filter((model, index, array) => model && array.indexOf(model) === index);

  modelOptions.value = options.length > 0 ? options : [import.meta.env.VITE_DEFAULT_MODEL || "gpt-4o-mini"];

  if (!modelOptions.value.includes(activeModel.value)) {
    activeModel.value = modelOptions.value[0];
  }

  if (typeof window !== "undefined") {
    const stored = window.localStorage.getItem(ACTIVE_MODEL_KEY)?.trim();
    if (stored && modelOptions.value.includes(stored)) {
      activeModel.value = stored;
    }
  }
};

const normalizeTheme = (value: unknown, fallback: ThemeKey = "system"): ThemeKey => {
  return value === "light" || value === "dark" || value === "system" ? value : fallback;
};

const applyTheme = (value: unknown) => {
  const normalized = normalizeTheme(value, theme.value);
  theme.value = normalized;
  if (typeof document !== "undefined") {
    document.documentElement.dataset.theme = normalized;
  }
};

const calculateStreak = (timestamps: string[]): number => {
  const days = new Set(
    timestamps
      .map((value) => new Date(value))
      .filter((date) => !Number.isNaN(date.valueOf()))
      .map((date) => date.toISOString().slice(0, 10)),
  );

  if (days.size === 0) {
    return 0;
  }

  let count = 0;
  const cursor = new Date();

  while (count < 366) {
    const key = cursor.toISOString().slice(0, 10);
    if (!days.has(key)) {
      break;
    }
    count += 1;
    cursor.setDate(cursor.getDate() - 1);
  }

  return count;
};

const isNotFoundOrUnauthorized = (error: unknown): boolean => {
  if (!(error instanceof ApiError)) {
    return false;
  }
  return error.status === 401 || error.status === 404;
};

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === "object" && value !== null;
};

const hydrate = async () => {
  restoreLanguage();
  refreshModelOptions();

  const writeInFlight = pendingSettingsWrite;
  if (writeInFlight) {
    await writeInFlight.then(
      () => undefined,
      () => undefined,
    );
  }

  const invoke = <T>(factory: () => Promise<T>): Promise<T> => {
    try {
      return factory();
    } catch (error) {
      return Promise.reject(error);
    }
  };

  const [profileResult, balanceResult, docsResult, runsResult, settingsResult, leaderboardResult] =
    await Promise.allSettled([
      invoke(() => getMyProfile()),
      invoke(() => getShopBalance()),
      invoke(() => listDocuments()),
      invoke(() => listRuns()),
      invoke(() => getSettings()),
      invoke(() => getLeaderboard(20)),
    ]);

  if (profileResult.status === "fulfilled") {
    profileName.value = profileResult.value.display_name?.trim() || DEFAULT_DISPLAY_NAME;
    profileLevel.value = profileResult.value.tier_label?.trim() || DEFAULT_LEVEL_LABEL;
  }

  if (balanceResult.status === "fulfilled") {
    const balance = Number(balanceResult.value.balance);
    if (Number.isFinite(balance)) {
      coins.value = balance;
      hasCoinBalance.value = true;
    } else {
      coins.value = 0;
      hasCoinBalance.value = false;
    }
  } else if (!isNotFoundOrUnauthorized(balanceResult.reason)) {
    coins.value = 0;
    hasCoinBalance.value = false;
  }

  if (runsResult.status === "fulfilled") {
    const nextRuns = Array.isArray(runsResult.value)
      ? runsResult.value.filter((item): item is RunListItem => isRecord(item) && typeof item.status === "string")
      : [];
    runs.value = nextRuns;
    const completionDates = nextRuns
      .filter((run) => run.status === "completed")
      .map((run) => run.ended_at)
      .filter((value): value is string => typeof value === "string");
    streak.value = calculateStreak(completionDates);
  } else {
    runs.value = [];
    streak.value = 0;
  }

  if (docsResult.status === "fulfilled") {
    documents.value = Array.isArray(docsResult.value) ? docsResult.value : [];
  } else {
    documents.value = [];
  }

  if (settingsResult.status === "fulfilled") {
    const payload = settingsResult.value;
    if (isRecord(payload)) {
      applyTheme(payload.theme_key);
      applyLanguage(normalizeLanguage(payload.language_code, language.value));
      if (typeof payload.sound_enabled === "boolean") {
        soundEnabled.value = payload.sound_enabled;
      }
      if (typeof payload.haptic_enabled === "boolean") {
        hapticEnabled.value = payload.haptic_enabled;
      }
      if (typeof payload.daily_reminder_enabled === "boolean") {
        dailyReminderEnabled.value = payload.daily_reminder_enabled;
      }
    }
  }

  if (leaderboardResult.status === "fulfilled") {
    leaderboard.value = Array.isArray(leaderboardResult.value) ? leaderboardResult.value : [];
  } else {
    leaderboard.value = [];
  }

  isBootstrapped.value = true;
};

const setActiveModel = (model: string) => {
  if (!modelOptions.value.includes(model)) {
    return;
  }
  activeModel.value = model;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(ACTIVE_MODEL_KEY, model);
  }
};

const updateSettingState = async (patch: {
  theme_key?: ThemeKey;
  language_code?: SupportedLocale;
  sound_enabled?: boolean;
  haptic_enabled?: boolean;
  daily_reminder_enabled?: boolean;
}) => {
  const writePromise = updateSettings(patch);
  pendingSettingsWrite = writePromise;

  try {
    const updated = await writePromise;
    applyTheme(updated.theme_key);
    applyLanguage(normalizeLanguage(updated.language_code, language.value));
    soundEnabled.value = updated.sound_enabled;
    hapticEnabled.value = updated.haptic_enabled;
    dailyReminderEnabled.value = updated.daily_reminder_enabled;
  } catch {
    if (patch.theme_key) {
      applyTheme(patch.theme_key);
    }
    if (patch.language_code) {
      applyLanguage(normalizeLanguage(patch.language_code));
    }
    if (patch.sound_enabled !== undefined) {
      soundEnabled.value = patch.sound_enabled;
    }
    if (patch.haptic_enabled !== undefined) {
      hapticEnabled.value = patch.haptic_enabled;
    }
    if (patch.daily_reminder_enabled !== undefined) {
      dailyReminderEnabled.value = patch.daily_reminder_enabled;
    }
  } finally {
    if (pendingSettingsWrite === writePromise) {
      pendingSettingsWrite = null;
    }
  }
};

const uploadAndRefresh = async (fileList: FileList | File[]) => {
  const files = Array.from(fileList);
  if (files.length === 0) {
    return;
  }

  await Promise.all(files.map((file) => uploadDocument(file)));
  documents.value = await listDocuments();
};

const completedRuns = computed(() =>
  (Array.isArray(runs.value) ? runs.value : []).filter(
    (run) => isRecord(run) && typeof run.status === "string" && run.status === "completed",
  ).length,
);

export const useScholarData = () => {
  return {
    activeModel,
    applyLanguage,
    applyTheme,
    coins,
    hasCoinBalance,
    completedRuns,
    dailyReminderEnabled,
    documents,
    hapticEnabled,
    hydrate,
    isBootstrapped,
    language,
    leaderboard,
    modelOptions,
    profileLevel,
    profileName,
    runs,
    soundEnabled,
    streak,
    theme,
    setActiveModel,
    updateSettingState,
    uploadAndRefresh,
  };
};
