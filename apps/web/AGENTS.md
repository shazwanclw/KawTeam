<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes â€” APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` â€” verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## KawTeam project rules (updated 11 October 2026)

Read [current product specification](../../docs/CURRENT_PRODUCT_SPEC.md), [integration status](../../docs/INTEGRATION_STATUS.md) and the [workspace README](../../README.md) before changes. These supersede older layout/provider assumptions.

Keep chat-first home, project/task pickers, below-chat All Task / Recent Activity, with Failsafe only when unresolved issues exist, task Secured/Approval/dates, sidebar-only Overview links and Connections. Support task-scoped chat reference attachments and the Drive-link icon; keep the hamburger stationary without duplicate close buttons. No login, preferences trigger, top project tabs or Subprojects. Human final approval is separate from supplier confirmation. Preserve shared-demo role/revision/ownership checks and legacy records.

Gemini/Tavily live checks pass. Gmail is locally authorised with a controlled test receipt, and nine WorkBuddy MCP tools are implemented. Real supplier quote/confirmation acceptance, actual WorkBuddy orchestration/website trigger, Drive access, Google Calendar OAuth/sync and deployment remain pending. Never infer completed outcomes from configured keys or health, or expose secrets in docs/client/logs.

After implementation, run checks appropriate to the change using README commands. Documentation-only changes require link/content/format verification, not an unnecessary application rebuild. Keep this project section outside the generated Next.js block.
