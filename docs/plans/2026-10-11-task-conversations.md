# Task conversations and supplier queue implementation plan

**Goal:** Project chat creates focused tasks, existing task selection resumes its conversation, and each task has ranked human approvals, independently confirmed secured suppliers and dates.

**Architecture:** Preserve event/task/thread/case storage and existing roles. New conversations create deterministic, retry-safe embedded tasks. The case for a task is updated in place when requirements change. Supplier decisions have separate approved and secured states, with immutable term fingerprints; a provider confirmation must refer to the approved terms. Keep legacy case routes compatible, but surface saved cases as task rows.

**Tech stack:** Next.js/React/TypeScript, existing shadcn dropdown/dialog components, FastAPI/Pydantic, Supabase scoped transactional RPCs.

The user explicitly requests implementation and autonomous brainstorming. Use the existing configured workspace; preserve preceding uncommitted UI changes. No extra design approval is required. No external messaging or paid integration is configured.

## Design decisions

Project opens to a compact, centred chat. Default selector is New Task; selecting an existing task expands its transcript. Below the composer are All Task and Recent Activity tabs. Task rows link to a detail page and show pending approval count. Task detail uses approximately 70/30 content/date columns, stacked on mobile. It contains Secured, ranked Approval rows, plus access to the task conversation.

Use explicit `selectionTarget` separate from item quantity: 50 shirts usually requires one company; 10 event vendors requires ten placements. Rank confirmed suitable quotes by landed cost, then arrival, then name. No arbitrary AI scores. All discovered candidates remain in the outreach pool; discovery results still need verified contacts and quotes. Provider result limits are not a three-supplier liaison cap. Approval only occurs after recorded final quotation replies. Waitlist advances after rejection; once all slots are occupied, remaining candidates are not selected locally, without claiming rejection emails were sent.

Approved is not secured. Only a subsequent saved supplier confirmation referencing the exact approved brief/terms marks a supplier secured. Editing procurement requirements invalidates current quotes and selections, retaining prior decisions as superseded history. Follow-up questions preserve the existing task and request. Missing facts remain conversational, never an intake form.

Existing unscoped case requests are presented as task rows without deleting records. Their first continuation materialises the embedded task. Existing general project history is retained as a legacy conversation if present.

## Steps and acceptance

1. Add failing backend tests in `apps/api/tests/test_tasks.py` for task creation/retry/isolation, named event creation, continuation and requirement edits; tests in `test_task_workflow.py` for ranking, target slots, rejection, no premature approvals, confirmation and stale terms/permissions. Add frontend helper tests in `apps/web/tests/tasks.test.ts` and a browser acceptance script.
2. Add `apps/api/src/kawteam/tasks.py` for naming/targets, queue/terms and decisions. Update `main.py`, `projects.py`, `providers.py`, `workflow.py`, `repository.py`. Keep connected-email execution deferred; controlled liaison/confirmation explicitly demo-only.
3. Add additive scoped RPC migration `supabase/migrations/202610110006_task_conversations.sql`: transactional task start and revision-aware resulting-case updates. Inspect current schema before application; verify roles, idempotency and limits with local tests and an opt-in live QA project.
4. Add `apps/web/src/lib/tasks.ts`, typed decisions/queue fields. Modify chat surface so home picks projects and project picks tasks; no default general-thread continuation. Add project task list and detail components, replace project top tabs, route legacy cases appropriately. Update global approval counts/history to include task vendor checkpoints.
5. Style focused chat, task rows, secured/approval rows and dates with the existing teal/lime palette; inspect desktop/mobile. Avoid nested click controls and provide keyboard/role controls.
6. Run backend pytest/Ruff, frontend domain tests/lint/typecheck/build. Browser-test new task, resumed conversation/update, approval/rejection/confirmation, permissions, reload, old records and responsive layouts. Restore sample mutations and delete only labelled QA projects. Update README/checkpoint and workflow instructions.

Alternatives considered: keeping a project-wide thread with inferred tasks risks mixing requests; creating a task for every message breaks follow-up conversations. Chosen boundary is a new conversation, with subsequent messages continuing the selected task.

## Completion

All six implementation steps are complete, including the additional scoped legacy-history migration `202610110007_legacy_task_conversations.sql`. The connected Supabase project has all seven migrations. Verification passed: 43 frontend tests, 71 backend tests, lint/type checks, production build, read-only browser regressions, the full saved task browser flow and the opt-in database transaction checks. The original sample was restored and temporary QA projects removed. See [Task conversations checkpoint](../TASK_CONVERSATIONS_CHECKPOINT.md) for the final behavior, verification and deferred live-provider requirements.
