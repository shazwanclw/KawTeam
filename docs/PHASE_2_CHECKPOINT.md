# Phase 2 checkpoint: frontend delivered and evolved

Updated 11 October 2026. This file is a milestone summary, not an instruction to rebuild the original casebook. Current scope: [product specification](CURRENT_PRODUCT_SPEC.md), [task checkpoint](TASK_CONVERSATIONS_CHECKPOINT.md), [integration status](INTEGRATION_STATUS.md).

## Current frontend

Chat-first home, project picker, optional Drive project creation, task-based project chat/history, All Task / Recent Activity below the composer, task Secured/Approval/dates, sidebar-only Overview links, milestone tables, red-dot calendar and Connections. Existing teal/lime/Jakarta/shadcn design remains. No login, upload/intake form, assistant settings, generic metric dashboard or top project/subproject tabs.

Profile switcher supports shared-demo Organiser/Teammate/Observer; server checks now enforce role permissions. API mode persists to Supabase, not just browser-local fixtures. Earlier `/demo`/casebook helpers remain secondary compatibility surfaces, with fictional supplier data labelled.

## Verification and later delivery

Latest suites: 43 frontend tests, 100 backend tests, type/lint checks. Production build and saved browser flows passed before docs refresh, including task continuation/edit, approval/confirmation, roles and responsive widths. Phases 3-5 persistence/decision foundations now exist; Gemini/Tavily are live-tested.

Gmail is locally authorised; one controlled test send has a saved provider receipt, and saved-thread reading works. Eight scoped WorkBuddy MCP tools exist and real local project/task reads pass. Actual desktop orchestration, website trigger, automated contact enrichment, live supplier quote/confirmation acceptance, Drive access and public deployment remain pending. See [integration status](INTEGRATION_STATUS.md).
