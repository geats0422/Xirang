# AGENTS.md

This repository currently contains a single app under `frontend/`.
Agentic coding tools should treat `frontend/` as the active project root for almost all build, lint, test, and implementation work.

## Scope
- Main app: `frontend/`
- Framework: Vue 3 + TypeScript + Vite
- Router: Vue Router 4
- Tests: Vitest + `@vue/test-utils` + jsdom
- Linting: ESLint flat config
- Global styles/tokens: `frontend/src/styles/tokens.css`

## Rule Files
- No repository-level `.cursorrules` file was found.
- No `.cursor/rules/` directory was found.
- No `.github/copilot-instructions.md` file was found.
- There is an internal OpenCode config at `.opencode/AGENTS.md`, but there was no root `AGENTS.md` prior to this file.

## Working Directory Guidance
- For app commands, use `D:\project\Xirang\frontend` as the working directory.
- Avoid treating the repository root as a Node project unless new root-level tooling is explicitly added.
- When editing app code, prefer paths relative to `frontend/` in your reasoning and summaries.

## Install / Dev Commands
Run these from `frontend/`.

```bash
npm install
npm run dev
npm run lint
npm run lint:fix
npm run typecheck
npm run test
npm run build
```

## Single-Test Commands
Use Vitest via the existing npm script.

Run one test file:
```bash
npm run test -- src/pages/DungeonScholarHomePage.spec.ts
```

Run multiple specific files:
```bash
npm run test -- src/utils/auth.spec.ts src/components/GameSettlementModal.spec.ts
```

Run tests matching a name pattern:
```bash
npm run test -- -t "clicking coin button navigates to shop"
```

Run one file and one test name:
```bash
npm run test -- src/pages/DungeonScholarSettingsPage.spec.ts -t "renders extracted settings sections"
```

Raw Vitest command:
```bash
vitest run --passWithNoTests
```

## Required Verification Before Finishing
For meaningful code changes, run:
```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

Minimum expectations:
- Small UI-only change: `lint` + `typecheck`
- Behavior change: `lint` + `typecheck` + targeted test(s)
- Structural/refactor or shared code change: run all four

## Project Structure
- `frontend/src/pages/`: route-level Vue pages
- `frontend/src/components/`: reusable UI and feature components
- `frontend/src/components/settings/`: Settings page subcomponents
- `frontend/src/components/leaderboard/`: Leaderboard page subcomponents
- `frontend/src/components/layout/`: shared layout components such as sidebar
- `frontend/src/composables/`: shared Composition API logic
- `frontend/src/constants/`: shared constants such as route definitions
- `frontend/src/router/`: router setup and route registration
- `frontend/src/utils/`: utility modules and auth helpers
- `frontend/public/`: static assets served directly by Vite

## Code Style Guidelines

### Imports
- Use ES module imports only.
- Group imports as: framework/library, shared app imports, then local imports.
- Use relative imports consistently; the codebase currently does not use TS path aliases.
- Import `type` symbols with `import { foo, type Bar }` where appropriate.

### Formatting
- Use double quotes in TypeScript and Vue `<script setup>` blocks.
- Use semicolons consistently.
- Prefer trailing commas in multiline arrays, objects, and function calls when nearby code uses them.
- Keep expanded objects and route definitions vertically formatted when they have multiple fields.
- In templates, keep attributes compact unless multiline formatting clearly improves readability.

### Vue / SFC Conventions
- Use `<script setup lang="ts">` for Vue components.
- Keep page files focused on composition and data wiring.
- Move large visual sections into dedicated feature components once a page grows.
- Shared navigation/layout belongs in `components/layout/` or composables, not duplicated across pages.
- Prefer props + emits over implicit shared mutable state.
- Keep static presentational subtrees in child components when they reduce page complexity.

### Types
- TypeScript is `strict`; do not weaken compiler options.
- Add explicit types for complex arrays, domain rows, props, and emit contracts.
- Use `type` aliases for shaped UI data such as `StandingRow` and `PreferenceRow`.
- Avoid `any`; if unavoidable, prefer `unknown` and narrow it.
- Preserve browser guards like `typeof window === "undefined"` when touching browser-only code.

### Naming
- Components: PascalCase filenames and symbols, e.g. `AppSidebar.vue`.
- Pages: PascalCase page files prefixed by feature name, e.g. `DungeonScholarHomePage.vue`.
- Composables: `useXxx.ts`.
- Local variables/functions: `camelCase`.
- CSS classes: `kebab-case` with `block__element--modifier` style patterns when useful.
- Shared route definitions belong in `frontend/src/constants/routes.ts`, not inline string literals.

### Routing
- Reuse `frontend/src/constants/routes.ts` instead of scattering route strings.
- Reuse `frontend/src/composables/useRouteNavigation.ts` for page navigation behavior.
- Keep route-level pages lazily loaded in `frontend/src/router/index.ts`.
- When adding a page, register the lazy import and prefer matching the existing route naming pattern.

### Styling
- Reuse tokens from `frontend/src/styles/tokens.css` where practical.
- Prefer existing colors, spacing, radii, and shadows before introducing new values.
- Avoid unnecessary new hard-coded colors if an equivalent token or nearby pattern exists.
- Use scoped styles for component-local styling.
- If a page accumulates too much style weight, extract the corresponding UI block into a child component.

### Error Handling
- Prefer guarded logic and early returns over deeply nested branches.
- Preserve existing `try/finally` navigation cleanup patterns.
- For auth or browser storage logic, fail closed rather than assuming success.
- Avoid swallowing errors unless there is a deliberate UI fallback or safe no-op.
- When adding async UI actions, consider how loading or failure would be surfaced.

### Testing Expectations
- Add or update Vitest coverage for behavior changes.
- Prefer focused component tests with `@vue/test-utils` over broad brittle snapshots.
- Test important user behavior: navigation, emitted events, auth helpers, and conditional rendering.
- Use `createMemoryHistory()` + `createRouter()` for route-aware component tests.
- Keep tests near the affected code using `*.spec.ts` naming.

## ESLint Rules That Matter
Based on `frontend/eslint.config.mjs`:
- `@typescript-eslint/no-unused-vars` is an error.
- Unused args/vars are only tolerated when prefixed with `_`.
- `vue/multi-word-component-names` is disabled.
- Several strict template formatting rules are intentionally disabled; do not reformat solely to satisfy nonexistent Prettier-style rules.

## Agent Guidance
- Prefer improving shared abstractions over copying page logic.
- Before adding a new helper, search for an existing component, composable, or constant that already solves most of the problem.
- Keep changes narrowly scoped and consistent with the current Vue 3 Composition API style.
- Do not add new dependencies unless they materially simplify the codebase and are justified by repeated need.
- If you add a new command or workflow, update this file.
