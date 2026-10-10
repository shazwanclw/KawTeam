# KawTeam implementation plan: current phases and remaining work

Reconciled 11 October 2026. The original frontend-first foundation has been delivered; do not restart from an empty project. [Current specification](../CURRENT_PRODUCT_SPEC.md), [design](2026-10-10-kawteam-design.md), [integration status](../INTEGRATION_STATUS.md) and [checklist](../../KAWTEAM_BUILD_CHECKLIST.md) define the accepted scope.

**Goal:** Complete a chat-driven project/task sourcing workflow, with useful WorkBuddy execution, real non-binding liaison, human final choice and independently confirmed supplier outcomes.

**Architecture:** Next.js web gateway, FastAPI rule/services layer, Supabase durable state, Gemini conversation and Tavily discovery. WorkBuddy calls KawTeam tools through MCP; its website trigger is unresolved. Gmail/Drive require authorised access. Keep costs bounded and avoid an always-on process inside Vercel functions.

**Tech stack:** Next.js 16.4, React, TypeScript, Tailwind/shadcn, FastAPI/Pydantic, MCP Python SDK, Supabase protected RPCs. Two Vercel projects are the hosting target.

## Phase inventory

| Phase | Current state |
|---|---|
| 0: feasibility | Local MCP health works; WorkBuddy entry configured; actual execution and trigger open |
| 1: foundation | Repository, dependencies, contracts, tokens and environment templates delivered |
| 2: frontend | Latest chat/task/overview/Connections layout implemented and browser-checked |
| 3: persistence | Seven migrations, roles, revisions, transactions and retries implemented |
| 4: conversation/discovery | Gemini/Tavily configured and live-tested; Drive credential/contact enrichment open |
| 5: liaison/approval | Gmail OAuth/send/reply acceptance passes; grounded quote/confirmation guards implemented; real commercial run pending |
| 6: WorkBuddy | Eight scoped tools with real local transport/project/task reads; actual desktop runner/website trigger pending |
| 7: outcome | Task status/dates and legacy reporting present; complete live task report pending |
| 8: deployment | Configuration roots prepared; public deployment unverified |
| 9: submission | Public links, PDF, group/campus and receipt still need verification |

## Fixed product requirements

No login, intake form or upload UI. Optional Drive link at creation. Main Chat chooses projects; Project Chat chooses New Task/existing tasks. A new conversation creates a task; follow-ups/questions/edits continue it. Only All Task / Recent Activity below project chat. Task detail Secured/Approval left, dates right. Sidebar Overview sublinks only. Organiser is final approver. Remove three-supplier cap; contact verified suitable returned pool; rank completed final quotes, maintain waitlist and separate confirmation.

## Step A: Gmail authorisation implemented; deployment acceptance remains

**Current user preparation:** The user reports Gmail API setup complete and supplied `Downloads/Email API.json`. Its Desktop OAuth client format, required credential fields and Google endpoints are verified; it stays outside Git. Personal Gmail can work; dedicated inbox preferred. Google consent, selected identity and a controlled send/reply check passed for the original sender. Current sender `shazwanclw@gmail.com` is separately authorised and identity-verified; no new-account send has been made.

**Implementation locations:** `apps/api/src/kawteam/config.py`, a new Gmail provider module and local authorisation command, `apps/api/.env.example`, provider tests and integration docs. Protect token/client files with ignored paths before writing credentials. No Gmail password, invented callback route or frontend-public token.

1. Add a local consent command with explicit required send/read scopes and safe credential storage.
2. Verify selected account using a read-only identity check, without dumping inbox data.
3. Add bounded recipient validation and MIME/thread handling.
4. Test authorised send/read using controlled inboxes only.

**Acceptance:** Actual consent, sender identity and controlled message/reply evidence. Test OAuth expiration/refresh and deployed credentials separately. This step does not mean public OAuth production approval.

## Next step B: durable communication and evidence

**Locations:** new provider/service modules; `main.py`, `repository.py`, `projects.py`, `tasks.py`, `workflow.py`; additive migration if needed; backend tests.

1. Verify source identity/contact and deduplicate businesses, not only hosts.
2. Store enquiry intent before sending; ensure retry does not blindly duplicate an uncertain send.
3. Correlate incoming provider messages to task/supplier/thread; deduplicate provider IDs.
4. Parse quotations with raw evidence, unknown shipping/spec/date and validity preserved.
5. Implement bounded non-binding negotiation, waits, stop rules and durable checkpoints.
6. Create final matching quote records; let existing queue enforce budgets/targets.
7. Record separate confirmation after human approval. Do not expose final approve/reject as agent tools.

**Acceptance:** No claimed contact before send evidence; no final quote before usable final reply; no secured state before matching confirmation; no over-budget/over-target decisions; edits invalidate stale terms; failures remain honest. Test one and ten placements and rejection/waitlist cases. Non-binding enquiry policy follows current user request, not legacy draft checkpoints.

## Next step C: WorkBuddy scoped tools and trigger

**Locations:** `apps/api/src/kawteam/mcp/server.py`, shared services, tests, `workbuddy/kawteam/skills/kawteam-procurement/SKILL.md`, `docs/integration/workbuddy.md`.

1. Capture actual desktop health request/result and tool identity.
2. Add scoped project/task/context/read/checkpoint tools.
3. Add bounded discovery/contact/liaison/reply tools only where live providers exist.
4. Enforce workspace, task ownership, role/action restrictions, retries and usage limits in services.
5. Demonstrate WorkBuddy planning/execution/resume on one saved task.
6. Resolve a supported API/SDK or verified bridge for website-initiated work. If unavailable, label desktop initiation and do not claim a fully automatic public app.

**Acceptance:** Useful real WorkBuddy tool calls saved in the same task UI, with resumable checkpoints and final human approval excluded from agent capabilities. Credits do not prove hosted API eligibility. Do not use undocumented personal-account proxies.

## Next step D: actual Drive context

**Locations:** existing `drive.py`, `memory.py`, snapshot RPC, project-memory UI and tests.

Provide a public credential/file or service account/shared private folder. Verify supported file reads, changed budget refresh, old-file replacement, removed files, partial failure and access denial. Stay inside existing file/read limits; no need to restore uploads. Later user OAuth/background sync is a separate feature.

**Acceptance:** A real authorised document excerpt affects the selected project's answer with a valid citation. Failed reads preserve attributed old memory, not invented current content.

## Next step E: live task outcome and deployment

Complete evidence-backed task outcome/report with unknowns, approval/confirmation state and no-deal conditions. Verify print/export rather than claiming legacy reports automatically cover multiple supplier placements. Then deploy `apps/web` and `apps/api` separately on the approved free-plan target with Supabase, secure cookies, HTTPS API URL and server-only secrets.

Agent/email work must use short requests and persisted checkpoints; polling/reply execution needs a verified external runner/trigger. No continuous Vercel loop or laptop process assumed in the deployment.

**Acceptance:** Incognito public access; source repo public check; deployed chat, task continuation, roles, quotations, approval, confirmation, Drive and actual WorkBuddy evidence; no credentials in browser/Git/logs. Confirm limits and costs before enabling services.

## Verification commands

From `apps/api`: `.venv/Scripts/python.exe -m pytest -q` and `.venv/Scripts/python.exe -m ruff check src tests`.

From `apps/web`: `npm test`, `npm run typecheck`, `npm run lint`, `npm run build`. Stop the web server before building the same directory. With both servers running: `npm run test:e2e`, `node tests/refinement-browser.mjs`.

Opt-in saved-data wrappers: `tests/live_task_browser.py`, `tests/live_task_database.py`; follow README, restore sample and remove only explicitly labelled QA records. Live provider tests consume limited quota; tests do not authorise vendor emails.

Current evidence: 103 backend/44 frontend tests, lint/type checks, prior build/browser/DB acceptance, live Gemini/Tavily, real scoped MCP reads and a controlled Gmail send/reply. The new sender identity is verified; no new-account email was sent. Treat an unchecked future step as pending even if the scaffolding exists.

## Submission and later phases

Prepare pitch PDF, group/campus metadata, actual public URLs and receipt. Supplied deadline 11 October 2026 09:30 MYT; buffer cutoff 09:00; target 08:45. Show user value, complete agentic actions, final human control and clearly labelled simulations. No numeric scoring weights or guaranteed judging acceptance.

Later phases: sponsorship/contribution matching; partnerships; meeting availability/invites/commitments; multilingual/social channels; credibility/history enrichment; CRM; real organisation accounts; retention/opt-outs; exports and measured analytics. They do not displace the live procurement vertical slice.
