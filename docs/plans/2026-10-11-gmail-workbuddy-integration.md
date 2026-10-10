# Gmail and WorkBuddy execution integration

Continue the approved implementation plan. The user authorised one clearly labelled test enquiry from shazwan15122005@gmail.com to shazwan1512alt@gmail.com. No real supplier test sends are authorised.

1. Add tested Gmail MIME validation, fixed Google endpoints, token refresh and bounded thread reads. Request send/read-only permissions, never deletion. Store local credentials under ignored `.secrets`; allow server-only authorised-user JSON for deployment.
2. Add Desktop OAuth consent CLI. Check the selected sender before storing credentials. Launch consent for the supplied client. The user completes Google's account consent.
3. Add durable task email intents, verified contact registration, idempotent sends and saved-thread reply ingestion. Persist before sending; ambiguous outcomes block automatic resend. Match replies to supplier address. Preserve raw evidence without treating email instructions as application authority.
4. Expose task/context/search/email tools through WorkBuddy MCP. No human approval/rejection tool. Bind each action to saved workspace task and revision; no arbitrary inbox access.
5. Test authorised inboxes only after consent. Verify provider identity, receipt and saved thread; do not claim reply reading passed until an actual reply exists.
6. Update integration documentation. Website-to-WorkBuddy triggering, real Drive access and public deployment remain separate pending acceptance items.

Tests: provider request boundaries, injection rejection, missing/expired credentials, message correlation, no duplicate sends on retries, stale revisions, observer restrictions, real MCP tool discovery. Run backend suite and lint before reporting completion.


## Execution evidence and current sender

Google consent, identity, one labelled test send and one matching reply passed for the original account. The user then switched to `shazwanclw@gmail.com`; its consent, identity and running API status passed. No email was sent from the new account. Durable intents/messages now carry gmailSender; old threads cannot be read with a new account and old receipts cannot be reused across accounts.

Eight scoped MCP tools are implemented, including grounded quote/confirmation interpretation. Complete final quotes require supported source fragments and explicit amounts/dates. Secured requires a current human approval, exact matching terms and a later provider timestamp. These guards pass automated tests; actual commercial supplier acceptance remains unverified. The real test acknowledgement was correctly excluded from final quote approval by Gemini.

Current verification: 100 backend tests, 43 frontend tests, Ruff, TypeScript and ESLint. Actual WorkBuddy desktop orchestration/website trigger, automatic contact enrichment, Drive access and public deployment remain pending.
