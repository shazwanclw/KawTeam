# Chat and overview refinement implementation plan

**Goal:** Reduce chat clutter, preserve open navigation, and make overview show business milestones, concise approvals and month-specific dates.

**Architecture:** Keep shared project chat and persisted procurement state. Hold sidebar visibility in the root workspace provider so routing does not reset it. Pure activity/schedule helpers supply milestone rows, approval summaries and sidebar counts; existing role/revision checks remain authoritative.

**Tech stack:** Next.js, React, TypeScript, shadcn Dialog/Calendar, existing FastAPI/Supabase actions.

The user requests implementation and has authorised autonomous UI recommendations. No further design gate is needed. Work in this configured workspace, preserve existing records and do not publish or send external messages.

## Design choices

Use a concise approval summary backed by saved messages/terms, with direct approval in the modal. An email preview would contradict the requested presentation; an invented AI summary would obscure provenance. Keep request constraints, the business content of the prepared enquiry, latest reply per supplier and confirmed offers. Remove email headers, raw conversation history and workflow traces. Final supplier choice remains an explicit radio selection followed by Approved.

Activity lists completed comparisons, actual recorded outreach/replies and human checkpoints; internal request parsing/planning/setup logs are excluded. Multiple sends roll up to the number of suppliers actually contacted, never the number merely discovered. Preserve demo labels. Pending enquiries are labelled ready for approval, never contacted.

Calendar separates upcoming and past dates in the displayed month. Past dates do not imply that unresolved supplier work is complete. Today's dates count as upcoming. Sidebar approval count counts pending checkpoints; Calendar count counts distinct saved upcoming dates. Month navigation clears an old selected day.

## Implementation steps

1. Add failing domain tests for milestone filtering/contact rollups, approved decision history, concise summaries and schedule month/day/date counts. Add browser acceptance for the new slogan, removed controls, navigation persistence, sidebar counts, overview tabs absent, summary approval and month switching.
2. Modify `src/lib/activity.ts`; create `src/lib/schedule.ts`. Keep preserved user decisions and roles. Update activity/approval test expectations for approved history.
3. Simplify `chat-surface.tsx`; remove preferences trigger and decorative helper/prompts/status text. Remove the edition badge. Add root-provider navigation state; stop closing it on links/project creation. Remove overview page tabs and add sidebar badges.
4. Rewrite project/global approval detail with concise business summaries, direct message approval and explicit supplier selection. Filters are only Approval Needed and Approved. Keep approved history; use Open in project for deeper context.
5. Make Schedule controlled by visible month and selected date, red scheduled dots, month-scoped upcoming/past lists. Test year boundaries and invalid dates. Reuse existing shadcn Calendar.
6. Run domain tests, typecheck, lint and build. Run actual browser flows including role restrictions and direct approval with restore. Inspect desktop/mobile screenshots. Document results; preserve real projects and remove only disposable QA records.

## Completion evidence

Implemented and verified on 11 October 2026. See [the refinement checkpoint](../CHAT_OVERVIEW_REFINEMENT_CHECKPOINT.md) for acceptance coverage and retained integration limits. Frontend: 36 tests, lint, TypeScript and production build passed. Backend: 53 tests and Ruff passed. Browser checks covered the requested UI, complete chat/project flow, direct enquiry approval and explicit supplier approval with role restrictions; sample mutations were restored. Disposable test projects were removed. A fresh `npm run dev` session also hydrated and loaded the backend project session.
