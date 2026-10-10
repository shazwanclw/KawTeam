# Phases 3-7 checkpoint: current state

Reconciled 11 October 2026. [Current specification](CURRENT_PRODUCT_SPEC.md), [integration status](INTEGRATION_STATUS.md) and [task checkpoint](TASK_CONVERSATIONS_CHECKPOINT.md) supersede earlier form/upload/general-chat/shortlist assumptions.

## Delivered and open

| Phase | Delivered | Open |
|---|---|---|
| 3 | Supabase, seven migrations, signed shared-demo roles, protected RPCs, atomic tasks/chat/cases, revisions/retries | Public deployment and deployed checks |
| 4 | Project retrieval/citations, Drive adapter, live Gemini/Tavily, bounded candidate pool, eligibility | Actual Drive access, verified contacts and broader deduplication |
| 5 | Controlled queue lifecycle plus Gmail authorisation/send/saved-thread read and durable intents | Real final quotes/confirmations, contact enrichment and follow-up orchestration |
| 6 | Desktop MCP configuration and health transport scaffold | Actual useful WorkBuddy tools, orchestration/resume and website trigger |
| 7 | Task statuses/dates, milestone history, legacy report/pending/no-deal/simulated savings | Complete live task outcome/export and print QA |

Home picks projects; project chat picks tasks; new conversations create tasks; follow-ups/questions/edits stay scoped. Projects have no top tabs or upload UI. All Task / Recent Activity appear below chat; task page has Secured/Approval left and dates right. Organiser retains final control.

## Persistence and security

Tables deny direct public access; RPCs require a private workspace credential. Next.js forwards allowlisted requests with server gateway and signed HttpOnly role cookie. FastAPI applies role/revision/ownership checks. Shared-demo profile switching is intentional, not private tenant authentication.

Task start, initial message and legacy history copy are transactional. Case/assistant updates are atomic and revision-aware. Snapshots retain current Drive identities and preserve attributed readable memory on failures. External text is untrusted reference data. Unknown terms remain unknown; final quote/confirmation evidence hashes must match current scope.

## Evidence and boundaries

100 backend tests and 43 frontend tests pass; lint/type checks pass. Production build, saved browser/DB task checks and responsive layouts passed before this docs refresh. Live Gemini reply and Tavily sources verified; local MCP health works. QA records removed and original sample restored.

Gmail is locally authorised; one controlled test send has a saved provider receipt, and saved-thread reading works. Eight scoped WorkBuddy MCP tools exist and real local project/task reads pass. Actual desktop orchestration, website trigger, automated contact enrichment, live supplier quote/confirmation acceptance, Drive access and public deployment remain pending. See [integration status](INTEGRATION_STATUS.md).
