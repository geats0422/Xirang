import { createRouter, createWebHistory } from "vue-router";
import { ROUTES } from "../constants/routes";

const EasternFantasyLandingPage = () => import("../pages/EasternFantasyLandingPage.vue");
const DungeonScholarLoginPage = () => import("../pages/DungeonScholarLoginPage.vue");
const DungeonScholarHomePage = () => import("../pages/DungeonScholarHomePage.vue");
const DungeonScholarLibraryPage = () => import("../pages/DungeonScholarLibraryPage.vue");
const DungeonScholarLevelPathPage = () => import("../pages/DungeonScholarLevelPathPage.vue");
const DungeonScholarModeGuidePage = () => import("../pages/DungeonScholarModeGuidePage.vue");
const DungeonScholarModeSelectionPage = () => import("../pages/DungeonScholarModeSelectionPage.vue");
const DungeonScholarEndlessAbyssPage = () => import("../pages/DungeonScholarEndlessAbyssPage.vue");
const DungeonScholarSpeedSurvivalPage = () => import("../pages/DungeonScholarSpeedSurvivalPage.vue");
const DungeonScholarKnowledgeDraftPage = () => import("../pages/DungeonScholarKnowledgeDraftPage.vue");
const DungeonScholarReviewPage = () => import("../pages/DungeonScholarReviewPage.vue");
const DungeonScholarQuestsPage = () => import("../pages/DungeonScholarQuestsPage.vue");
const DungeonScholarShopPage = () => import("../pages/DungeonScholarShopPage.vue");
const DungeonScholarLeaderboardPage = () => import("../pages/DungeonScholarLeaderboardPage.vue");
const DungeonScholarSettingsPage = () => import("../pages/DungeonScholarSettingsPage.vue");
const DungeonScholarProfilePage = () => import("../pages/DungeonScholarProfilePage.vue");
const DungeonScholarPrivacyPolicyPage = () => import("../pages/DungeonScholarPrivacyPolicyPage.vue");
const DungeonScholarHelpCenterPage = () => import("../pages/DungeonScholarHelpCenterPage.vue");
const DungeonScholarTermsPage = () => import("../pages/DungeonScholarTermsPage.vue");
const DungeonScholarFeaturesPage = () => import("../pages/DungeonScholarFeaturesPage.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: ROUTES.landing,
      name: "landing",
      component: EasternFantasyLandingPage,
    },
    {
      path: ROUTES.login,
      name: "login",
      component: DungeonScholarLoginPage,
    },
    {
      path: ROUTES.signUp,
      name: "sign-up",
      component: DungeonScholarLoginPage,
    },
    {
      path: ROUTES.home,
      name: "home",
      component: DungeonScholarHomePage,
    },
    {
      path: ROUTES.library,
      name: "library",
      component: DungeonScholarLibraryPage,
    },
    {
      path: ROUTES.levelPath,
      name: "level-path",
      component: DungeonScholarLevelPathPage,
    },
    {
      path: ROUTES.modeGuide,
      name: "mode-guide",
      component: DungeonScholarModeGuidePage,
    },
    {
      path: ROUTES.gameModes,
      name: "game-modes",
      component: DungeonScholarModeSelectionPage,
    },
    {
      path: ROUTES.endlessAbyss,
      name: "endless-abyss",
      component: DungeonScholarEndlessAbyssPage,
    },
    {
      path: ROUTES.speedSurvival,
      name: "speed-survival",
      component: DungeonScholarSpeedSurvivalPage,
    },
    {
      path: ROUTES.knowledgeDraft,
      name: "knowledge-draft",
      component: DungeonScholarKnowledgeDraftPage,
    },
    {
      path: ROUTES.review,
      name: "review",
      component: DungeonScholarReviewPage,
    },
    {
      path: ROUTES.quests,
      name: "quests",
      component: DungeonScholarQuestsPage,
    },
    {
      path: ROUTES.shop,
      name: "shop",
      component: DungeonScholarShopPage,
    },
    {
      path: ROUTES.leaderboard,
      name: "leaderboard",
      component: DungeonScholarLeaderboardPage,
    },
    {
      path: ROUTES.settings,
      name: "settings",
      component: DungeonScholarSettingsPage,
    },
    {
      path: "/settings/privacy-policy",
      name: "settings-privacy-policy",
      component: DungeonScholarPrivacyPolicyPage,
    },
    {
      path: ROUTES.privacyPolicy,
      name: "privacy-policy",
      component: DungeonScholarPrivacyPolicyPage,
    },
    {
      path: "/settings/user-agreement",
      name: "settings-user-agreement",
      component: DungeonScholarTermsPage,
    },
    {
      path: "/settings/help-center",
      name: "settings-help-center",
      component: DungeonScholarHelpCenterPage,
    },
    {
      path: ROUTES.helpCenter,
      name: "help-center",
      component: DungeonScholarHelpCenterPage,
    },
    {
      path: ROUTES.termsOfService,
      name: "terms-of-service",
      component: DungeonScholarTermsPage,
    },
    {
      path: ROUTES.profile,
      name: "profile",
      component: DungeonScholarProfilePage,
    },
    {
      path: ROUTES.features,
      name: "features",
      component: DungeonScholarFeaturesPage,
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: ROUTES.landing,
    },
  ],
});

export default router;
