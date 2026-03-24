# Review Rules Repository

This directory contains auto-generated rule candidates from the feedback learning system.

## Purpose

The self-learning agent analyzes user feedback about questions and generates improvement suggestions. These suggestions are stored as **rule candidates** that must be reviewed by a human before any action is taken.

## Phase 1 Behavior

- Rules are generated and stored for review only
- **Rules are NOT automatically applied** to live question generation or prompts
- A human must review and approve/reject each rule candidate

## Rule Candidate Structure

Each rule candidate contains:

- `rule_type`: Category of the rule (e.g., "quality_improvement", "content_update")
- `title`: Short summary of the suggested improvement
- `content`: Detailed description of the rule
- `status`: Current status (`pending_review`, `approved`, `rejected`)
- `source_job_id`: Reference to the feedback learning job that generated this rule

## Workflow

1. User submits feedback about a question
2. Feedback learning job runs (asynchronously)
3. AI summarizes feedback and generates suggestions
4. Suggestions are stored as rule candidates with `pending_review` status
5. Human reviews and updates status to `approved` or `rejected`
6. (Phase 2) Approved rules may be applied to improve question generation

## API Endpoints

- `POST /api/v1/feedback` - Submit feedback about a question
- `GET /api/v1/feedback/{id}` - Get specific feedback
- `GET /api/v1/feedback` - List user's feedback
- `POST /api/v1/feedback/summarize` - Trigger feedback summarization
- `GET /api/v1/review/rules` - List rule candidates

## Storage

Rule candidates are stored in the `review_rule_candidates` table in the database.
