# KawTeam — Build and Submission Checklist

> **Current authorised scope (10 October, chat home/Drive update):** Phases 3–5 and 7 with persisted project memory and conversations; **defer WorkBuddy Phase 6 until explicitly requested**. No login or procurement intake form. The home page starts with chat and an optional project selector. Create by project name and an optional Google Drive link; no upload UI. Projects have Chat, Recent Activity, Approval and Subprojects. Overview uses activity/approval tables and Calendar. Connections means previously contacted or chosen suppliers. Final vendor selection always requires the organiser. Provider/Drive credentials and external email are not configured. See the [current checkpoint](docs/CHAT_HOME_DRIVE_CHECKPOINT.md) for actual implementation and remaining integrations. Older detailed sections below are planning reference and are superseded where they conflict with this update.


**Build status:** chat-first frontend and persisted Phases 3–5/7 are implemented locally. Live provider keys, external email, WorkBuddy and public deployment remain open.  
**Master plan:** [Phase-by-phase implementation plan](docs/plans/2026-10-10-kawteam-implementation-plan.md).  
**Design:** [Product and UI specification](docs/plans/2026-10-10-kawteam-design.md).  
**Target submission:** 11 October 2026, 08:45 MYT. Treat 09:00 as the operational cutoff due to the supplied 30-minute buffer.

## Phase 0 — Connection feasibility

- [ ] WorkBuddy installed/signed in; account version and access recorded.
- [ ] Actual custom tool call verified with matching server request/result.
- [x] Local stdio transport verified with MCP SDK; actual client auth remains open.
- [x] Desktop stdio route documented; no hosted agent API assumed.

## Phase 1 — Foundation

- [x] Git, Next.js, Python package and lockfiles established.
- [x] Mission/offer/message/approval/event contracts agreed.
- [x] Sen/null/date/provenance rules fixed.
- [x] Realistic fixture states created.
- [x] Design tokens and core primitives reviewed.
- [x] Secret-free environment template and setup commands written.

## Phase 2 — Frontend

- [x] Workspace and goal entry.
- [x] Mission summary and workflow progress.
- [x] Supplier comparison and evidence drawer.
- [x] Offer/thread timeline.
- [x] Exact-message approval/edit/rejection experience.
- [x] Outcome and print layout.
- [x] Labelled local demo at `/demo` (not publicly deployed).
- [x] Loading, empty, waiting, error, no-deal states.
- [x] Keyboard/modal and mobile navigation reviewed; main flow browser-tested.
- [ ] Additional tablet/zoom and print QA before deployment.
- [ ] Fixture preview deployed and labelled.

## Phase 3 — Persistence/auth

- [x] Database schema/migrations; RLS/direct access denied; credential-gated RPCs.
- [x] Signed demo-profile sessions and role-checked API gateway (shared workspace; no real user authentication).
- [x] Transactional state/event updates and revisions.
- [x] Unsigned/wrong-credential/observer mutations rejected; shared demo roles deliberately selectable.
- [x] Mission reload works; polling uses ordered events.
- [ ] Backend deployed and reachable from web.

## Phase 4 — Discovery/evaluation

- [x] Live search adapter and capped requests.
- [ ] Source/contact provenance and deduplication.
- [x] Quote normalisation with unknown costs preserved.
- [x] Hard budget/specification/deadline eligibility.
- [ ] Explainable ranking with evidence coverage.
- [ ] Cheapest qualifying option and backups.
- [x] Calculation and ranking behavior tests pass.

## Phase 5 — Negotiation/approvals

- [x] Controlled fictional supplier provider labelled.
- [x] Exact immutable payload approval enforced server-side.
- [ ] Edited/expired/cross-owner approvals blocked.
- [ ] Send deduplication and uncertain delivery behavior.
- [ ] Reply processing, rounds, stop rules and backup switching.
- [x] No purchase/payment/signature tools.
- [x] Critical behavior tests pass.

## Phase 6 — WorkBuddy execution (explicitly deferred)

- [ ] Shared-service MCP tool set registered.
- [ ] KawTeam workflow skill loaded in WorkBuddy.
- [ ] Real goal extraction and saved task plan.
- [ ] Actual discover/compare/approve/send/reply/replan/report flow.
- [ ] Checkpoint/resume behavior verified in actual client.
- [ ] Concurrent-run controls and action caps enforced.
- [ ] Matching tool IDs captured in UI/server/client evidence.

## Phase 7 — Outcome

- [ ] All mandatory terms checked before verified recommendation.
- [ ] Report retains sources, history and outstanding conditions.
- [x] Comparable savings only; simulated/potential labels accurate.
- [x] No-deal and pending-reply outcomes handled.
- [ ] Print version reviewed for clipping.
- [ ] Evidence/savings tests pass.

## Phase 8 — Deployment and QA

- [ ] Production web/API/MCP/database configuration.
- [ ] Secrets excluded from repo/client/logs.
- [ ] Public demo opens in incognito without registration.
- [ ] Actual deployed WorkBuddy call succeeds.
- [ ] Deployed owner isolation/approval/budget/rejection/report checks.
- [ ] Lint, typecheck, tests and production build verified.
- [ ] Cold-start behavior accounted for; backup recording ready.

## Phase 9 — Pitch/submission

- [ ] Feature freeze by 07:00 MYT if schedule permits.
- [ ] Pitch PDF rendered and visually checked.
- [ ] Public GitHub link verified while signed out.
- [ ] Deployed app link verified in incognito.
- [ ] README states actual implementation and limitations.
- [ ] Group name and campus branch supplied.
- [ ] Controlled suppliers and simulated metrics disclosed.
- [ ] All required materials submitted by target 08:45 MYT.
- [ ] Submission receipt retained.

## After core completion

- [ ] Phase 10: authorised live Gmail, durable follow-ups, verified resume capability.
- [ ] Phase 11: sponsorship mission and cash/in-kind pipeline.
- [ ] Phase 12: calendar/meeting commitments/team roles.
- [ ] Phase 13: multi-source discovery, CRM, analytics and platform maturity.

## Phase evidence log

Fill this during implementation; leave pending until verified.

| Phase | State | Commit/files | Verification evidence | Limitations |
|---|---|---|---|---|
| 0 | Pending | — | — | Account access unverified |
| 1 | Pending | — | — | No app scaffold |
| 2 | Pending | — | — | — |
| 3 | Pending | — | — | — |
| 4 | Pending | — | — | — |
| 5 | Pending | — | — | — |
| 6 | Pending | — | — | — |
| 7 | Pending | — | — | — |
| 8 | Pending | — | — | — |
| 9 | Pending | — | — | Team metadata required |


## Free-tier hosting constraint (user update)

For the hackathon, target zero out-of-pocket cost: Next.js frontend and FastAPI backend on Vercel Hobby as separate projects from the same repository; Supabase Free for shared persistence. This replaces the earlier Render backend hosting recommendation. FastAPI remains the intended application backend; only MCP health/contracts exist today.

Design API/MCP operations as short, stateless requests. Persist workflow checkpoints in the database; do not depend on an always-running server, in-memory workflow state, local disk storage, a background email-polling loop or frequent Hobby cron jobs. WorkBuddy orchestrates multi-step work and calls bounded tools; transport/client compatibility must be verified before deployment.

Use supplied WorkBuddy credits for AI where supported. Hosting being free does not make AI, search or email APIs free. Do not introduce paid-only services or require a paid upgrade without a new user instruction. Keep provider usage capped and distinguish unavailable live integrations from labelled demo fixtures. A single Vercel deployment for the entire repository is not assumed; the web and Python app have separate root directories and can be connected with a frontend API proxy.

References verified: https://vercel.com/docs/frameworks/backend/fastapi ; https://vercel.com/docs/plans/hobby ; https://vercel.com/docs/functions/limitations ; https://vercel.com/docs/cron-jobs/manage-cron-jobs ; https://supabase.com/pricing
