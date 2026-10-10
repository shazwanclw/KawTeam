# KawTeam

**What are we going to KawTeam today?**

KawTeam starts with a conversation. Pick a project for context, or send a request without one and KawTeam creates a project while saving your first message. Each new conversation creates a task inside a project; choosing an existing task resumes its conversation. A project name and optional Google Drive link replace the upload flow. Memory and conversations persist in Supabase. There is no login or procurement intake form.

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

Projects open directly to chat, with **New Task** selected by default. Send a new request to create a named task, or use **Choose task** to expand an existing task's saved conversation. Follow-up questions and edits stay in that task. Changing quantity, budget, dates or specifications updates its request in place and requires fresh supplier terms. **All Task** and **Recent Activity** are below the composer; there are no top project tabs or Subprojects controls.

Task rows display pending approval counts. Opening a task shows **Secured** and a ranked **Approval** queue on the left, with **Upcoming events** on the right. Use **Continue conversation** to return to its chat. A request for 50 shirts normally targets one supplier; a request for 10 event vendors targets ten placements. Item quantity and supplier target are stored separately. Existing supplier reuse through Connections requests fresh terms. Earlier project-wide conversations and saved requests remain accessible as tasks.

The sidebar starts closed and stays open across navigation until you close it. **Overview** sections appear only in that sidebar. Recent Activity lists up to 15 completed business milestones, excluding internal parsing, planning and setup logs. Contact totals count actual recorded outgoing messages, never unsent drafts or discovered candidates.

**Approval** has **Approval Needed** and **Approved** filters. Supplier checkpoints appear only after recorded final quotation replies match the current request and meet its requirements. All discovered candidates remain in the liaison pool; the old three-candidate cap is removed. Suitable final quotes are ordered by confirmed landed cost, delivery date and name. Single-supplier tasks expose one active approval slot; multi-supplier tasks expose the remaining number of slots. Rejecting advances the waitlist. Filling the target marks the remaining suitable candidates not selected locally, without claiming rejection emails were sent.

A row opens the request, quoted terms and saved reply summaries. Only the organiser can approve or reject there, or use **Open in project** for the task. Approval reserves a slot and stays **Awaiting confirmation**. **Secured requires a separate supplier confirmation matching the approved terms**; no automatic purchase, payment or signature occurs. Requirement changes preserve prior decisions as superseded history and clear current quotes/approvals.

**Calendar** marks saved dates with red dots and shows Upcoming dates and Past dates for the displayed month. Selecting a day filters that month's list; changing month resets the day filter. Today's dates remain upcoming. Past dates do not imply that unfinished project work is completed. Task deadlines, proposed/confirmed delivery dates and pending quote expiries feed the calendar. Sidebar badges show pending approval checkpoints and distinct upcoming saved dates.

**Connections** contains suppliers with recorded messages or a prior human selection, with history and a fresh-request shortcut. Research candidates and unsent drafts alone do not count as relationships.

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

- Supabase projects, task conversations, ranked supplier checkpoints, Drive snapshots, extracted memory, scoped conversations, requests, drafts and human decisions. Atomic saves/chat completion, conflict detection and retry protection. Seven additive migrations are in `supabase/migrations`, applied to the connected KawTeam project.
- Project-scoped context retrieval/citations. Stable Drive file identities replace stale versions and exclude archived documents from memory. Existing document records remain compatible.
- Optional Gemini conversation and Tavily source discovery adapters. **Neither key is configured yet.** Public-source candidates remain unquoted; unknown terms and contacts are never invented.
- Legacy controlled tote scenario: **Prepare enquiry → Approve draft → Send in demo → Check demo reply**. Exact-message hash/revision, 30-minute approval expiry, single-use send and three-round cap. Replies are fictional and saved; no external email is sent.
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

`npm run test:e2e` runs the read-only task layout check. `node tests/refinement-browser.mjs` checks the chat, persistent sidebar, overview and calendar. Screenshots are ignored under `apps/web/test-results/`.

For the complete saved task/liaison check, run from `apps/api`:

```powershell
$env:PYTHONPATH='src'
$env:KAWTEAM_TEST_URL='http://127.0.0.1:3000'
.venv/Scripts/python.exe tests/live_task_browser.py
```

This opt-in check creates a labelled QA project, verifies separate tasks, continued edits, role restrictions, ranked rejection/approval and a separate simulated supplier confirmation. It restores the original tote sample in `finally`; remove only the QA project ID printed afterward. Its browser script requires the wrapper's explicit mutation flag. No external email is sent.

`tests/live_task_database.py` is a separate opt-in database check for concurrent task starts/retries, preserved legacy history, permissions and atomic in-place request/chat completion. It prints the labelled disposable project ID for scoped cleanup. Older chat-home/outreach/choice browser scripts document previous UI versions and are superseded by the current task checks.

## Free deployment preparation

The deployment target remains two Vercel projects from this repository: Next.js root **apps/web**, FastAPI root **apps/api**. The API exports `app` from `index.py`, an officially supported [FastAPI entrypoint](https://vercel.com/docs/frameworks/backend/fastapi). Use your free plan and check its [function limits](https://vercel.com/docs/functions/limitations) before deployment; no paid hosting has been enabled.

Deploy the API with its local server environment values, preserving the database credential matching the applied migrations, and set `COOKIE_SECURE=true`. Deploy the web with `NEXT_PUBLIC_DATA_MODE=api`, `KAWTEAM_API_URL=https://your-api.vercel.app`, and the matching server-only `KAWTEAM_GATEWAY_SECRET`. Never expose secrets with a `NEXT_PUBLIC_` prefix. Verify the deployed session, project/chat, Drive and controlled outreach flow before submitting.

Database tables deny direct public access. Scoped RPCs require a separate secret-held backend credential. [Checkpoint security notes](docs/PHASE_3_7_CHECKPOINT.md) explain the expected Supabase advisor warnings.

Submission: public GitHub repository, deployed app URL, presentation PDF, group name and campus branch. Aim **11 October 08:45 MYT**, ahead of the supplied 09:00 buffer cutoff.

See the [current task checkpoint](docs/TASK_CONVERSATIONS_CHECKPOINT.md), [UI refinement checkpoint](docs/CHAT_OVERVIEW_REFINEMENT_CHECKPOINT.md), [chat/Drive checkpoint](docs/CHAT_HOME_DRIVE_CHECKPOINT.md), [implementation plan](docs/plans/2026-10-10-chat-home-drive.md), [earlier makeover](docs/PROJECT_MAKEOVER_CHECKPOINT.md), [backend checkpoint](docs/PHASE_3_7_CHECKPOINT.md) and [checklist](KAWTEAM_BUILD_CHECKLIST.md). Original blueprint retained.
