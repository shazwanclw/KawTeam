# Chat and overview refinement plan: delivered current scope

Updated 11 October 2026. [Current specification](../CURRENT_PRODUCT_SPEC.md) is authoritative; [refinement checkpoint](../CHAT_OVERVIEW_REFINEMENT_CHECKPOINT.md) records retained changes. Later [task conversations](2026-10-11-task-conversations.md) replace old project tabs and draft-centric approvals.

**Goal:** Minimal chat, persistent sidebar, milestone activity, concise final supplier reviews and clear month-based dates.

## Delivered decisions

Remove Hackathon edition, quick vendor chips, small footer/provider text and assistant preferences. Use What are we going to KawTeam today? Preserve project/context selection. Keep opened sidebar across routes; Overview's three links only appear there. Show approval count and distinct upcoming-date count.

Activity includes up to 15 useful saved milestones, not thoughts/parsing/planning/setup/draft edits. Approval filters only Approval Needed / Approved, with concise scope/terms/replies and Open in project. Current task flow approves human supplier decisions, not every enquiry. Calendar has red dots, month/day-based Upcoming/Past lists, today upcoming and reset day selection on month change.

## Implementation and verification

Activity/schedule helpers, overview views, chat, sidebar and browser checks delivered. Current suites: 43 frontend/71 backend; lint/type checks pass. Prior build and read-only task/refinement browser acceptance passed. Agent statuses require evidence, not fake background work.

Gemini/Tavily now work; real Drive/Gmail and WorkBuddy tools/trigger remain pending. Read [integration status](../INTEGRATION_STATUS.md), not old missing-key notes. No public deployment is verified.
