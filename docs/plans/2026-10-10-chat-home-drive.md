# Chat home and Drive project context implementation plan

**Goal:** Make chat the entry point, simplify navigation and provide project context from optional Google Drive links.

**Architecture:** Shared composer and conversation for the main chat and project/subproject chat. Project-scoped activity and approval tables reuse persisted case evidence and exact-message approval rules. Optional Drive ingestion stores extracted document context in existing project memory; no new uploads are exposed in the UI.

**Tech stack:** Next.js/React/TypeScript, existing shadcn Dialog/DropdownMenu/Tabs/Calendar, FastAPI, Supabase protected RPCs.

**Implementation status:** Completed locally and browser-verified. See [current checkpoint](../CHAT_HOME_DRIVE_CHECKPOINT.md) for test evidence and the credential-dependent integrations still pending. Real Drive account reads await credentials; WorkBuddy remains deferred.

The user explicitly requests this flow and implementation. Existing autonomous design authorisation applies; no additional design approval gate or question is required. Use the current workspace to preserve configured local servers and ignored credentials.

## Design and alternatives

Choose a single chat surface with a project selector, rather than separate home intake and project composers, because selection should only change context. Keep project creation available from the sidebar Projects plus and the empty project selector; avoid duplicate permanent create buttons. A full-screen dashboard would obscure the primary feature, while a flat list of chats would hide approvals and project history.

Light neutral canvas, deep teal type/navigation, restrained lime details; spacious centred initial composer with user slogan “If you have trouble searching, KawTeam with us!” No Chat/Work switch, model picker, upload buttons or provider settings navigation. Hamburger collapses the sidebar at all sizes.

Sidebar: Chat; expandable Overview → Recent Activity, Approval, Calendar; scrollable Projects with plus/search; Connections. Project chat includes compact tabs: Chat, Recent Activity, Approval, Subprojects. Subprojects are named optional separate conversations sharing project Drive context. Existing task records remain compatible internally.

Recent Activity: last 15 saved case actions/logs, one row per action, scoped globally or by project. Dialog shows full log details, request constraints and links. Approval: pending draft and final-decision rows, dialog preview with evidence/vendor history, global view routes to project approval; organiser actions remain explicit in project/case evidence view. No fabricated runtime progress; distinguish saving/working, awaiting integration, awaiting approval, awaiting reply, completed/pending from persisted evidence.

Calendar includes saved project dates and supplier deadlines. New request facts update its calendar item; no AI-created dates unless they have actually been saved.

Connections lists vendors with recorded conversations or explicit prior human selection, supports opening relationship details/history and continuing a fresh request. Discovered-only candidates do not masquerade as relationships.

## Tasks

1. Backend tests first: optional validated Drive URL, shared/private statuses, project creation and memory sync, no-project chat creates project safely and retries idempotently. Drive links are strict Google IDs/hosts; bounded safe reads, no arbitrary URL fetches, no execution of document instructions. Private access requires configured credential; never claim successful ingestion on failure. Unit-test extraction with injected transports, preserving existing memory/roles.
2. Backend implementation: add Drive source metadata, safe adapter, optional credential configuration, sync endpoint and atomic document saves. Google native files export to supported text; binary files use existing extractors. Folder traversal bounded with pagination/cycle detection; reject or report unreadable/oversized docs. Preserve old snapshots on failed import. No unauthorised emails or WorkBuddy.
3. Browser failing acceptance test: centred chat, collapse nav, selector/no-project creation, optional Drive source, overview tables/dialogs, project tabs/subproject isolation, connections semantics, mobile, observer restrictions.
4. Frontend shared composer: selector, retry-safe no-project send, messages/result workflow cards, assistant preferences, project tabs and optional Drive memory dialog (source/status/manual refresh). Remove exposed uploads; preserved existing docs remain usable for citations.
5. Frontend navigation/tables: collapsed sidebar, project list with plus/search only, Overview tabs, activity modal, approval detail modal, connected vendors list/history. No provider settings page.
6. Verify independently: backend tests/Ruff; frontend tests/typecheck/lint/build; actual production browser flows; desktop/mobile screenshots, independent implementation review. Update docs/current checkpoint. Keep environment files ignored and no paid services.

## Acceptance

- `/` starts with slogan and functional chat composer, selected project optional.
- No selected project prompt creates a persisted project and conversation, no lost/repeated first message.
- New project dialog: name required, Drive URL optional; clear memory sync state.
- Drive contents become project-wide contextual documents only after successful authorised reads.
- Sidebar has exactly requested sections and no persistent duplicate create buttons.
- Global/project tables open meaningful detail dialogs; human approves exact drafts and chooses final supplier.
- Subproject conversations independent, project memory shared.
- UI never claims live AI/search/email/Drive work when integrations are not configured.
