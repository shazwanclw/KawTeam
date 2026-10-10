# Chat and overview refinement checkpoint

Reconciled 11 October 2026. These delivered refinements remain active; [task conversations](TASK_CONVERSATIONS_CHECKPOINT.md) define the later project/task layout. Read [current specification](CURRENT_PRODUCT_SPEC.md) and [integration status](INTEGRATION_STATUS.md) for complete current behavior.

## Current interface

- Headline: What are we going to KawTeam today? No Hackathon edition badge, quick vendor chips, footnotes, provider-status footer or preferences trigger.
- Sidebar starts closed, remains open across routes until manually closed; full reload resets it. Overview section links are only in the sidebar.
- Activity shows up to 15 recorded milestones, not thoughts/parsing/planning/setup/draft edits. Contact counts need recorded sends and demo provenance.
- Sidebar Approval counts actionable decisions; Calendar counts distinct upcoming saved dates.
- Approval filters are Approval Needed and Approved. Dialogs summarise terms/final replies, not raw email headers or full conversations. Open in project leads to the owning task.
- Organiser Approved/Reject actions apply to ready supplier decisions in current task flow. Approval is separate from matching supplier confirmation and any sending/purchase.
- Calendar uses red dots and Upcoming/Past lists for the visible month/selected day. Changing month clears day filtering. Today is upcoming; elapsed dates do not mean work complete.
- Project top tabs/subprojects are removed. All Task / Recent Activity below chat and task-specific Secured/Approval/dates are the later accepted layout.

## Evidence and limits

Current suites: 43 frontend and 71 backend tests; TypeScript/ESLint/Ruff pass. Earlier refinement and later task browser acceptance passed, including responsive overflow and permissions. Production build verified before docs-only refresh. Legacy browser scripts target older screens; current read-only checks are task-layout-browser and refinement-browser.

Gemini/Tavily now have successful live checks. Drive credentials, Gmail execution, WorkBuddy useful tools/trigger and deployment remain pending. No fake background progress or supplier messaging should be inferred from configured keys.
