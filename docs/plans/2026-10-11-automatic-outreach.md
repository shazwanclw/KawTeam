# Automatic task outreach implementation plan

Goal: finish the already authorised chat-to-enquiry workflow without requiring manual supplier contact entry. Human approval remains the final supplier decision.

Architecture: save a task-scoped automation request before executing actions. A protected bounded tick performs one supplier step, using the existing CAS repository, durable email intent and request hash. The website ticks while open; WorkBuddy can also execute a scoped tick. This is not a hosted WorkBuddy trigger or an always-running deployed worker.

1. Add failing tests for official-page contact extraction, irrelevant/directory sources, no invented addresses, observer rejection, duplicate ticks, stale task scope, real send receipts and incomplete-reply clarification.
2. Implement contact extraction through Tavily's fixed extract endpoint. Read only the discovered supplier's public website and common contact pages. Require an address literally present in returned source content and grounded service relevance from Gemini. Preserve source URL, excerpt and verification time. Missing or ambiguous contacts remain blocked with a reason.
3. Implement one-action task ticks: verify contact, send the initial non-binding enquiry, sync known supplier threads, interpret a current reply, or send a bounded clarification of missing terms. Never select suppliers or send an order. Persist progress and errors; uncertain sends remain blocked.
4. Queue automation only for new or edited supplier requests made through chat. Wire the protected tick endpoint into the existing visible-page refresh loop. Do not send anything merely by opening legacy tasks that have no automation authorisation.
5. Add a scoped WorkBuddy tick tool. Run backend tests/lint, frontend checks and a controlled integration test with a fake mailbox. Do not send a real supplier test enquiry from this development session.
6. Update current integration documentation with verified behaviour and remaining limitations. Public hosting and an unattended scheduler remain unverified.
