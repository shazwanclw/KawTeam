# KawTeam chat-first and Drive context checkpoint

10 October 2026. This supersedes the overview-first navigation and exposed upload flow in `PROJECT_MAKEOVER_CHECKPOINT.md`. Existing project records, documents and human decisions are retained.

Later UI refinements are documented in [the 11 October checkpoint](CHAT_OVERVIEW_REFINEMENT_CHECKPOINT.md), which supersedes the assistant-settings trigger, raw approval preview and overview navigation details below.

## Implemented flow

The landing page starts with the user's slogan and a centred chat composer. The project selector changes conversation context. With no selected project, the first request creates a project and saves its conversation atomically. Retries use the same request identity and do not create another project or lose the first message.

New project asks for name and an optional Google Drive URL. Its permanent creation action is the plus beside Projects in the sidebar. The empty project selector also offers Add a project. There are no new upload buttons or file inputs.

The sidebar collapses at all viewport sizes and contains Chat; Overview with Recent Activity, Approval and Calendar; a searchable, scrolling Projects list; and Connections. The old provider Connections page is removed from navigation. Vendor Library becomes Connections and includes only suppliers with sent/received messages or an explicit prior human choice.

Projects default to Chat, with Recent Activity, Approval and Subprojects tabs. Optional subprojects use existing task records, independent conversations and shared parent-project context. Legacy task/case routes remain compatible.

Activity tables display at most 15 actual saved case actions, newest dated actions first, with undated sample clocks labelled. Rows open a dialog with the recorded action, request context and relevant evidence/history. No synthetic activity metrics or background progress are added.

Global approval rows open summaries and lead to the owning project's review. Project review shows exact outgoing text, recipient, revision, supplier evidence and recorded conversation. Organisers can approve or return a pending draft. Approval is separate from sending. Confirmed, valid supplier offers lead to comparison and an explicit human choice; unconfirmed candidates do not request a final decision.

Connections show supplier relationship history and a fresh-request shortcut. Reusing a supplier skips discovery, but resets previous terms and requires a new quotation and approval. Opening the shortcut alone does not save assistant preferences; they are applied when the user sends the request.

Agent status is derived from saved work: ready, integration needed, review needed or awaiting reply. Working appears only during an actual client request. Calendar displays saved project dates and supplier deadlines; continuous agent scheduling is not active.

## Design

Neutral white canvas and pale sidebar, deep teal text/actions, restrained lime accents from #00545f / #d6fb00 / #ecffb6. Local Jakarta typography, spacious chat entry, compact project tabs, consistent table/dialog styling and responsive layouts. Existing official shadcn Dialog, DropdownMenu, Button and Calendar components are reused. No Chat/Work toggle or model selector.

Desktop and mobile home, project approvals and connection-history screenshots were inspected. Tables scroll inside their own containers; positioning their scroll containers prevents absolutely positioned accessible headings from widening the mobile page.

## Drive ingestion and memory

New adapter: `apps/api/src/kawteam/drive.py`.

- Only validated HTTPS Google Drive/Docs links are accepted. User links supply IDs, never arbitrary fetch destinations. API calls use fixed Google hosts, readonly credentials and no redirects.
- `GOOGLE_DRIVE_API_KEY` supports public-link reads. `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` supports private content explicitly shared with its service-account email. No credential is currently supplied; links save as `awaiting_access` without claiming ingestion.
- Docs/Slides export as text; Sheets export as XLSX so all worksheets are available. Existing PDF/DOCX/XLSX/TXT/MD/CSV extractors are reused. Unsupported, scanned or unreadable documents are reported.
- Limits: 3 MB per file, 20 current documents per project, 80,000 extracted characters per file; folder depth 3, 10 folders, 10 listing pages, 45 requests, a 45-second read budget and bounded credential refresh. Chunk reads check elapsed time and size.
- Each Drive file has a stable project-specific document identity. Refresh replaces that identity's current text, rather than appending stale versions. Facts are recomputed from active documents, including when a budget is edited and then reverted.
- Complete successful sync archives files removed from the source. Partial reads retain unread previous documents; failures preserve saved memory. Changing to an inaccessible source clears that source's import count/date and separately attributes preserved memory to its previous successful source.
- Source/status/current documents are visible in the Project memory dialog. Refresh is manual. There is no scheduled sync, Google user OAuth or WorkBuddy-driven refresh yet.

Applied `202610100005_drive_snapshot.sql` adds `kawteam_drive_snapshot`. The write is atomic, guarded by workspace secret, editable demo role, project revision and document ownership checks. Archived documents are excluded from retrieval. Existing RLS/public access restrictions remain.

Documents are contextual data, not authority to change the user's goal, send messages or select suppliers. The organiser retains exact outgoing-message approval and final supplier selection.

## Natural prompts

The deterministic parser supports currency budgets including RM5k, quantities including shirts/items/people/pax, explicit ISO deadlines or day/month/year phrasing, and locations such as “in Subang Jaya”. Ambiguous or missing dates remain conversational clarification. Missing context directs users to chat or authorised Drive memory.

## Verification

- 53 backend tests passed; Ruff clean.
- 26 frontend domain/activity tests passed; ESLint and TypeScript clean.
- Next.js 16.4.0 production build passed.
- Production browser acceptance passed: chat home, collapsed navigation, project picker, name/optional Drive creation, honest missing-access status, selected/no-project chat, activity/approval dialogs, subproject isolation, Connections, Observer restrictions and widths 390/768/1280/1440.
- Additional final browser checks passed for selecting Sunway Got Talent, sidebar project search, the saved calendar and mobile project layouts.
- Controlled outreach browser passed through the new project approval dialog: exact approval, one simulated send, saved supplier reply, consumed approval, Connections history and prefilled fresh request. The original sample was restored; final human supplier selection was unchanged.
- Live Supabase Drive snapshot checks passed: edit/revert replacement, active-document count, archived exclusion, role/secret rejection and atomic memory updates. Their disposable records were removed.
- Drive provider reads were tested with injected transports. An actual Google account/folder read cannot be tested until a Drive credential is configured.
- Independent frontend/backend reviews completed; identified routing, retry and Drive snapshot/provenance issues were corrected.

Ignored screenshots are under `apps/web/test-results/`. The obsolete overview/upload browser test was removed; `npm run test:e2e` now runs `tests/chat-home-browser.mjs`. Final cleanup removed 25 disposable QA records and 44 related retry/action records, preserving Sunway Got Talent, Tech Night and the original supplier samples.

## Still pending

Google Drive credentials; Gemini/Tavily keys; WorkBuddy (deferred by the user); real external email; public deployment; final hackathon presentation/submission. The current app makes these limits visible and does not claim live provider results or autonomous background work.

See the README for local commands, credential options and deployment preparation. No paid hosting or paid provider billing has been enabled.
