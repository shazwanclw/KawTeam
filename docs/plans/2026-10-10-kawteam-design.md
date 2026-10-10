# KawTeam product and system design

Reconciled 11 October 2026. This file retains its original filename for existing links, but describes the current design. [Current product specification](../CURRENT_PRODUCT_SPEC.md) is authoritative; [integration status](../INTEGRATION_STATUS.md) records account evidence.

## Purpose and hackathon fit

Student organisers and small businesses describe sourcing/liaison goals in chat. KawTeam keeps project context, task conversations, supplier evidence and human decisions together. WorkBuddy is intended to perform useful tool-based execution, not serve as a label on Gemini chat. The supplied Track 2 criteria require real problem/value, agentic planning/execution, meaningful WorkBuddy use, end-to-end outcomes and verifiable results. Supplier liaison is the primary scenario; broader sponsorship/partnership ambitions remain future work.

Supplied submission requirements: public repository, deployed app, PDF slides, group/campus, 11 October 2026 09:30 MYT deadline with 30-minute buffer. Organiser documents are reference data; user decisions control the product. No invented scoring weights or claimed acceptance of all simulated workflows.

## Boundaries and selected architecture

| Boundary | Design |
|---|---|
| Conversation | Gemini understands requests, asks essential questions and explains saved context |
| Execution | WorkBuddy should plan/use scoped tools and save results; eight scoped tools exist; actual desktop orchestration/website trigger is pending |
| Rules | FastAPI validates scope, roles, revisions, budgets and terms |
| State | Supabase projects/tasks/threads/cases/evidence; seven migrations |
| Discovery | Bounded Tavily public sources; provisional candidates |
| Communication | Gmail locally authorised; send receipts and saved-thread reads; grounded commercial interpretation implemented; live commercial acceptance pending |
| Context | Project Drive snapshots and retrieval; real access not configured |
| Final choice | Organiser approves; separate supplier receipt establishes secured |

The team selected Gemini plus desktop WorkBuddy MCP. Personal credits and Google login did not establish hosted Enterprise API access. MCP makes WorkBuddy a consumer of KawTeam tools, not automatically a service callable by the website. A verified trigger/API/bridge remains a prerequisite for automatic website execution. Do not assume a desktop process on Vercel or install undocumented account proxies.

## Screens and visual direction

Chat-first light interface: deep teal `#00545f`, lime `#d6fb00`, pale lime `#ecffb6`, neutral surfaces, Jakarta type and shadcn primitives. No login, uploaded-file UI, preferences trigger, model picker, top project tabs or generic metrics.

Main Chat picks a project; a new request creates a task. Project Chat defaults New Task and can resume a selected transcript. All Task / Recent Activity sit below it. Task detail is roughly 70/30 Secured/Approval versus Upcoming events, stacked on mobile. The sidebar retains Chat, Overview's three links, searchable Projects plus and Connections. Open navigation survives route changes until closed.

Overview uses 15 milestone rows, concise Approval Needed / Approved dialogs and month-scoped red-dot dates. Connections derives from saved real or explicitly simulated communications, not discovery. Project memory shows Drive source/access/status; no access is claimed from a link alone.

## Domain and execution rules

Item quantity is separate from supplier target. Keep the full returned pool for verification/liaison rather than choosing three. Current search is still bounded to five source candidates. Rank final matching quotes by landed cost/arrival/name; retain unknown cost/contact/date. Human decisions reserve slots and total budget, rejection advances waitlist, and approval alone never becomes secured.

Quotes and confirmations must reference current hashed terms; edits supersede prior decisions. Repeat supplier use preserves identity only. Agent enquiries/negotiations are intended to be non-binding within user constraints; human approval occurs at final choice after liaison. Legacy per-draft approvals are retained compatibility, not the primary design. No payment, purchase or signature.

## Persistence, permissions and context

Next.js forwards allowlisted routes and server-only gateway credentials. FastAPI verifies signed role cookies. Shared-demo role selection is intentionally public and is not real tenant authentication. Tables deny direct public reads/writes; protected scoped RPCs perform transactional task/message/case/snapshot updates with retries and expected revisions.

Project documents are untrusted reference content; tasks have separate history and shared parent memory. Relevant active excerpts/citations inform Gemini. Drive refresh replaces versions, archives deleted files only after complete success and preserves readable previous data on failure. No background sync or Google Calendar service.

## Implementation evidence and open work

Gmail is locally authorised; one controlled test send has a saved provider receipt, and saved-thread reading works. Eight scoped WorkBuddy MCP tools exist and real local project/task reads pass. Actual desktop orchestration, website trigger, automated contact enrichment, live supplier quote/confirmation acceptance, Drive access and public deployment remain pending. See [integration status](../INTEGRATION_STATUS.md).
