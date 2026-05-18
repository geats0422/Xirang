import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { i18n } from "./i18n";
import { ROUTES } from "./constants/routes";
import { AUTH_SESSION_CLEARED_EVENT, isAuthenticated } from "./utils/auth";
import "./styles/tokens.css";
import "./styles/markdown.css";
import "./styles/themes/light.css";
import "./styles/themes/dark.css";

const PUBLIC_PATHS = new Set<string>([
  ROUTES.landing,
  ROUTES.login,
  ROUTES.signUp,
  ROUTES.privacyPolicy,
  ROUTES.helpCenter,
  ROUTES.termsOfService,
  ROUTES.features,
  ROUTES.pricing,
]);

const isProtectedPath = (path: string): boolean => !PUBLIC_PATHS.has(path);

router.beforeEach((to) => {
  if (isProtectedPath(to.path) && !isAuthenticated()) {
    return ROUTES.login;
  }
  return true;
});

window.addEventListener(AUTH_SESSION_CLEARED_EVENT, () => {
  if (isProtectedPath(router.currentRoute.value.path)) {
    void router.replace(ROUTES.login);
  }
});

createApp(App).use(router).use(i18n).mount("#app");
