# KawTeam

**What are we going to KawTeam today?**

KawTeam helps student organisers and small businesses find suppliers, manage liaison and review offers in one project workspace. Start with a request in chat, let the tools research and track replies, then make the final supplier decision yourself. Approval and supplier confirmation are separate steps.

## Product walkthrough

1. Describe a goal, such as **"Find 50 T-shirts within RM2,000 for Sunway Got Talent."** Select a project, or let KawTeam resolve/create one with a concise name.
2. A new conversation becomes a task. Add a Google Drive reference or readable attachment for context; choose an existing task to continue its conversation.
3. New sourcing retains all returned candidates for verification and non-binding liaison. Repeat orders can reuse a known supplier and skip discovery.
4. Review ranked final offers in the task. Approve or reject; a matching supplier confirmation is required before **Secured**.
5. Follow completed milestones, approval counts, important dates and saved supplier email history.

The shared hackathon version has no login. Its sidebar profile menu switches Organiser, Teammate and Observer roles; only the organiser can make final supplier decisions. This is a shared demonstration workspace, not private multi-account authentication.

## Run locally

Requirements: Node.js/npm, Python 3.12+ and the configured provider/database credentials. From a fresh checkout, create the backend environment:

```powershell
cd apps/api
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

In a separate terminal, install the frontend:

```powershell
cd apps/web
npm ci
Copy-Item .env.example .env.local
```

Fill in the environment values using the [integration setup guide](docs/INTEGRATION_STATUS.md). Existing local credentials are not included in GitHub. Do not overwrite already-configured environment files.

Start the backend in one terminal:

```powershell
cd apps/api
.venv/Scripts/python.exe -m uvicorn kawteam.main:app --app-dir src --reload --port 8000
```

Start the frontend in another:

```powershell
cd apps/web
npm run dev
```

Open **http://localhost:3000**. API mode requires both servers. Restart the backend after changing its environment. Development uses Webpack; stop the frontend before building into the same `.next` directory.

## Implementation status

| Capability | Current state |
|---|---|
| Projects, tasks, conversations and decisions | Supabase-backed; transaction, revision and retry guards |
| Website AI and research | Gemini conversation; Tavily public-source discovery |
| Supplier email | Gmail send/read services, persisted receipts and bounded foreground outreach |
| Final approval and supplier confirmation | Separate states; ranked offers, waitlist and budget checks |
| WorkBuddy | Nine KawTeam MCP tools; website-to-WorkBuddy trigger is not connected |
| Project memory | Readable attachments and persisted context; Drive adapter awaits authorised credentials |
| Calendar | Website calendar works; Google Calendar API sync is planned, not implemented |
| Hosting | Vercel deployment roots prepared; public app deployment not verified |

Provider keys alone do not prove an end-to-end outcome. WorkBuddy consumes KawTeam tools from its desktop app; website chat currently uses Gemini and the backend services directly. Outreach advances while the website is open, not through an always-on hosted worker. See [integration status](docs/INTEGRATION_STATUS.md) for evidence and remaining work.

## Demo

Three prepared projects show single-supplier T-shirt sourcing, ten exhibitor placements and repeat catering. They include complete **simulated** conversations, offers and confirmations from fictional suppliers. No real vendor is contacted by opening these fixtures. Project headers omit a Sample badge; email history and execution provenance still identify demo records. Follow the [demo guide](docs/DEMO_SCENARIOS.md).

## Documentation

- [Product specification](docs/CURRENT_PRODUCT_SPEC.md): current screens, task flow and decision rules.
- [Architecture](docs/ARCHITECTURE.md): services, data flow and hackathon requirements.
- [Integration setup and status](docs/INTEGRATION_STATUS.md): credentials, verification, deployment and remaining work.
- [Demo scenarios](docs/DEMO_SCENARIOS.md): presentation walkthrough and safe dataset regeneration.
- [WorkBuddy setup](docs/integration/workbuddy.md): MCP configuration and actual execution checks.
- [API contract](docs/contracts/mission-api.md): endpoints, ownership, revisions and action semantics.

The [proposed pitch workflow](docs/assets/kawteam-proposed-workflow.png) includes intended WorkBuddy orchestration and Google Calendar sync; it is not a claim that those pending integrations already run.

## Verification

From `apps/api`:

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check src tests
```

From `apps/web`:

```powershell
npm test
npm run typecheck
npm run lint
npm run build
```

Recent recorded checks passed: 154 backend tests, 47 frontend tests, TypeScript, ESLint, Ruff and targeted desktop/mobile browser flows. These are historical checks, not a claim that every command reruns on each documentation change. With the frontend running, mocked browser suites include `compact-chat-browser.mjs`, `chat-references-browser.mjs`, `supplier-history-browser.mjs`, `profile-menu-browser.mjs`, `approval-reference-browser.mjs`, `calendar-summary-browser.mjs` and `presentation-demo-browser.mjs`, under `apps/web/tests`. They do not authorise live supplier email. Screenshots and private credentials are Git-ignored.

## Hackathon submission

Dormathon 2026, Track 2: WorkBuddy agentic solutions. Required deliverables are a public repository, deployed application link, pitch PDF, group name and campus branch. The supplied deadline is **11 October 2026, 09:30 MYT**, with a 30-minute buffer; operational cutoff **09:00 MYT**. WorkBuddy must demonstrate meaningful tool execution for the track, rather than simply appearing in the pitch. Submission and deployment completion are not claimed here.