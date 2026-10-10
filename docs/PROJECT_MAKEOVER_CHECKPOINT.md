# KawTeam project workspace makeover

Historical checkpoint. The current interface and Google Drive memory flow are documented in [CHAT_HOME_DRIVE_CHECKPOINT.md](CHAT_HOME_DRIVE_CHECKPOINT.md).

10 October 2026. Supersedes the previous home/chat navigation in PHASE_3_7_CHECKPOINT.md. WorkBuddy and external email remain deferred.

## Product flow

Overview → New project (name only) → general conversation. Upload project plans using Files, the paperclip or context panel. Tasks are optional separate conversations under a project, sharing its documents. Sidebar project names resume work. Overview contains saved activity, pending message approvals and real dates, without fabricated metrics or AI summaries.

Assistant settings persist per project: Automatic (default), Research first or Existing vendor; shortlist size 1–3; optional preferred supplier and instructions. Automatic distinguishes new discovery from repeat orders. Explicit supplier names take precedence over preferences. Ambiguous suppliers require clarification. Implicit previous-supplier references stay in the current project/task. An explicit library choice can reuse another project's supplier identity.

Repeat orders skip discovery and clear previous price, delivery terms, deadline fit, approval and decision. Each needs fresh terms and human review. Research refresh preserves prior explicit human decisions and approved recipients. The organiser still approves exact outgoing drafts and makes the final supplier choice; nothing is automatically bought.

## Routes and design

- `/`: project overview.
- `/projects/:id`: general conversation.
- `/projects/:id/tasks`: optional task list.
- `/projects/:id/tasks/:taskId`: isolated task conversation.
- `/projects/:id/files`, `/projects/:id/approvals`, `/projects/:id/vendors`: project resources.
- `/approvals`, `/calendar`, `/vendors`, `/connections`: workspace views.
- `/cases/:id`: supplier evidence, outreach and human decision; return link resumes its project/task conversation.

Palette: #00545f deep teal navigation, #d6fb00 primary project action, #ecffb6 active and selected surfaces, neutral white content. Local Jakarta font, restrained outlines and spacing. No login page; the profile menu switches demo roles.

The configured shadcn stdio MCP was connected using `scripts/shadcn-mcp.py`; its registry reference is recorded in `docs/shadcn-registry-reference.json`. Official shadcn Button, Dialog, DropdownMenu, Tabs and Calendar components are installed. Calendar date attributes use deterministic formatting to avoid Windows/browser locale hydration mismatch. Dependencies were fetched from the Yarn npm mirror with TLS verification enabled after the default npm registry certificate failed locally.

## Persistence

Applied additive migration `202610100004_project_tasks_chat.sql`. Existing records retained. Settings/task writes require an editable signed demo role. Atomic chat RPC validates task membership; tasks have independent threads. Documents remain project-wide. Supabase direct anonymous access stays denied.

## Honest integration status

Gemini/Tavily keys are not supplied. External email is unconnected. WorkBuddy remains deferred by the user. Settings and routing work now; live discovery, AI conversation and external outreach require their integrations. Controlled sample offers and emails remain explicitly simulated. No public deployment was created as part of this makeover.

## Verification

Backend: 40 tests and Ruff. Frontend: 13 domain tests, TypeScript, ESLint, production build. Production browser coverage: project creation, upload/memory, general chat, optional task isolation, persisted settings, repeat supplier route, calendar, responsive overflow and Observer permissions. Controlled outreach browser verifies exact approval, single send, reply, consumed approval and unchanged human selection, then restores the sample. Desktop and mobile screenshots reviewed. Independent frontend/backend review findings corrected. Next.js and its lint configuration updated to 16.4.0; production dependency audit reports zero vulnerabilities. Temporary QA project records removed after verification.
