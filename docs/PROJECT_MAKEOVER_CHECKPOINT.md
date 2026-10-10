# Project makeover checkpoint: current reconciliation

Updated 11 October 2026. The original overview-first/upload/optional-subproject makeover has been superseded. This file retains implementation history without prescribing the old UI. Current rules: [product specification](CURRENT_PRODUCT_SPEC.md), [task checkpoint](TASK_CONVERSATIONS_CHECKPOINT.md), [integration status](INTEGRATION_STATUS.md).

## What remains from the makeover

Teal/lime palette, local Jakarta typography, shadcn buttons/dialogs/dropdowns/calendar, responsive layouts, profile-based demo roles, Supabase project/task storage and compatible legacy routes. Shared project context with isolated task threads and repeat supplier identity remains useful.

## What changed

Home now starts with chat. No Files/upload UI or assistant settings button. Projects start directly at New Task/existing-task chat, not a general thread with top tabs. All Task / Recent Activity are below chat; task detail contains Secured/Approval and Upcoming events. Subprojects are replaced by task vocabulary. Overview sublinks live only in the sidebar; Connections means saved supplier relationships.

New project takes name plus optional Drive link. Creation uses Projects plus and empty-picker fallback. Repeat orders skip discovery when supplier identity is explicit but require new terms. No arbitrary three-supplier outreach cap. Final human approval follows liaison; only a matching supplier confirmation creates secured. Legacy exact-draft approvals are not the primary experience.

## Persistence and integration

The original project_tasks_chat migration is retained; seven total migrations now cover Drive snapshots, atomic task starts, case edits and legacy threads. Existing user records are preserved. Role/revision/ownership/retry protections remain, with deliberate shared-demo profile switching and no private authentication claim.

Gmail is locally authorised; one controlled test send has a saved provider receipt, and saved-thread reading works. Eight scoped WorkBuddy MCP tools exist and real local project/task reads pass. Actual desktop orchestration, website trigger, automated contact enrichment, live supplier quote/confirmation acceptance, Drive access and public deployment remain pending. See [integration status](INTEGRATION_STATUS.md).
