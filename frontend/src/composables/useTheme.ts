import { ref } from "vue";

export type Theme = "light" | "dark" | "system";

const THEME_KEY = "xirang-theme";
const MEDIA_QUERY = "(prefers-color-scheme: dark)";

const getStoredTheme = (): Theme => {
  if (typeof window === "undefined") {
    return "light";
  }

  const storedTheme = window.localStorage.getItem(THEME_KEY);
  if (storedTheme === "light" || storedTheme === "dark" || storedTheme === "system") {
    return storedTheme;
  }

  return "light";
};

const theme = ref<Theme>(getStoredTheme());
const actualTheme = ref<"light" | "dark">("light");

const applyTheme = (nextTheme: "light" | "dark") => {
  if (typeof document === "undefined") {
    return;
  }

  document.documentElement.setAttribute("data-theme", nextTheme);
  actualTheme.value = nextTheme;
};

const initTheme = () => {
  if (typeof window === "undefined") {
    return;
  }

  if (theme.value === "system") {
    const prefersDark = window.matchMedia(MEDIA_QUERY).matches;
    applyTheme(prefersDark ? "dark" : "light");
    return;
  }

  applyTheme(theme.value);
};

const setTheme = (nextTheme: Theme) => {
  theme.value = nextTheme;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(THEME_KEY, nextTheme);
  }
  initTheme();
};

if (typeof window !== "undefined") {
  const mediaQuery = window.matchMedia(MEDIA_QUERY);
  mediaQuery.addEventListener("change", () => {
    if (theme.value === "system") {
      initTheme();
    }
  });
}

export const useTheme = () => {
  return {
    theme,
    actualTheme,
    initTheme,
    setTheme,
  };
};
