# Chat home and Drive context plan: current reconciliation

Updated 11 October 2026. Completed frontend/memory foundation; real folder access still pending. [Current specification](../CURRENT_PRODUCT_SPEC.md), [Drive checkpoint](../CHAT_HOME_DRIVE_CHECKPOINT.md), [task checkpoint](../TASK_CONVERSATIONS_CHECKPOINT.md) and [integration status](../INTEGRATION_STATUS.md) define actual behavior.

**Goal:** Chat-first requests with optional authorised Drive project memory, distinct task conversations and final human supplier decisions.

**Architecture:** Shared Next.js composer, FastAPI request/context services, protected Supabase project/task/thread/case/snapshot transactions. Gemini conversations and Tavily sources now work; Drive credential and email/agent execution remain open.

## Delivered

- Home project picker; sidebar Projects plus/search; name and optional Drive link; no upload UI.
- Current headline What are we going to KawTeam today? No model switch/preferences/quick-chip/footer clutter.
- New task per new conversation; saved-task continuation/edits, shared parent memory and isolated history.
- All Task / Recent Activity below project composer; task Secured/Approval/dates replace old top project/subproject tabs.
- Sidebar-only Overview links, milestone summaries, final supplier approval/history, red-dot month calendar and Connections.
- Bounded Drive extraction/snapshot, document version replacement, removed-file archive, partial-failure preservation and project citations.

## Pending access and acceptance

Configure Drive API key/public content or service-account JSON/shared private folder. Verify actual source read, changed/reverted facts, removed files, scope and denial using authorised documents. No continuous sync, OCR or Google user OAuth exists. A link alone does not prove memory import.

Task chat and snapshot protections are covered by current 100 backend/43 frontend suites; prior production build/browser/database checks passed. No old upload/subproject screen should be restored to satisfy a superseded browser script. Follow the remaining [phase plan](2026-10-10-kawteam-implementation-plan.md) for live providers and deployment.
