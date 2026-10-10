# Chat and overview refinement checkpoint

11 October 2026. This updates the chat/Drive interface while preserving project memory, conversations, backend actions and the team's final supplier decision.

The later [task conversation checkpoint](TASK_CONVERSATIONS_CHECKPOINT.md) supersedes project/subproject navigation and outgoing-message approval details here.

## Current interface

- Main chat headline: **What are we going to KawTeam today?** Removed the Hackathon edition badge, composer footnotes, quick vendor prompts, connection-status footer and assistant-preferences trigger. Project selection and Drive context remain accessible.
- Navigation starts closed. Once opened it stays open across page, project and subproject navigation until explicitly closed. A full reload starts closed again. Overview section links appear only in the sidebar.
- Recent Activity keeps up to 15 completed milestones and human checkpoints. Parsing, planning, connection setup and draft-edit logs are excluded. Supplier contact counts derive from actual saved sent messages. Controlled demo provenance is retained.
- Sidebar Approval counts pending checkpoints. Calendar counts distinct upcoming saved dates, including today, without duplicating the same date across deadlines.
- Approval filters are **Approval Needed** and **Approved**. Details contain the request constraints, current enquiry's business terms and latest saved reply per supplier. Email headers, recipient addresses, raw conversation history and exact-checkpoint metadata are absent. **Open in project** leads to the owning conversation.
- The **Approved** button approves a message or an explicitly selected supplier. No supplier is preselected. Only organisers can approve; backend role/revision checks remain authoritative. Approving does not send email or place an order. Approved enquiries and final human selections remain visible in Approved history.
- Calendar dates use red dots. Upcoming dates and Past dates are scoped to the visible month and optional selected day. Month changes clear the selected day. Past dates mean elapsed dates, without claiming unfinished work is completed.

## Verification

- Frontend: **36 tests passed**, ESLint passed, TypeScript passed, production build passed.
- Backend: **53 tests passed**, Ruff passed. No backend production code changes were required.
- Read-only refinement browser checks passed for removed controls, sidebar persistence, badges, milestone filtering, approval summaries, red dots, month switching and viewport widths 390, 768, 1280 and 1440.
- Complete chat/project browser regression passed: optional Drive link, honest access-needed status, selected/unselected project requests, separate subproject conversation, observer restrictions and responsive layouts.
- Controlled outreach browser check passed through global approval, simulated send/reply, Connections history and fresh request. The original sample was restored; no real email was sent.
- Explicit supplier-choice browser check passed: opening the summary never selects a supplier, teammates cannot approve, an organiser's explicit choice persists and appears in Approved history. The original sample was restored; no outgoing message was added.
- Desktop and mobile screenshots were inspected. Browser artifacts remain ignored in `apps/web/test-results/`.
- Removed only the two disposable projects created by the chat regression, with 6 test records and 10 test actions. Sunway Got Talent and Tech Night remain.
- A fresh default `npm run dev` server hydrated and loaded its backend session. Production preview remains at `http://localhost:3000` with the existing API at port 8000.

## Retained limits

Drive, AI/search, external email and WorkBuddy integration status is unchanged. Saved milestone presentation does not create background execution. Supplier replies and terms in the sample remain explicitly illustrative. Changes are local; this refinement has not been deployed or pushed.
