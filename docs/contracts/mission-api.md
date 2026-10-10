# KawTeam project, task and supplier API contract

Updated 11 October 2026. [Current product specification](../CURRENT_PRODUCT_SPEC.md) governs UX; [integration status](../INTEGRATION_STATUS.md) governs provider claims. Runtime contracts are `apps/web/src/lib/demo.ts`, `apps/api/src/kawteam/main.py`, `schemas/domain.py`, `tasks.py` and Supabase migrations. Generated FastAPI OpenAPI is authoritative for exact payload schemas.

## Data and scope

- Project/event: identity, name, optional Drive source, facts, active document memory, embedded tasks and backend revision.
- Task: identity/title, parent project and independent conversation. Legacy case or general thread can materialise a task without deleting history.
- Thread: project/task ownership, saved user/assistant messages, request IDs and provider/citation provenance.
- Supplier request/case: quantity, budgetSen, targetSen, goal, deadline, location, selectionTarget, candidates, messages, decisions and milestones.
- Vendor/offer: identity/source evidence, unknown/confirmed costs, specs, arrival, validity and liaison readiness.
- Decision: human approval/rejection, supplier, current terms hash; secured requires confirmationMessageId/approval linkage.

Amounts are integer sen. Unknown delivery is null, not zero. Dates are real ISO dates and display in Asia/Kuala_Lumpur. `quantity` counts items; `selectionTarget` counts placements. Preserve demo/live provenance and untrusted document/email boundaries.

## Backend endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Backend liveness; not proof of all provider connections |
| `POST /session` | Signed shared-demo profile cookie; `profile` is organiser/teammate/observer |
| `GET /state` | Scoped saved state, fit and derived approval queues |
| `GET /connections` | Configuration status; not a live provider test |
| `POST /events` | Name + optional driveUrl project creation |
| `POST /events/{id}/tasks` | Compatible explicit task creation; primary UI creates from chat |
| `POST /events/{id}/settings` | Legacy assistant settings; preferences UI removed; shortlist setting no longer controls pool |
| `POST /events/{id}/drive` | Authorised bounded Drive refresh/snapshot |
| `POST /events/{id}/documents`, `GET /documents/{id}` | Legacy document compatibility; no current upload UI |
| `POST /chat` | New/resumed task chat with eventId/taskId/requestId and message |
| `POST /actions` | Revision/idempotency-aware case actions |
| `GET /cases/{id}/report` | Legacy case outcome report |

Except health, requests require the server gateway; scoped state/actions additionally require the signed session. The browser calls the allowlisted Next.js proxy `/api/kawteam/...`, not Supabase tables or server credentials directly. The profile switcher is an intentionally shared demo, not account authentication.

## Chat transaction semantics

Missing taskId starts a deterministic retry-safe task. Optional project selection/event-name resolution chooses the owner. Selected taskId must belong to that project. The returned taskId selects its transcript. Preserve request identity across retries; reject conflicting reuse. The task and first user message commit together. Assistant completion and resulting case update commit atomically; requirement changes update the existing case using its current revision.

Questions keep terms; changed quantity/budget/date/location/specs/placement target supersede old quotes and decisions. Provider errors preserve the user message and do not claim successful actions. Retrieved project excerpts/citations never provide authority to override the user.

## Primary task actions

```json
{
  "type": "approve-vendor",
  "caseId": "SAVED_CASE_ID",
  "vendorId": "SAVED_VENDOR_ID",
  "expectedRevision": 1,
  "requestId": "UNIQUE_REQUEST_ID"
}
```

`approve-vendor` / `reject-vendor` require an organiser and an actionable ready queue row. Ranking uses matching received final quotes, eligibility, landed cost, arrival and name. Approved/secured reserve slots and aggregate budget; rejection advances waitlist; full target marks remaining suitable rows not selected locally.

Queue statuses: approval_needed, waitlist, approved, secured, rejected, not_selected, liaising, needs_terms. `liaising` is presented as pending unless real execution evidence exists. Secured is never inferred from approval alone; matching received commitment evidence is mandatory.

`liaise-task` and `confirm-vendor` are explicitly controlled original-tote demo actions. They cannot manufacture replies/confirmation for arbitrary live requests. Legacy actions create/research/choose/edit-draft/approve/reject/prepare/send/sync remain for compatibility; taskWorkflowVersion blocks old choose bypass. Exact-message hash/expiry/send rules describe the legacy demo, not final-approval-only target liaison.

## Persistence and security

Seven applied migrations protect `kawteam_workspaces`, `kawteam_records`, `kawteam_actions` with revoked direct public privileges and private credential-gated RPCs. Ownership, role, expected revisions, request hashes and transactional locking guard changes. Additive task-start/legacy-copy RPCs preserve previous records. Shared demo identity is deliberate; do not claim isolated private accounts.

## MCP and current routes

MCP exposes eight scoped stdio tools: health, project list, task/context, research, sender identity, non-binding enquiry, saved-thread reply sync and quote/confirmation interpretation. No final-decision tool exists. See [WorkBuddy guide](../integration/workbuddy.md).

Primary UI routes: `/`, `/projects/{id}`, `/projects/{id}?task={taskId}`, `/projects/{id}/tasks/{taskId}`, `/overview/activity`, `/overview/approvals`, `/overview/calendar`, `/connections`. Catch-all routing retains older project/case links; old URLs do not reinstate removed top project tabs. `/demo` and legacy case/report views remain secondary.

Gemini/Tavily are live-tested; Gmail consent and controlled send are verified, and saved-thread reading works. WorkBuddy scoped tools are transport-tested. Real commercial reply/confirmation acceptance, actual desktop orchestration/website trigger, Drive reads and deployment remain pending.


## Live email routes

All routes require the gateway and signed demo profile. `GET /email/status` verifies the configured Gmail sender. `POST /cases/{caseId}/email/contact` accepts vendorId/email/expectedRevision and is organiser-only; this registers a human-verified contact, not a final supplier choice. `POST /cases/{caseId}/email/send` accepts vendorId/subject/body/expectedRevision/requestId and is editable-profile-only, non-binding. `POST /cases/{caseId}/email/sync` accepts expectedRevision and is editable-profile-only. `POST /cases/{caseId}/email/quote` accepts vendorId/providerMessageId/expectedRevision and interprets only the latest saved supplier reply. Unknown fields are rejected.

Recipients must be real task suppliers with organiser-registered contacts. No arbitrary inbox, payment, booking or final-approval MCP capability. Intents are saved before send; identical request retries return a saved receipt, changed content fails, and ambiguous/reserved sends block retry. Provider IDs and received raw evidence are retained. Quote interpretation requires verbatim evidence, supported prices and explicit dates. Confirmation requires a current organiser decision, exact matching terms and provider receipt after that approval. Raw replies alone never imply final readiness or Secured.
