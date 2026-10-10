# Task conversations checkpoint

Updated 11 October 2026. This is the delivered task redesign, reconciled with the subsequent provider setup. [Current specification](CURRENT_PRODUCT_SPEC.md) and [integration status](INTEGRATION_STATUS.md) are authoritative.

## Delivered flow

Main Chat retains its project picker and creates a task for each new conversation. Named existing projects are resolved; otherwise a named project is created. First task/message writes are atomic and retry-safe. Projects open directly to New Task chat; choosing a saved task expands its transcript. Questions and edits stay scoped, and changed requirements update the case in place with old terms superseded.

Only All Task / Recent Activity appear below chat. Row boxes show approval counts and link to task detail. Secured/Approval occupy the left column; Upcoming events the right, stacking on mobile. Continue conversation selects the task. Legacy case requests and earlier project-wide threads remain resumable without deleting original records.

## Supplier decision lifecycle

Retain all returned source candidates; no three-candidate outreach cap. Current discovery is bounded to five sources, not exhaustive. Valid complete final quote replies are ranked by landed cost, arrival and name. Item quantity and supplier/placement target are independent. Human approvals reserve remaining slots and aggregate budget; rejects advance waitlist; full target locally closes other suitable candidates.

Approved is not secured. Received confirmation must reference the same supplier, approval and current term hash. Requirement changes invalidate fresh-quote readiness and decisions, preserving history. Organiser-only server checks, revisions and retries remain enforced.

Run sample liaison and Check demo confirmation are restricted labelled actions for the original tote scenario. They simulate multi-supplier liaison and separate confirmation; no live supplier email was sent. Legacy exact-message approval controls remain compatibility, not the new primary checkpoint policy.

## Persistence and verification

Seven applied migrations include task conversations and legacy-copy changes. Shared-demo role selection is deliberate, not private multi-user authentication. Tests cover naming/retries, continuation/edits, isolation, legacy threads, valid final quotes, one/ten targets, total budget, stale terms, confirmation proof and role restrictions.

100 backend tests and 43 frontend tests pass, plus Ruff, TypeScript and ESLint. Production build, responsive saved browser flow and database concurrency checks passed before this documentation refresh. Original sample restored; QA projects removed. README documents read-only and opt-in checks.

## Latest integration update

Gmail is locally authorised; one controlled test send has a saved provider receipt, and saved-thread reading works. Eight scoped WorkBuddy MCP tools exist and real local project/task reads pass. Actual desktop orchestration, website trigger, automated contact enrichment, live supplier quote/confirmation acceptance, Drive access and public deployment remain pending. See [integration status](INTEGRATION_STATUS.md).
