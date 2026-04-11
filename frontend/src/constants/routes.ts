export const ROUTES = {
  landing: "/",
  login: "/login",
  signUp: "/sign-up",
  home: "/home",
  library: "/library",
  levelPath: "/library/level-path",
  modeGuide: "/library/mode-guide",
  gameModes: "/library/game-modes",
  endlessAbyss: "/library/game-modes/endless-abyss",
  speedSurvival: "/library/game-modes/speed-survival",
  knowledgeDraft: "/library/game-modes/knowledge-draft",
  review: "/library/game-modes/review",
  quests: "/quests",
  shop: "/shop",
  leaderboard: "/leaderboard",
  settings: "/settings",
profile: "/profile",
  privacyPolicy: "/privacy-policy",
} as const;

export type AppRoutePath = (typeof ROUTES)[keyof typeof ROUTES];

export type PrimaryNavItem = {
  label: string;
  icon: string;
  route: AppRoutePath;
};

export const PRIMARY_NAV_ITEMS: PrimaryNavItem[] = [
  { label: "Home", icon: "⌂", route: ROUTES.home },
  { label: "Library", icon: "◫", route: ROUTES.library },
  { label: "Quests", icon: "✦", route: ROUTES.quests },
  { label: "Leaderboard", icon: "▤", route: ROUTES.leaderboard },
];
