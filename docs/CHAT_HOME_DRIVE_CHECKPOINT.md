# Chat home and Drive context checkpoint

Reconciled 11 October 2026. Chat-first/Drive functionality persists, but the later [task conversation checkpoint](TASK_CONVERSATIONS_CHECKPOINT.md) replaces old project tabs and draft-centric approvals. [Current specification](CURRENT_PRODUCT_SPEC.md) is the product source of truth.

## Current flow

Home is chat with a project picker. A new conversation creates a task; without selection it resolves/creates a project from the prompt. New project asks name and optional Drive link; sidebar Projects plus is the permanent creation control, with an empty-picker fallback. No upload UI.

Sidebar Chat, Overview links, Projects search/list and Connections. Open navigation persists until closed. Projects open directly to New Task/existing-task chat. All Task / Recent Activity sit below the composer. Task detail has ranked human Approval, separately confirmed Secured suppliers and dates. Repeat supplier requests keep identity and require fresh terms.

## Drive adapter and memory

`apps/api/src/kawteam/drive.py` validates HTTPS Drive/Docs IDs and uses fixed Google hosts. Supported credentials are a public-content Drive API key or service-account JSON with a private folder explicitly shared as reader. Neither is configured. Saved links show awaiting_access and do not claim ingestion.

Docs/Slides export as text; Sheets as XLSX; PDF/DOCX/XLSX/TXT/MD/CSV extraction is bounded. No OCR. Limits: 3 MB/file, 80,000 extracted characters/file, 20 current documents/project, folder depth 3, 10 folders, 10 listing pages, 45 requests and 45-second budget.

Stable document identities replace versions. Complete sync archives removed files; partial reads/failures preserve readable previous memory and its correct source attribution. Facts recompute from active documents. Project memory dialog shows source/status/current documents; refresh is manual. No Google user OAuth, automatic background sync or unrestricted Drive access.

Seven migrations now include the earlier drive_snapshot RPC plus task/legacy changes. Snapshot writes are atomic, credential/ownership/role/revision guarded. Archived documents are excluded from retrieval. Documents remain untrusted reference context, not authority to send or select suppliers.

## Conversation and evidence

Deterministic parsing and Gemini can use project facts; essential missing terms are asked conversationally. Explicit user updates override memory and invalidate current quotes only when requirements change. Task history remains separate from other tasks. Source citations must point to actual project excerpts.

Backend/frontend tests and injected Drive transports pass; real Google folder access still needs credentials. Current test counts are 100 backend/43 frontend. Production build and browser/database flows were previously verified; read-only e2e now targets task-layout-browser, not the old chat-home script.

## Latest provider status

Gmail is locally authorised; one controlled test send has a saved provider receipt, and saved-thread reading works. Eight scoped WorkBuddy MCP tools exist and real local project/task reads pass. Actual desktop orchestration, website trigger, automated contact enrichment, live supplier quote/confirmation acceptance, Drive access and public deployment remain pending. See [integration status](INTEGRATION_STATUS.md).
