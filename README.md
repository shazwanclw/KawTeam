# KawTeam

**If you have trouble searching, KawTeam with us!**

KawTeam starts with a conversation. Pick a project for context, or send a request without one and KawTeam creates a project while saving your first message. Projects have their own chat, recent activity, approval checkpoints and optional subprojects. A project name and optional Google Drive link replace the upload flow. Memory, conversations and assistant preferences persist in Supabase. There is no login or procurement intake form.

## Run locally

Open this folder in VS Code. Use **two terminals**, starting from the project folder.

Terminal 1:

```powershell
cd apps/api
.venv/Scripts/python.exe -m uvicorn kawteam.main:app --app-dir src --reload --port 8000
```

Terminal 2:

```powershell
cd apps/web
npm run dev
```

Open **http://localhost:3000**. Local ignored environment files already connect this workspace to KawTeam Supabase. On a fresh checkout, run `npm ci` in `apps/web`; create a Python venv and install `requirements.txt` in `apps/api`. Configure both `.env.example` templates first.

The hamburger opens Chat, Overview, Projects and Connections. Create a project with the **plus beside Projects**; use the search icon to filter the list. The empty project picker also offers Add a project. Try “Find shirt printing vendors for 50 shirts within RM2,000 by 25 October 2026 in Subang Jaya.” Missing facts are requested in the conversation. Enter sends; Shift+Enter adds a line.

Each project starts with Chat and has Recent Activity, Approval and Subprojects tabs. **New subproject** creates a separate conversation sharing the parent project's memory. **Assistant settings** beside the composer offers Automatic, Research first or Existing vendor, a preferred supplier, a shortlist cap of three and custom instructions. Repeat orders skip discovery and require fresh terms; previous prices, approvals and supplier decisions are not copied.

**Overview** shows the latest 15 saved actions, approval checkpoints and a calendar of saved dates across projects. Activity and approval rows open details; global approval details lead to project review. **Connections** contains suppliers with recorded messages or a prior human selection, with history and a fresh-request shortcut. Research candidates and unsent drafts alone do not count as relationships.

Switch Organiser, Teammate and Observer using the profile button. Server-side permissions protect mutations, approvals and selection, but this deliberately shared public demo is not private personal authentication. **Only the organiser chooses a final vendor.** Choosing never buys, pays or signs anything.

## Google Drive project memory

Create with an optional Google Drive folder/document URL, then use **Project memory / Drive context** to inspect its source, status and current documents, or refresh it. There are no upload buttons in the new interface; existing documents remain usable.

**A link alone does not grant Drive access. No Drive credential is configured yet.** Links save with “Drive access needed”; the UI does not claim their contents have been read. Add one of these to `apps/api/.env`, then restart FastAPI:

```dotenv
# Publicly shared documents; enable the Drive API for this key's project:
GOOGLE_DRIVE_API_KEY=your_key

# OR a complete service-account credential JSON value:
GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON='{"type":"service_account", ... complete credential JSON ...}'
```

For private content, share the intended folder with the credential's `client_email` as a reader. The app reads that shared content; it does not gain access to your entire personal Drive. Credentials stay on the server. This version uses server credentials, without a Google sign-in flow. See Google's [Drive authorization documentation](https://developers.google.com/workspace/drive/api/guides/about-auth).

Docs and Slides import as text; Sheets import as XLSX with all worksheets, using Google's [export formats](https://developers.google.com/workspace/drive/api/guides/ref-export-formats). PDF, DOCX, XLSX, TXT, Markdown and CSV are supported, with 3 MB/file, 80,000 extracted characters/file and 20 current imported documents/project limits. Folder traversal is bounded. Scanned PDFs require a text version; there is no OCR.

Refresh replaces each file's current version and recomputes project facts. A complete refresh archives removed files. Partial/failed reads preserve existing readable memory and report problems. If a new source is inaccessible, preserved memory is explicitly attributed to its previous source. Refresh is manual; continuous background sync is not connected yet.

## Current implementation

- Supabase projects, optional subprojects, assistant settings, Drive snapshots, extracted memory, scoped conversations, requests, drafts and human decisions. Atomic saves/chat completion, conflict detection and retry protection. Five additive migrations are in `supabase/migrations`, applied to the connected KawTeam project.
- Project-scoped context retrieval/citations. Stable Drive file identities replace stale versions and exclude archived documents from memory. Existing document records remain compatible.
- Optional Gemini conversation and Tavily source discovery adapters. **Neither key is configured yet.** Public-source candidates remain unquoted; unknown terms and contacts are never invented.
- Controlled tote scenario: **Prepare enquiry → Approve draft → Send in demo → Check demo reply**. Exact-message hash/revision, 30-minute approval expiry, single-use send and three-round cap. Replies are fictional and saved; no external email is sent.
- Outcome report with constraints, evidence references, pending/no-deal outcomes and explicitly simulated potential savings for the sample scope.

**WorkBuddy remains deferred at your request. External email is not connected.** The health-only scaffold is preserved; live agent execution and real supplier email require their integrations. Until AI/search keys are supplied, requests and workflow plans save with honest setup notes. Working status appears only during an actual request; no background execution is claimed. No public deployment has been created.

## Optional provider keys

Add to `apps/api/.env`, never frontend code or Git, then restart FastAPI:

```dotenv
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-3.5-flash-lite
TAVILY_API_KEY=your_key
```

Restart FastAPI after changing environment values. These keys do not connect external email or WorkBuddy. Provider configuration is exposed as status only, without credentials. No paid provider billing has been enabled.

## Verify

In `apps/api`: `.venv/Scripts/python.exe -m pytest -q` and `.venv/Scripts/python.exe -m ruff check src tests`.

In `apps/web`: `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`. Stop the dev server before building the same directory. With both servers running and Playwright Chromium installed, run `npm run test:e2e`.

`npm run test:e2e` runs `tests/chat-home-browser.mjs`. Browser tests create labelled QA projects in the connected workspace; remove only those test records after inspection. Screenshots are ignored under `apps/web/test-results/`. The obsolete overview/upload browser test was removed.

For the controlled outreach check, run from `apps/api`:

```powershell
$env:PYTHONPATH='src'
.venv/Scripts/python.exe tests/live_outreach_browser.py
```

It verifies the project approval dialog, exact approval, one simulated send, saved reply, Connections history and fresh-request continuation, then restores the original sample case. `tests/live_database.py` is a separate opt-in concurrency check.

## Free deployment preparation

The deployment target remains two Vercel projects from this repository: Next.js root **apps/web**, FastAPI root **apps/api**. The API exports `app` from `index.py`, an officially supported [FastAPI entrypoint](https://vercel.com/docs/frameworks/backend/fastapi). Use your free plan and check its [function limits](https://vercel.com/docs/functions/limitations) before deployment; no paid hosting has been enabled.

Deploy the API with its local server environment values, preserving the database credential matching the applied migrations, and set `COOKIE_SECURE=true`. Deploy the web with `NEXT_PUBLIC_DATA_MODE=api`, `KAWTEAM_API_URL=https://your-api.vercel.app`, and the matching server-only `KAWTEAM_GATEWAY_SECRET`. Never expose secrets with a `NEXT_PUBLIC_` prefix. Verify the deployed session, project/chat, Drive and controlled outreach flow before submitting.

Database tables deny direct public access. Scoped RPCs require a separate secret-held backend credential. [Checkpoint security notes](docs/PHASE_3_7_CHECKPOINT.md) explain the expected Supabase advisor warnings.

Submission: public GitHub repository, deployed app URL, presentation PDF, group name and campus branch. Aim **11 October 08:45 MYT**, ahead of the supplied 09:00 buffer cutoff.

See the [current chat/Drive checkpoint](docs/CHAT_HOME_DRIVE_CHECKPOINT.md), [implementation plan](docs/plans/2026-10-10-chat-home-drive.md), [earlier makeover](docs/PROJECT_MAKEOVER_CHECKPOINT.md), [backend checkpoint](docs/PHASE_3_7_CHECKPOINT.md) and [checklist](KAWTEAM_BUILD_CHECKLIST.md). Original blueprint retained.
