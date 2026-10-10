# Presentation scenarios

These are **simulated records**, not evidence that KawTeam sent real enquiries, secured real suppliers or placed bookings. They use fictional businesses, reserved `.example` email domains, `sample: true` and `executionMode: demo`. The saved sent/received history is deliberately fabricated for the presentation. The history dialog labels demo messages; chat summaries also identify the simulation. Existing live Gmail credentials remain connected and unchanged.

The reproducible offline generator is [demo_scenarios.py](../apps/api/src/kawteam/demo_scenarios.py); its generated dataset is [presentation-demo.json](../apps/api/src/kawteam/presentation-demo.json). Neither generation nor replacement calls Gmail, Gemini, Tavily, Drive or WorkBuddy. The dataset has no authorised automation queues, email intents or provider receipts. Real liaison rejects these suppliers, so opening a seeded task cannot send the fabricated emails.

| Project | Demonstration | Saved state |
|---|---|---|
| Sunway Got Talent | Single-supplier T-shirt sourcing: 50 shirts, RM2,000 ceiling | Five complete negotiated offers. Threadcraft RM1,700 is ready for review; four alternatives wait. Rejecting it advances the next offer. Approval remains separate from confirmation. |
| Kampus Weekend Market | Ten exhibitor placements from twelve candidates, RM5,000 total support ceiling | Two secured, one approved awaiting confirmation, seven review slots and two alternatives. Each fictional exhibitor has enquiry, initial reply, negotiation and final terms. |
| Build Together Workshop | Reusing a known catering supplier instead of researching again | Original 50 lunch packs secured at RM780. Separate extra-20-pack task has fresh RM300 terms approved but not confirmed. Both tasks share the Green Table connection. |

There are exactly three projects, four task conversations, four supplier requests, three project briefing documents and 20 request-specific supplier entries representing 19 distinct businesses. Project memory includes event dates, locations, budgets and scope. Project headers intentionally omit the Sample badge; saved messages, records and history retain demo provenance. Completed milestones feed Recent Activity; saved deadlines, quote expiry and proposed delivery dates feed Calendar, grouped into at most three project summaries per day with full details available on click. Full supplier timelines feed the history dialogs and Connections. Secured records contain a matching supplier confirmation linked to an organiser approval and exact terms hash. An approval alone is never counted as secured.

The multi-exhibitor request follows the existing generic placement model: `selectionTarget=10` is the number of placements; request-level quantity is the scope agreed by each exhibitor, and individual support quotations are counted against the aggregate budget. This is not a specialist marketplace or sponsorship integration. Catering is a supported procurement example rather than a claim of a new specialist sponsorship workflow.

The narrow presentation compatibility helper [demo_scope.py](../apps/api/src/kawteam/demo_scope.py) allows matching sample quotations in these frozen scenarios. It requires the case sample marker, version 1, the vendor sample marker, matching `scenarioCaseId` and demo execution mode. The existing original tote fixture remains compatible. Live supplier guards and role permissions are unchanged. The controlled confirmation action explicitly creates a **demo** confirmation; it does not call a provider or create a real order.

## Replace application data safely

Replacement was executed and verified on 11 October 2026: the active workspace has three events, four cases, four threads and three documents; all 91 previous action-history rows were removed. The verified pre-reset backup is privately retained under `%LOCALAPPDATA%/KawTeam/private-backups/kawteam-before-presentation-demo-20261011.json`, outside the repository. The browser checks used a read-only exported snapshot with every gateway call mocked: eight pending approvals, nineteen relationships and all 88 simulated messages are represented correctly. The existing **Check demo confirmation** control also recognises matching versioned presentation fixtures, using the same explicit provenance criteria as the backend. Live suppliers never qualify for this control.

The user authorised removal of previous fake application records. Only the current workspace's `kawteam_records` and `kawteam_actions` are replaced. Workspace credentials, schema, OAuth tokens, API keys and configuration remain intact. Other workspaces are unaffected. The old records/actions must first be backed up to a private path outside the repository, such as `%LOCALAPPDATA%/KawTeam/private-backups/`, and must never be committed or exposed in presentation screenshots.

From the repository root:

```powershell
$env:PYTHONPATH='apps/api/src'
apps/api/.venv/Scripts/python.exe -m kawteam.demo_scenarios --output test-results/demo-backup-query.sql --workspace WORKSPACE_UUID --backup-query
```

Execute that read-only query with an authorised database administrator tool. Securely save its returned `payload` **and** `digest` outside the repository, then generate the replacement SQL with the actual returned digest:

```powershell
apps/api/.venv/Scripts/python.exe -m kawteam.demo_scenarios --output test-results/demo-replacement.sql --workspace WORKSPACE_UUID --expected-digest RETURNED_BACKUP_DIGEST
```

Execute the generated SQL through the same administrator connection. It locks the two application tables, rechecks the exact backup digest, deletes the scoped old records/actions and inserts all relationships in one transaction. If anything changed after the backup, it aborts before deletion; take a fresh backup. No temporary public reset RPC or permanent administrative credential is introduced. Stop application writers during replacement and verify the resulting snapshot before presenting. The initial replacement was executed as recorded above; future replacements must follow the same guarded procedure.

To regenerate the offline JSON:

```powershell
apps/api/.venv/Scripts/python.exe -m kawteam.demo_scenarios --output apps/api/src/kawteam/presentation-demo.json
```

Quotes are valid through 20 October 2026 for this hackathon presentation. A later presentation should deliberately refresh dates and regenerate all term hashes rather than bypass quote expiry. The generator does not automatically seed new installations or overwrite a running workspace.

## Browser verification

With the frontend dev server running, execute `node tests/presentation-demo-browser.mjs` from `apps/web`. It uses a read-only remote snapshot when exported into `test-results/premium/remote-demo-snapshot.json`, or generates the same offline scenarios through the existing API virtual environment. Every browser gateway call is mocked. It checks all three projects, four saved transcripts, approval/secured counts, full per-supplier histories, nineteen connections and separate confirmation controls without modifying Supabase or sending emails. `premium-visual-browser.mjs` captures visual baselines. Set `KAWTEAM_VISUAL_PHASE=reference` for the current styling capture; old strict before/after geometry checks predate the authorised card/calendar redesign. Screenshot artifacts remain Git-ignored.
