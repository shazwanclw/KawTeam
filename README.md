# KawTeam

**What are we going to KawTeam today?**

Chat-first sourcing and stakeholder liaison for student projects and small businesses. Each new conversation creates a task; continuing a selected task preserves its history. The organiser makes the final supplier choice, and supplier confirmation is separate from approval. No login or procurement intake form.

Updated 11 October 2026. Start with the [current product specification](docs/CURRENT_PRODUCT_SPEC.md), [integration status](docs/INTEGRATION_STATUS.md), [blueprint](AI_Complete_Hackathon_Blueprint.md) and [build checklist](KAWTEAM_BUILD_CHECKLIST.md). Older dated documents have been reconciled with the current scope.

Original long-form ideas are preserved as clearly superseded [blueprint](docs/archive/pre-refresh-blueprint.md), [implementation-plan](docs/archive/pre-refresh-implementation-plan.md) and [design](docs/archive/pre-refresh-design.md) archives. Use current documents for implementation; archives retain future-product detail, not current requirements.

## Run locally

Open this repository in VS Code. Use two terminals, starting from the repository root.

Backend:

```powershell
cd apps/api
.venv/Scripts/python.exe -m uvicorn kawteam.main:app --app-dir src --reload --port 8000
```

Frontend:

```powershell
cd apps/web
npm run dev
```

Open **http://localhost:3000**. For a fresh checkout, use `npm ci` in `apps/web`; create a Python venv and install `requirements.txt` in `apps/api`; configure both `.env.example` files. Existing credentials are ignored and are not supplied by cloning GitHub. Restart the backend after changing its environment. Stop the frontend server before building the same `.next` directory.

## Current experience

- Main Chat selects a project. Without one, a named existing project is resolved or a project is created from the request. A new conversation creates a task, not an unscoped permanent chat.
- Projects open directly to chat. Choose New Task or an existing task to expand and resume its saved transcript. Requirement edits update that task; questions preserve its terms.
- All Task, Recent Activity and Failsafe sit below the project composer. Task rows show approval counts. No top project tabs, optional Subprojects or assistant-preference button.
- Task details show Secured and ranked Approval on the left, Upcoming events on the right. Approved is not secured. One supplier or multiple placements have separate targets from item quantity.
- Sidebar: Chat; Overview with Recent Activity / Approval / Calendar; searchable Projects with plus; Connections. The hamburger stays open across navigation until manually closed.
- New project asks for a name and optional Google Drive link. The chat composer offers a Drive link and readable file references (up to three files / 3 MB total); attachments stay with their task. Drive content requires authorised access; a link alone is not permission.
- Overview uses milestone rows, Approval Needed / Approved, concise review dialogs and Open in project. Calendar red dots and date lists follow the selected month. Connections retains genuine recorded relationships and labelled demo history.
- Profile menu switches shared-demo Organiser / Teammate / Observer roles. Only organisers make final decisions. This intentionally does not provide private user authentication.

Try: "Find vendors for 50 shirts within RM2,000 by 25 October 2026 in Subang Jaya for event Sunway Got Talent." In its task, continue with "We only want 40 shirts now." Enter sends; Shift+Enter inserts a line.

## What works and what does not

| Capability | Status |
|---|---|
| Supabase projects, tasks, conversations and decisions | Implemented; seven migrations applied |
| Gemini conversation | Key configured; live website reply verified |
| Tavily discovery | Key configured; live public-source search verified |
| Ranked post-liaison approval and confirmation rules | Implemented and tested; controlled sample exercises the lifecycle |
| Drive extraction, snapshot and project retrieval | Implemented; real access awaits credentials |
| WorkBuddy MCP | Nine scoped tools; real stdio discovery and saved project/task reads verified; desktop orchestration/website trigger pending |
| Supplier emails | Gmail OAuth/send/saved-thread read implemented; one controlled test receipt saved; quote/confirmation guards tested; real supplier acceptance pending |
| Public deployment | Planned; not verified |

Research retains the returned candidate pool rather than selecting only three for outreach. Current search still has a bounded five-source result limit. Returned websites are provisional: no invented prices, verified contacts, sent emails or supplier commitments. Ranking uses valid final quotation evidence, landed cost and arrival, not arbitrary AI scores.

To see the controlled lifecycle: open Tech Night -> Totes for the tech crowd -> Run sample liaison -> review a ready supplier -> Approved -> Check demo confirmation. The sample has three fictional suppliers, but only quotes meeting its budget/specs/date are actionable. Confirmation is independently simulated and labelled. No real supplier is contacted. Legacy exact-draft controls and `/demo` remain secondary compatibility surfaces, not the latest primary workflow.

## Environment and connections

The web uses `NEXT_PUBLIC_DATA_MODE=api`, `KAWTEAM_API_URL` and server-only `KAWTEAM_GATEWAY_SECRET`. Locally the API URL is `http://127.0.0.1:8000`. API credentials and Gemini/Tavily keys belong in `apps/api/.env`; never add credentials to `NEXT_PUBLIC_` variables.

AI/search keys are already configured locally. Drive supports `GOOGLE_DRIVE_API_KEY` for public content or `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` for a shared private folder. Share a private folder with the service-account `client_email` as reader. Docs/Slides export as text; Sheets as XLSX. PDF, DOCX, XLSX, TXT, MD and CSV have bounded extraction. Scanned PDFs have no OCR. Refresh is manual and preserves previous readable memory on failure; active snapshots replace old versions and archive removed files after complete sync.

Gmail is locally authorised via `Downloads/Email API.json`, with an ignored local token and one controlled test receipt saved. Use `GMAIL_SENDER`, `GMAIL_OAUTH_CLIENT_PATH`, optional `GMAIL_TOKEN_PATH`; deployment can use server-secret `GMAIL_AUTHORIZED_USER_JSON`. See [integration status](docs/INTEGRATION_STATUS.md) for commands, limits and remaining acceptance, and [WorkBuddy guide](docs/integration/workbuddy.md) for the nine scoped tools. No actual supplier was contacted.

## Verification

Backend, from `apps/api`:

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src tests
```

Frontend, from `apps/web`:

```powershell
npm test
npm run typecheck
npm run lint
npm run build
```

Latest test counts: 131 backend and 44 frontend tests. Type checks and lint pass. Production build and browser flows were verified before this docs-only refresh. With both servers running, `npm run test:e2e` checks task layout; `node tests/refinement-browser.mjs` checks chat/sidebar/overview/calendar. The isolated outreach browser check uses intercepted provider calls; older chat-home scripts target superseded screens.

Opt-in saved-data checks, from `apps/api`:

```powershell
$env:PYTHONPATH='src'
$env:KAWTEAM_TEST_URL='http://127.0.0.1:3000'
.venv/Scripts/python.exe tests/live_task_browser.py
.venv/Scripts/python.exe tests/live_task_database.py
```

These create labelled QA projects. The browser wrapper restores the original tote sample in `finally`; its output identifies the QA project for scoped cleanup. Remove only the explicitly identified QA records/actions. Screenshots are ignored under `apps/web/test-results/`. No test authorises real vendor email.

## Deployment and submission

Target two Vercel projects: Next.js root `apps/web` and FastAPI root `apps/api` (`index.py` exports the app), using the existing Supabase backend. Configure API server credentials, `COOKIE_SECURE=true`, matching gateway secrets and the deployed HTTPS API URL. Recheck free-plan eligibility and limits; no paid host or billing upgrade is authorised. A desktop WorkBuddy process does not run inside the deployed frontend. The website-to-agent trigger remains unresolved.

Submission needs a public GitHub repository, deployed app link, pitch PDF, group name and campus branch. Original deadline: 11 October 2026, 09:30 MYT; the 30-minute buffer makes 09:00 the operational cutoff. Verify actual links and submission receipt; repository/public deployment/submission completion is not claimed here.


## Automatic website outreach (11 October 2026)

Chat supplier requests now persist an authorised task-scoped outreach queue. The visible website runs one bounded step approximately every 15 seconds: verify a public supplier business contact, send a non-binding enquiry, sync saved Gmail threads, interpret a current reply, or request missing/revised terms. Only a literal address from the supplier's own site is used, with grounded service evidence; ambiguous contacts and provider failures remain visible on the task. All discovered candidates stay in the pool; unrelated sources are not emailed.

Email receipts, request hashes, deterministic send IDs, compare-and-swap writes and a 180-second step lease prevent duplicate/concurrent sends. A pause instruction disables further steps; asking to view contact details does not authorise sends. Enquiries stop for unselected suppliers when the approved target is filled. Human supplier selection remains in KawTeam. A later matching confirmation can mark an approved supplier secured; the runner does not send orders or binding acceptance.

Existing tasks are not silently enrolled: continue that task and say `Email the suppliers` or `Start outreach`. New or edited sourcing requests queue outreach automatically, unless the user asks for research only. Keep KawTeam open to advance website ticks; a permanently running hosted worker is not implemented. WorkBuddy can call `kawteam_outreach_step` for the same authorised task, but this does not give the website an inbound WorkBuddy API. Reconnect desktop MCP to discover the ninth tool.

Verification: controlled mailbox tests, live read-only supplier contact extraction, and an isolated browser tick check pass. No real supplier enquiry was sent during development. Real commercial supplier acceptance, public deployment, unattended scheduling and Drive access remain pending.
