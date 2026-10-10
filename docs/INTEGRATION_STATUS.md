# KawTeam integration status and next inputs

Updated 11 October 2026. Status is based on code/configuration and recorded checks, not on the presence of a key alone. No secrets are documented. See [current product specification](CURRENT_PRODUCT_SPEC.md).

## Verified and pending

### Presentation refresh — 11 October 2026

The workspace's old application records and action history were backed up privately outside Git, then replaced in a single digest-checked transaction. Supabase now contains exactly **three projects, four supplier tasks, four conversations and three project briefing documents**. Workspace credentials, schema and provider configuration were retained. [Presentation scenarios](DEMO_SCENARIOS.md) cover T-shirt sourcing, ten exhibitor placements and repeat catering. Their 88 sent/received messages are explicitly simulated; no real supplier was contacted during this refresh. Earlier live Gmail test receipts are retained only in the private backup rather than the active demonstration workspace.

The initial component restyle retained layout and copy, with twenty screenshot comparisons reporting no geometry differences greater than 1 px. The user's subsequent refinements explicitly requested the reference's larger Heros typography, exact gradient/material values, approval/vendor cards and a standalone calendar. Those visual changes supersede the earlier geometry baseline for the affected components. Recent Activity's duplicate inner header is removed; Overview links have icons; the official logo and stationary hamburger share a centre line. Calendar summaries are grouped by project/day with at most three per date, without deleting underlying saved dates.

Remote-seeded UI checks verified eight pending approvals, nineteen searchable vendor cards, task transcripts, full email histories and separate controlled confirmation actions. Checks passed: 154 backend tests, 47 frontend tests, TypeScript, ESLint, Ruff and the compact/reference/history/profile, approval-card and grouped-calendar browser suites. These checks do not constitute live supplier or deployed acceptance.

| Service | Current evidence | Remaining work |
|---|---|---|
| Supabase | Configured; API reads saved projects; seven migrations applied; task/chat transactions tested | Deployment environment and final deployed checks |
| Gemini | `GEMINI_API_KEY` present; adapter succeeded; website chat returned and saved a Gemini reply after backend reload | Usage/error handling and deployed smoke test |
| Tavily | `TAVILY_API_KEY` present; real bounded supplier search returned five source candidates | Broader sourcing and real commercial outreach acceptance |
| Google Drive | Adapter and persisted snapshot/retrieval exist; neither credential configured | Authorised folder, credential and actual ingestion test |
| WorkBuddy | Nine scoped tools discovered over real stdio; real project/task reads succeed against Supabase | Actual desktop orchestration evidence and supported website-to-WorkBuddy trigger |
| Gmail | Google consent and sender identity verified; one authorised test sent with saved receipt; saved-thread read succeeds | Real supplier quote/confirmation acceptance and deployed validation |
| Vercel | Next.js/FastAPI deployment roots prepared; no public deployment verified | Account/GitHub access, environment values, two deployments and deployed acceptance |

The backend reports email configured and WorkBuddy desktop tools available, with its website trigger not connected. `GET /email/status` performs a live sender identity check. Configuration is not evidence of complete autonomous execution.

## Gemini and Tavily

Use `apps/api/.env`, not frontend public variables. Existing keys are already working; do not request replacement keys without an actual provider failure.

```dotenv
GEMINI_API_KEY=YOUR_PRIVATE_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
TAVILY_API_KEY=YOUR_PRIVATE_KEY
```

The current configured model passed a live request. Restart/reload FastAPI after environment edits; configured status only means a value is loaded, so keep actual success/failure evidence separate. Provider usage is bounded; no paid upgrade or billing was enabled by the implementation.

Tavily is web discovery, not email or a complete social-platform API. Its free plan was checked as 1,000 credits/month with no card required; check [current provider pricing](https://www.tavily.com/pricing) before relying on quotas. Do not promise free unlimited use or reliable access to private/logged-in social content.

## Google Drive access

Provide an intended folder/document URL plus one supported server credential:

- `GOOGLE_DRIVE_API_KEY`: Drive API enabled, publicly accessible files only.
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON`: full service-account JSON; share the private folder with its `client_email` as reader.

A Gemini key is not automatically Drive authorisation. A private folder URL alone is insufficient. No Google user sign-in flow or continuous Drive sync exists. Refresh currently reads a bounded snapshot on demand. Credentials stay on the backend.

## Gmail: current sender shazwanclw@gmail.com

Google consent and sender identity verification succeeded for `shazwan15122005@gmail.com`, using `Downloads/Email API.json`. One user-authorised labelled test was sent to `shazwan1512alt@gmail.com`; its Gmail receipt is saved in **QA - Email connection test**. No real supplier was contacted. One actual matching reply was received and saved, completing the controlled send/reply check. The sender was then changed to `shazwanclw@gmail.com`; its Google consent and identity check passed. No message has been sent from the new account.

The CLI requests `gmail.send` and `gmail.readonly`, with no delete permission, and verifies the selected sender before storing the token in ignored `apps/api/.secrets/gmail-token.json`. From `apps/api`:

```powershell
$env:PYTHONPATH='src'
.venv/Scripts/python.exe -m kawteam.gmail_auth
# Historical fixed-account test already passed; do not rerun it under the new sender.
```

`gmail_check send` is an opt-in fixed-recipient test already executed. Its durable identity prevents a rerun sending another email. Local `.env` uses `GMAIL_OAUTH_CLIENT_PATH`, `GMAIL_SENDER`, optional `GMAIL_TOKEN_PATH`. Deployment can use secret `GMAIL_AUTHORIZED_USER_JSON` instead of a local file. Downloads paths do not exist on Vercel. Never put tokens in Git or public frontend variables. Local authorisation is not public production OAuth acceptance; testing tokens may need reauthorisation.

Live services persist intent before sending and save actual Gmail message/thread IDs. Incoming IDs are deduplicated. Reserved/uncertain sends block automatic retries: inspect the sender's Sent folder and reconcile manually, without bypassing the block through a new request ID. Limits: four messages per supplier, 60 per task, 20 threads per sync, last 30 messages per thread. Human-verified contacts and source-backed addresses are accepted. Automatic contact verification uses Tavily extraction and grounded Gemini service relevance; ambiguous or unavailable contacts are recorded without invented addresses. Raw replies are untrusted evidence. The interpretation tool uses Gemini plus verbatim evidence/amount/date validation: incomplete terms stay out of approval, and a confirmation needs current human approval, matching terms and a later provider timestamp. Only explicit ISO dates and RM/MYR amounts qualify; unclear replies need clarification. Extraction and confirmation guards pass automated tests; the actual test acknowledgement was correctly excluded from final approval. A real commercial supplier run and follow-up orchestration remain unverified.

[Google Gmail Python quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python), [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes).

## WorkBuddy direction and access

```text
Gemini -> website conversation / request understanding
WorkBuddy -> KawTeam MCP tools -> shared API / saved task state
Website -> WorkBuddy runner: still unresolved
```

WorkBuddy's Models API-key screen connects external models into WorkBuddy; it is not proof of an API allowing KawTeam to start its agent. Personal Google-sign-in credits do not establish Tencent Cloud Enterprise entitlements. Hosted Managed Agents access has not been obtained.

The user's actual UI path is Connectors -> MCP Server Management -> Add MCP. Its configuration file is `%USERPROFILE%/.workbuddy-ai/mcp.json`. Preserve unrelated entries. Reconnect the KawTeam entry to discover nine tools: health, projects, task/context, research, sender status, non-binding enquiry, saved-thread reply sync and quote/confirmation interpretation. No final approve/reject tool is exposed.

See [WorkBuddy integration guide](integration/workbuddy.md) for configuration and acceptance. The agent needs real scoped tools, limits, durable checkpoints and a verified start/resume mechanism. Do not install unofficial personal-account-to-API proxies or assume an undocumented endpoint to satisfy deployment.

## Deployment and submission

Target zero out-of-pocket hosting with two Vercel projects from the same repository: web root `apps/web`, API root `apps/api`, plus the existing Supabase project. Recheck eligibility and current limits before publishing; this is a target, not an unlimited-service guarantee.

Use server-only secrets, HTTPS API URL, `COOKIE_SECURE=true`, and the matching web/API gateway secret. Replace the local API URL on deployment. Vercel request functions cannot be assumed to run an always-on desktop WorkBuddy process or a continuous inbox-polling loop.

Remaining submission inputs: team/group name, campus branch, presentation PDF and final public application/repository verification. Original supplied deadline: 11 October 2026, 09:30 MYT, with a 30-minute buffer; operational cutoff 09:00, target 08:45. No submission receipt or final public URLs have been verified.

Mailboxes and request scopes are isolated: saved intents/replies carry the sender and request hash. Brief changes retain verified contact identity but require fresh enquiries/terms; old replies cannot regain approval eligibility. Latest replies use provider timestamps, not thread traversal order. These review findings have regression coverage.

Website outreach status was corrected after the T-shirt task showed five uncontacted results. Chat receives authoritative email configuration, contact count and send count; it must not ask to reconnect configured Gmail. Supplier rows distinguish Not contacted, Awaiting reply and Reply received. Website contact verification and bounded enquiry/reply steps are now implemented and tested. The supported website-to-WorkBuddy trigger remains unavailable; website automation uses the configured Gemini/Gmail services directly.


## Automatic website outreach (11 October 2026)

Chat supplier requests now persist an authorised task-scoped outreach queue. The visible website runs one bounded step approximately every 15 seconds: verify a public supplier business contact, send a non-binding enquiry, sync saved Gmail threads, interpret a current reply, or request missing/revised terms. Only a literal address from the supplier's own site is used, with grounded service evidence; ambiguous contacts and provider failures remain visible on the task. All discovered candidates stay in the pool; unrelated sources are not emailed.

Email receipts, request hashes, deterministic send IDs, compare-and-swap writes and a 180-second step lease prevent duplicate/concurrent sends. A pause instruction disables further steps; asking to view contact details does not authorise sends. Enquiries stop for unselected suppliers when the approved target is filled. Human supplier selection remains in KawTeam. A later matching confirmation can mark an approved supplier secured; the runner does not send orders or binding acceptance.

Existing tasks are not silently enrolled: continue that task and say `Email the suppliers` or `Start outreach`. New or edited sourcing requests queue outreach automatically, unless the user asks for research only. Keep KawTeam open to advance website ticks; a permanently running hosted worker is not implemented. WorkBuddy can call `kawteam_outreach_step` for the same authorised task, but this does not give the website an inbound WorkBuddy API. Reconnect desktop MCP to discover the ninth tool.

Verification: controlled mailbox tests, live read-only supplier contact extraction, and an isolated browser tick check pass. No real supplier enquiry was sent during development. Real commercial supplier acceptance, public deployment, unattended scheduling and Drive access remain pending.

## Compact autonomous chat update ? 11 October 2026

Pages use a compact hamburger rail and sidebar profile switcher. Project tabs include Failsafe. Sparse briefs can run research and provisional enquiries; unknown quantity uses pricing tiers, unknown destination is omitted, and absent deadlines use an explicit provisional 14-day assumption. Final scope/fit checks and organiser selection remain enforced. Recorded outreach progress is posted to the saved task transcript; foreground polling still requires KawTeam to be open. No real supplier email was sent by the verification tests for this update.

## Chat references update ? 11 October 2026

Automatic projects now use concise purpose names; the existing prompt-named project was renamed T-shirt Sourcing. The Drive icon is available before selecting a project and until a project has a saved source. A paperclip supports readable task-scoped documents, up to three files and 3 MB total. Multipart submission reads files before the assistant receives context; retries bind file content and link identity. Drive credentials/access are still required for ingestion. The hamburger stays at a fixed screen position and toggles the sidebar without separate close controls.
