# KawTeam frontend

Updated 11 October 2026. Read the [workspace README](../../README.md), [current product specification](../../docs/CURRENT_PRODUCT_SPEC.md) and [integration status](../../docs/INTEGRATION_STATUS.md).

## Run

From this directory: `npm ci` on a fresh checkout, then `npm run dev`. Open http://localhost:3000. API mode also needs FastAPI running on port 8000; root README has the backend command. Configure `.env.local` from `.env.example`; use server-only API/gateway values and do not expose provider credentials.

## Current UI

Main chat selects projects. Projects open directly to New Task/existing-task chat; selecting a task expands saved history. All Task / Recent Activity sit below chat. Task detail has Secured / ranked Approval and Upcoming events, with approval badges and separate supplier confirmation. Sidebar has Chat, Overview links, Projects plus/search and Connections. No login, upload UI, assistant preferences or top project/subproject tabs.

Use existing teal/lime tokens and shadcn primitives; preserve responsive stacking and keyboard access. Gemini/Tavily work through the backend. Drive credentials, Gmail and WorkBuddy execution/website trigger remain pending; do not show fabricated active work or sent emails.

## Verify

`npm test`, `npm run typecheck`, `npm run lint`, `npm run build`. Latest frontend test count: 43. Stop a web server before building the same directory. With web/API running, `npm run test:e2e` is the read-only task layout check; `node tests/refinement-browser.mjs` covers chat/overview/navigation/calendar. The root README documents opt-in saved-data checks and cleanup. Screenshots in test-results are ignored.

Read local Next.js documentation as required by [AGENTS.md](AGENTS.md) before code changes. A docs-only refresh does not require a new production build.
