# KawTeam frontend

Updated 11 October 2026. Read the [workspace README](../../README.md), [current product specification](../../docs/CURRENT_PRODUCT_SPEC.md) and [integration status](../../docs/INTEGRATION_STATUS.md).

## Run

From this directory: `npm ci` on a fresh checkout, then `npm run dev`. Open http://localhost:3000. API mode also needs FastAPI running on port 8000; root README has the backend command. Configure `.env.local` from `.env.example`; use server-only API/gateway values and do not expose provider credentials.

## Current UI

Main chat selects projects. Projects open directly to New Task/existing-task chat; selecting a task expands saved history. All Task / Recent Activity / Failsafe sit below chat. Task detail has Secured / ranked Approval and Upcoming events, with approval badges and separate supplier confirmation. Sidebar has Chat, Overview links, Projects plus/search and Connections. The composer has Drive-link/file-reference icons and removable attachment chips. The stationary hamburger toggles the sidebar. No login, assistant preferences or top project/subproject tabs.

Keep teal/lime tokens, shadcn primitives, responsive stacking and keyboard access. Gmail send/read and eight WorkBuddy tools are implemented; full orchestration/trigger, live supplier quote/confirmation acceptance, Drive access and deployment remain pending. Do not fabricate active work, quotes or sent messages.

## Verify

`npm test`, `npm run typecheck`, `npm run lint`, `npm run build`. Latest frontend test count: 43. Stop a web server before building the same directory. With web/API running, `npm run test:e2e` is the read-only task layout check; `node tests/refinement-browser.mjs` covers chat/overview/navigation/calendar. The root README documents opt-in saved-data checks and cleanup. Screenshots in test-results are ignored.

Read local Next.js documentation as required by [AGENTS.md](AGENTS.md) before code changes. A docs-only refresh does not require a new production build.


Local development uses Webpack by default (`npm run dev`) because fresh browser sessions stalled before hydration under the installed Turbopack runtime. The current saved T-shirt task renders successfully with Webpack. Run one frontend server on port 3000; do not share a build directory between simultaneous dev/start servers.
