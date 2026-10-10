# KawTeam build and submission checklist

Updated 11 October 2026. Current scope: [product specification](docs/CURRENT_PRODUCT_SPEC.md); account/provider evidence: [integration status](docs/INTEGRATION_STATUS.md); build order: [phase plan](docs/plans/2026-10-10-kawteam-implementation-plan.md).

Checked means implemented or verified as stated. A provider key alone does not complete its workflow. WorkBuddy setup is now underway; execution remains unimplemented.

## Phase 0: connections and architecture

- [x] Next.js + FastAPI + Supabase architecture; separate Vercel roots prepared.
- [x] Real local MCP stdio health discovery/invocation test.
- [x] WorkBuddy desktop KawTeam configuration present; user reports connection okay.
- [ ] Capture actual WorkBuddy health call/request ID as independent client evidence.
- [ ] Resolve supported website-to-agent start/resume mechanism and operating cost.
- [ ] Prove supplied WorkBuddy credits support the selected execution route.

## Phases 1-2: foundation and current frontend

- [x] Types, integer sen, unknown costs, ISO dates and demo/live provenance.
- [x] Teal/lime design, chat-first home, no login/upload/intake form.
- [x] Sidebar Chat / Overview links / Projects plus/search / Connections.
- [x] Navigation remains open across routes until closed.
- [x] Main project picker; project New Task/existing task selector and expanded history.
- [x] Below-chat All Task / Recent Activity and task approval badges.
- [x] Task Secured/Approval left and Upcoming events right; responsive stacking.
- [x] Overview milestones, concise review, Approval Needed / Approved, red-dot calendar.
- [x] Legacy conversations and cases surfaced as tasks.
- [ ] Final deployed tablet/zoom/print and incognito QA.

## Phase 3: persistence and shared-demo access

- [x] Seven migrations applied; Supabase is API-mode source of truth.
- [x] Private credential-gated RPCs and deny-all direct public table access.
- [x] Signed selectable demo profiles, backend role checks and allowlisted web gateway.
- [x] Atomic task starts, case/chat updates, revisions and retry protection.
- [x] Concurrent starts/retries, old thread copying and observer rejection verified.
- [ ] Production configuration and deployed isolation checks.

## Phase 4: conversation, memory and discovery

- [x] Gemini key configured; live adapter and saved website reply verified.
- [x] Tavily key configured; live public-source discovery verified.
- [x] Bounded source collection, provenance and unknown quotations preserved.
- [x] Retain returned candidate pool; old three-vendor outreach cap removed.
- [x] Stored project memory/retrieval/citations and Drive snapshot implementation.
- [ ] Configure authorised Drive folder and credential; verify actual read/refresh.
- [ ] Verify supplier identity, contact channel and suitability before outreach.
- [ ] Improve hostname-only deduplication and source coverage as needed.

## Phase 5: liaison, human approval and confirmation

- [x] Controlled sample liaison/replies explicitly labelled; no external email.
- [x] One/multiple placement targets separate from item quantity.
- [x] Final-quote evidence, terms hashes and deterministic valid-offer ranking.
- [x] Active slots/waitlist, rejection promotion and aggregate-budget enforcement.
- [x] Organiser-only final decisions; approval never implies secured.
- [x] Separate matching supplier confirmation required; stale edits invalidate terms.
- [x] Obtain `Downloads/Email API.json`; verify Desktop OAuth client format without exposing secrets.
- [x] Authorise sender consent/token and verify Gmail sender identity (no password).
- [x] Implement Gmail send/saved-thread read, recipient validation and correlation.
- [x] Persist send intents, prevent duplicate retry, block uncertain sends, deduplicate replies; enforce per-supplier/task limits.
- [x] Implement grounded quote extraction and post-approval matching confirmation guards; real commercial acceptance still pending.
- [x] Controlled email send/reply passed with one message and one reply; no real supplier outreach. Current new sender consent/identity separately verified.

## Phase 6: WorkBuddy execution

- [x] Desktop setup instructions reflect Connectors -> MCP Server Management -> Add MCP.
- [x] One health tool exists and is transport-tested.
- [x] Implement scoped project/task/context, discovery, non-binding liaison and saved-thread tools.
- [ ] Load updated workflow guidance in the actual client.
- [ ] Demonstrate goal planning, tool execution, reply validation and saved outcomes.
- [x] Keep human final approval outside all agent tools.
- [ ] Verify bounded/concurrent runs, resume and website trigger.
- [ ] Capture useful matching UI/server/client call evidence beyond health.

## Phase 7: outcomes

- [x] Saved milestones, relationship history and task dates.
- [x] Legacy outcome/report pending/no-deal and simulated-savings labels.
- [ ] Complete task-wide live final report, outstanding terms and evidence.
- [ ] Verify final print/export layout; measure only comparable actual outcomes.

## Phase 8: deployment

- [ ] Connect Vercel to the GitHub repository and confirm free-plan eligibility.
- [ ] Deploy web `apps/web` and API `apps/api`; configure HTTPS gateway/cookies.
- [ ] Keep secrets/tokens out of repo, frontend and logs.
- [ ] Use durable task checkpoints; no assumed always-on Vercel polling/desktop process.
- [ ] Verify deployed chat/Drive/email/WorkBuddy and roles/budget/retries.
- [ ] Incognito app access and public repository verified; backup recording ready.

## Phase 9: pitch and submission

- [ ] Group name and campus branch provided.
- [ ] Pitch clearly explains real user value and meaningful WorkBuddy execution.
- [ ] Live versus simulated/missing capabilities disclosed.
- [ ] Pitch PDF rendered/reviewed; public GitHub/app links checked.
- [ ] Submit and retain receipt. Supplied deadline: 11 October 2026 09:30 MYT; buffer cutoff 09:00; target 08:45.

## Verified evidence

131 backend tests, 44 frontend tests, Ruff, TypeScript and ESLint pass. Production build and browser task/overview flows passed before the docs refresh, including responsive widths, saved continuation/edit, rejection, approval and separate confirmation. Live Gemini/Tavily succeeded; Supabase transactional checks and MCP health transport succeeded. QA data was cleaned and original samples restored.

## Future product, not hackathon blockers

Dedicated sponsorship/partnership/scholarship workflows, external calendars and meeting commitments, authorised social messaging, private organisation accounts, advanced credibility/review scoring, multilingual channels, richer CRM/analytics and exports. No paid upgrade is authorised.
