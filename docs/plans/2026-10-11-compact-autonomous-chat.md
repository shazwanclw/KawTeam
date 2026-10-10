# Compact layout and autonomous sparse briefs

Goal: implement the user's requested compact pages, autonomous chat and project Failsafe tab.

Design: remove topbar brand/breadcrumb/profile clutter and page eyebrow copy. Retain a small navigation toggle and move profile switching into the sidebar. Reduce project/title/composer spacing. Keep the current palette and typography.

Sparse sourcing briefs retain unknown quantity, budget and destination as null. A missing deadline defaults to fourteen days from today and is recorded as an assumption. Research and non-binding enquiries can proceed with known facts only; enquiry templates omit unknown fields and request pricing tiers when quantity is unknown. Unknown user requirements cannot qualify a binding supplier decision.

Failsafes are task-scoped durable attention records with stable IDs, reasons, required fields, status and resolution history. Missing quantity raises an attention record without blocking enquiry work. Optional initial destination/date do not cause interrogation. Genuine ambiguity or exhausted automated/provider steps escalates; simple supplier waits do not. The project tab counts unresolved records, displays a focused reply input and resumes the affected task through its existing chat when context is supplied.

The composer shows the submitted user message immediately and an accessible animated Thinking state. Saved outreach progress comes from actual provider receipts and task state; no fabricated vendor counts or claimed sends. Remove repetitive approval disclaimers from ordinary replies, while retaining final approval in the decision UI and enforcement.

Implementation sequence:
1. Write regression tests for missing quantity/destination/deadline, grounded enquiries, approval eligibility and failsafe resolution. Implement sparse validation/defaults and lifecycle.
2. Add project failsafe UI and compact shell/chat spacing, preserving keyboard navigation and sidebar state.
3. Add progress messages from actual outreach milestones and pending chat display. Check retries do not duplicate transcript entries.
4. Run backend/frontend checks and isolated browser tests for layout, thinking state, failsafe counts/resolution. Do not send real supplier emails during development.
5. Update the current product/integration documentation with the changed behaviour and verified limits.

## Implementation and verification

Implemented compact global navigation, removed page/chatter kickers, tightened project spacing, added Thinking feedback and project Failsafe resolution. Sparse briefs preserve unknown quantity/destination, record provisional 14-day dates, and generate provisional enquiries without blocking research. Current-scope email/reply milestones update saved task conversations. Final fit and organiser selection remain enforced. Review fixes preserve saved facts against model nulls, distinguish total/per-item ceilings, accept explicit collection arrangements, and resolve recovered provider failures.

Validation: 145 backend tests and Ruff passed; 45 frontend tests, TypeScript and ESLint passed; isolated compact browser checks passed for navigation persistence, spacing, three tabs, Failsafe submission, optimistic prompt/Thinking, transcript deduplication and mobile overflow. Browser gateway calls were intercepted and no real supplier email was sent. Background outreach still uses foreground polling while KawTeam is open.
