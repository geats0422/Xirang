---
description: Generate and run E2E tests with Playwright
agent: e2e-runner
subtask: true
model: openai/gpt-5.3-codex
---

# E2E Command

Generate and run end-to-end tests using Playwright: $ARGUMENTS

## Your Task

1. **Analyze user flow** to test
2. **Create test journey** with Playwright
3. **Run tests** and capture artifacts
4. **Report results** with screenshots/videos

## Test Structure

```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature: [Name]', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: Navigate, authenticate, prepare state
  })

  test('should [expected behavior]', async ({ page }) => {
    // Arrange: Set up test data
    // Act: Perform action
    // Assert: Verify outcome
  })
})
```

## Artifact Collection

Capture for each test:
- Screenshot on failure
- Video on failure (if configured)
- Console logs
- Network requests (if relevant)

## Running Tests

```bash
# Run all tests
npx playwright test

# Run specific test file
npx playwright test tests/e2e/feature.spec.ts

# Run with UI
npx playwright test --ui
```

## Reporting

Report includes:
- Test results (pass/fail)
- Artifacts location
- Error details with screenshots
- Retry recommendations for flaky tests
