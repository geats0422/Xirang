# Frontend P0 Alignment Plan

> **For agentic workers:** Use `/execute <task>` after this plan is approved. Preserve the current `frontend/` visual language, layout structure, typography, spacing rhythm, and component patterns. Do not perform broad redesigns.

**Goal:** Align the existing Vue frontend with the PRD's P0 front-end-visible requirements so users can clearly complete the intended flow: upload -> mode select -> start run -> finish run -> settlement -> shop/top-up.

**Architecture:** Keep the current page-first structure under `frontend/src/pages/`, add only minimal shared UI/state abstractions, and enhance existing sections in place. Reuse current cards, pills, dialogs, status bars, and typography rather than introducing a new shell.

**Tech Stack:** Vue 3, TypeScript, Vue Router, Vitest, existing shared components and tokens.

**References:**
- `docs/PRD-Global-MVP-v1.md`
- `docs/7-Day-Launch-Plan-v1.md`

---

## Task List

### Task 1: Freeze Frontend-Visible Product Rules

**Goal:** Prevent churn before touching UI.

**Files:**
- Modify: `frontend/src/pages/DungeonScholarModeSelectionPage.vue`
- Modify: `frontend/src/pages/DungeonScholarShopPage.vue`
- Reference: `docs/PRD-Global-MVP-v1.md`
- Reference: `docs/7-Day-Launch-Plan-v1.md`

- [ ] **Step 1: Write failing tests (RED)**
  - Add or update tests proving mode selection starts with no active card.
  - Add or update tests proving shop copy and visible purchase surfaces match the agreed P0 wording.

- [ ] **Step 2: Run targeted tests and confirm failure**
  - Run: `npm run test -- src/pages/DungeonScholarModeSelectionPage.spec.ts src/pages/DungeonScholarShopPage.spec.ts`

- [ ] **Step 3: Implement minimal rule-alignment changes (GREEN)**
  - Remove default recommendation behavior from mode selection.
  - Align shop item copy and visible item set with the PRD.
  - Define minimal shared frontend UI state names for upload, run, settlement, wallet, and purchase flows.

- [ ] **Step 4: Refactor cautiously (REFACTOR)**
  - Extract shared state names or constants only if duplication appears.
  - Keep current page structure, card hierarchy, and visual rhythm intact.

- [ ] **Step 5: Verify**
  - Run: `npm run lint`
  - Run: `npm run typecheck`
  - Run targeted tests again.

- [ ] **Step 6: Commit**
  - Commit message: `feat: align frontend product rules with P0 PRD`

**Acceptance Criteria:**
- Mode selection has no default active recommendation.
- Shop visible item/copy no longer conflicts with the PRD.
- Shared frontend state vocabulary is stable for later tasks.

**Risks / Dependencies:**
- Depends on PRD wording being treated as frozen for this cycle.

### Task 2: Add Upload-Entry UI States to Home and Library

**Goal:** Make upload surfaces expressive without changing the existing visual language.

**Files:**
- Modify: `frontend/src/pages/DungeonScholarHomePage.vue`
- Modify: `frontend/src/pages/DungeonScholarLibraryPage.vue`
- Create (optional): `frontend/src/components/upload/UploadDisclaimerInline.vue`
- Create (optional): `frontend/src/components/upload/UploadEntryStateCard.vue`

- [ ] **Step 1: Write failing tests (RED)**
  - Add Home tests for idle/loading/success/failure rendering.
  - Add Library tests for upload-entry state transitions and empty-state CTA.

- [ ] **Step 2: Run targeted tests and confirm failure**
  - Run: `npm run test -- src/pages/DungeonScholarHomePage.spec.ts src/pages/DungeonScholarLibraryPage.spec.ts`

- [ ] **Step 3: Implement minimal UI states (GREEN)**
  - Add BETA/free disclaimer visibility.
  - Add upload idle/loading/success/failure/fallback states.
  - Add empty-library CTA without changing the existing card-grid language.
  - Keep all new elements inside `hero-upload`, toolbar upload entry, or `scroll-card--add`.

- [ ] **Step 4: Refactor cautiously (REFACTOR)**
  - Extract shared upload status subcomponents only if both pages need identical markup.
  - Preserve current spacing, card shapes, colors, and typography.

- [ ] **Step 5: Verify**
  - Run targeted tests again.
  - Run: `npm run lint`
  - Run: `npm run typecheck`

- [ ] **Step 6: Commit**
  - Commit message: `feat: add upload entry states to home and library`

**Acceptance Criteria:**
- Users can understand upload preconditions and next steps from both pages.
- Failure and fallback states are visible and non-disruptive.
- Visual appearance remains consistent with the current Home and Library pages.

**Risks / Dependencies:**
- No backend dependency required for initial UI-state work.

### Task 3: Correct Mode Selection Interaction Strategy

**Goal:** Match the PRD requirement of three equal choices with no default recommendation.

**Files:**
- Modify: `frontend/src/pages/DungeonScholarModeSelectionPage.vue`
- Create/Modify test: `frontend/src/pages/DungeonScholarModeSelectionPage.spec.ts`

- [ ] **Step 1: Write failing tests (RED)**
  - Test that no card is active on first render.
  - Test that the primary action is unavailable until a mode is chosen.
  - Test that selecting a mode enables progression.

- [ ] **Step 2: Run targeted tests and confirm failure**
  - Run: `npm run test -- src/pages/DungeonScholarModeSelectionPage.spec.ts`

- [ ] **Step 3: Implement interaction corrections (GREEN)**
  - Start with no selected mode.
  - Keep the current dialog layout, mode cards, and art direction.
  - Add lightweight visible decision support matching the PRD's `刺激 / 深度 / 轻松` framing.

- [ ] **Step 4: Refactor cautiously (REFACTOR)**
  - Consolidate mode metadata if labels and card data diverge.
  - Keep modal pacing, card count, and hierarchy unchanged.

- [ ] **Step 5: Verify**
  - Run targeted tests again.
  - Run: `npm run lint`
  - Run: `npm run typecheck`

- [ ] **Step 6: Commit**
  - Commit message: `feat: align mode selection interaction with PRD`

**Acceptance Criteria:**
- The page is clearly `three options, user chooses one`.
- The current modal aesthetic and pacing remain intact.

**Risks / Dependencies:**
- Requires checking both `begin` and `review` copy paths.

### Task 4: Upgrade the Three Gameplay Pages into Real Product Shells

**Goal:** Make the gameplay pages structurally P0-ready even before real question data is wired.

**Files:**
- Modify: `frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue`
- Modify: `frontend/src/pages/DungeonScholarEndlessAbyssPage.vue`
- Modify: `frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue`
- Create (optional): `frontend/src/components/game/QuestionFeedbackAction.vue`
- Create (optional): `frontend/src/components/game/RunStatusNotice.vue`

- [ ] **Step 1: Write failing tests (RED)**
  - Add one behavior/UI assertion per gameplay page for feedback entry visibility.
  - Add one assertion per gameplay page for run-status notice visibility.

- [ ] **Step 2: Run targeted tests and confirm failure**
  - Run: `npm run test -- src/pages/DungeonScholarSpeedSurvivalPage.spec.ts src/pages/DungeonScholarEndlessAbyssPage.spec.ts src/pages/DungeonScholarKnowledgeDraftPage.spec.ts`

- [ ] **Step 3: Implement gameplay shell improvements (GREEN)**
  - Add visible placeholders/regions for real question content.
  - Add `这题有误` feedback UI.
  - Add visible notices for `<2s no score` and reduced-reward cases.
  - Improve `KnowledgeDraft` interaction framing so it better matches card/drag semantics without redesigning the whole page.

- [ ] **Step 4: Refactor cautiously (REFACTOR)**
  - Extract shared feedback/status UI if duplication is clear.
  - Keep page identity, status bars, question cards, and footer action rhythm consistent.

- [ ] **Step 5: Verify**
  - Run targeted tests again.
  - Run: `npm run lint`
  - Run: `npm run typecheck`

- [ ] **Step 6: Commit**
  - Commit message: `feat: make gameplay pages P0-ready shells`

**Acceptance Criteria:**
- All three pages visibly support PRD-required gameplay feedback and risk messaging.
- No page loses its current visual identity.

**Risks / Dependencies:**
- Future real question/session data should slot into these regions without structural rework.

### Task 5: Unify Settlement and Visible Wallet/Result Surfaces

**Goal:** Remove disconnected static XP/coins/streak displays across pages.

**Files:**
- Modify: `frontend/src/components/GameSettlementModal.vue`
- Modify: `frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue`
- Modify: `frontend/src/pages/DungeonScholarEndlessAbyssPage.vue`
- Modify: `frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue`
- Modify: `frontend/src/pages/DungeonScholarHomePage.vue`
- Modify: `frontend/src/pages/DungeonScholarShopPage.vue`
- Modify: `frontend/src/pages/DungeonScholarProfilePage.vue`
- Create (optional): `frontend/src/composables/useFrontendProgressState.ts`

- [ ] **Step 1: Write failing tests (RED)**
  - Update settlement modal tests for new visible fields/states.
  - Add at least one synchronization test for shared visible wallet/progress state.

- [ ] **Step 2: Run targeted tests and confirm failure**
  - Run: `npm run test -- src/components/GameSettlementModal.spec.ts`
  - Run any new targeted page/state tests.

- [ ] **Step 3: Implement unified visible state (GREEN)**
  - Map settlement fields to unified result concepts: XP, coins, streak/freeze state, scoring validity, wrong-question follow-up entry.
  - Use a single frontend source for visible wallet/progress values.
  - Preserve the current settlement modal visual hierarchy.

- [ ] **Step 4: Refactor cautiously (REFACTOR)**
  - Extract repeated wallet/progress formatting if needed.
  - Keep settlement modal art direction unchanged.

- [ ] **Step 5: Verify**
  - Run targeted tests again.
  - Run: `npm run lint`
  - Run: `npm run typecheck`

- [ ] **Step 6: Commit**
  - Commit message: `feat: unify settlement and visible wallet state`

**Acceptance Criteria:**
- Settlement no longer feels like hardcoded decoration.
- Home, Shop, and Profile reflect a consistent visible state model.

**Risks / Dependencies:**
- Frontend-only shared state is acceptable until backend ledger exists.

### Task 6: Add Top-Up Entry and Insufficient-Balance UI Flow to Shop

**Goal:** Satisfy the PRD's required top-up path and insufficient-balance fallback.

**Files:**
- Modify: `frontend/src/pages/DungeonScholarShopPage.vue`
- Create (optional): `frontend/src/components/shop/TopUpEntryCard.vue`
- Create (optional): `frontend/src/components/shop/InsufficientBalanceModal.vue`

- [ ] **Step 1: Write failing tests (RED)**
  - Test that top-up entry is always visible.
  - Test that insufficient balance opens the top-up modal/flow.
  - Test that successful purchase path and fallback path render distinct feedback.

- [ ] **Step 2: Run targeted tests and confirm failure**
  - Run: `npm run test -- src/pages/DungeonScholarShopPage.spec.ts`

- [ ] **Step 3: Implement minimal shop flow (GREEN)**
  - Add a constant top-up entry.
  - Add an insufficient-balance branch and a minimal `$1.99` rescue pack surface.
  - Keep the current shop hero, cards, and wallet group.

- [ ] **Step 4: Refactor cautiously (REFACTOR)**
  - Extract shared purchase feedback UI if needed.
  - Avoid introducing a generic payment UI pattern.

- [ ] **Step 5: Verify**
  - Run targeted tests again.
  - Run: `npm run lint`
  - Run: `npm run typecheck`

- [ ] **Step 6: Commit**
  - Commit message: `feat: add P0 shop top-up and insufficient balance flow`

**Acceptance Criteria:**
- The shop visibly supports the PRD-required fallback path.
- The page still looks like the existing Xi Rang shop, not a generic payment screen.

**Risks / Dependencies:**
- Payment integration can remain mocked; the UI flow must still be complete.

### Task 7: Add Analytics Hook Points for Funnel and Error Feedback

**Goal:** Prepare the frontend for Day 6 funnel and error observation without rewriting page structure later.

**Files:**
- Create: `frontend/src/composables/useAnalyticsEvents.ts`
- Modify: `frontend/src/pages/DungeonScholarHomePage.vue`
- Modify: `frontend/src/pages/DungeonScholarLibraryPage.vue`
- Modify: `frontend/src/pages/DungeonScholarModeSelectionPage.vue`
- Modify: `frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue`
- Modify: `frontend/src/pages/DungeonScholarEndlessAbyssPage.vue`
- Modify: `frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue`
- Modify: `frontend/src/pages/DungeonScholarShopPage.vue`

- [ ] **Step 1: Write failing tests (RED)**
  - Add unit tests for analytics event helper/composable.
  - Add targeted tests proving critical pages trigger event hooks at the right UI transitions.

- [ ] **Step 2: Run targeted tests and confirm failure**
  - Run: `npm run test -- src/composables/useAnalyticsEvents.spec.ts`
  - Run any new page-level event tests.

- [ ] **Step 3: Implement minimal event hook points (GREEN)**
  - Define stable event names for `upload_started`, `upload_succeeded`, `upload_failed`, `mode_selected`, `run_started`, `run_completed`, `insufficient_balance_triggered`, and `wrong_question_reported`.
  - Keep instrumentation out of templates as much as possible.

- [ ] **Step 4: Refactor cautiously (REFACTOR)**
  - Keep naming and payload shapes centralized.
  - Do not let analytics logic distort page readability.

- [ ] **Step 5: Verify**
  - Run targeted tests again.
  - Run: `npm run lint`
  - Run: `npm run typecheck`

- [ ] **Step 6: Commit**
  - Commit message: `feat: add P0 frontend analytics hook points`

**Acceptance Criteria:**
- Frontend has stable event hook points for funnel and feedback analysis.
- UI structure and readability are preserved.

**Risks / Dependencies:**
- Real analytics SDK can be attached later without rewriting page structure.

---

## Dependencies

- Task 1 -> Task 2 -> Task 3 -> Task 4 -> Task 5 -> Task 6 -> Task 7
- Task 5 depends on Task 4 clarifying gameplay-visible result fields.
- Task 6 depends on Task 5 for shared wallet display semantics.
- Task 7 can start lightly after Task 2, but should be finalized after the main UI states stabilize.

---

## Global Verification

- [ ] `npm run lint`
- [ ] `npm run typecheck`
- [ ] `npm run test`
- [ ] Manually verify visual consistency on:
  - `frontend/src/pages/DungeonScholarHomePage.vue`
  - `frontend/src/pages/DungeonScholarLibraryPage.vue`
  - `frontend/src/pages/DungeonScholarModeSelectionPage.vue`
  - `frontend/src/pages/DungeonScholarShopPage.vue`
  - `frontend/src/pages/DungeonScholarSpeedSurvivalPage.vue`
  - `frontend/src/pages/DungeonScholarEndlessAbyssPage.vue`
  - `frontend/src/pages/DungeonScholarKnowledgeDraftPage.vue`
  - `frontend/src/components/GameSettlementModal.vue`

---

## Guardrails

- Do not add a fourth mode.
- Do not redesign Landing / Settings / Leaderboard / Profile.
- Do not introduce a new visual system.
- Reuse current cards, pills, dialogs, toolbars, and status patterns.
- Prefer inserting new states into existing sections over creating new page blocks.
- Prioritize PRD alignment over polish.
