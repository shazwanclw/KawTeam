# WorkBuddy integration: actual desktop setup and remaining execution

Updated 11 October 2026. The chosen approach is Gemini website chat plus WorkBuddy MCP execution. See [integration status](../INTEGRATION_STATUS.md) and [current specification](../CURRENT_PRODUCT_SPEC.md).

## What is configured

The user's desktop app signs in with Google. Actual UI: **Connectors -> MCP Server Management -> Add MCP**. The JSON editor identifies `%USERPROFILE%/.workbuddy-ai/mcp.json`; a KawTeam entry is present. The user reports the connection is okay. A local MCP client successfully launches the Python server, discovers kawteam_health and calls it. An independently inspected actual WorkBuddy request/result is still needed.

The user's supplied credit screen showed 2,350 total credits, including base and reward credits. Do not assume that balance is current, that one credit equals one task, or that credits grant hosted API access. Measure a small run before extrapolating.

## Configuration

The following matches this Windows workspace. Preserve other servers; merge the kawteam entry rather than replacing populated mcpServers. On another machine replace both absolute paths, or use `workbuddy/kawteam/mcp.example.json`.

```json
{
  "mcpServers": {
    "kawteam": {
      "command": "C:/Users/shazw/Documents/Taylor Hackathon/apps/api/.venv/Scripts/python.exe",
      "args": [
        "C:/Users/shazw/Documents/Taylor Hackathon/apps/api/src/kawteam/mcp/server.py"
      ]
    }
  }
}
```

Save, enable KawTeam and open a new conversation. Ask: **Call kawteam_health with request_id "workbuddy-connection-test" and show the result.** Verify matching request ID, status ok and the actual client tool event. Never paste backend secrets into chat.

## Direction matters

```text
WorkBuddy -> our KawTeam MCP server -> saved task/context/search/email tools
Website -> WorkBuddy agent run -> requires a separate verified trigger
```

Add MCP lets WorkBuddy consume tools. It does not expose a WorkBuddy agent API to KawTeam, automate a desktop run from the website or spend desktop credits through Gemini. WorkBuddy model settings accept external model credentials, not necessarily inbound agent credentials.

Tencent documents Enterprise Managed Agents/ADK APIs, but the user's personal Google-login account has not established access. Do not assume entitlement or require a paid upgrade. No unofficial personal-account proxy or undocumented endpoint is authorised. See [official Enterprise API documentation](https://cloud.tencent.com/document/api/1831/138581).

## Implemented tools and limits

Eight tools are implemented in `apps/api/src/kawteam/mcp/server.py`: `kawteam_health`, `kawteam_projects`, `kawteam_task`, `kawteam_research`, `kawteam_email_status`, `kawteam_send_enquiry`, `kawteam_sync_replies`, `kawteam_interpret_quote`. Reconnect/restart the KawTeam MCP entry to refresh discovery. They use shared backend services directly; FastAPI need not be running, but server environment, Supabase and provider access must work.

List projects, read a saved task, then use its current backendRevision. Research saves bounded public candidates without verifying contacts or quotes. Only organiser-registered contacts can receive non-binding enquiries. Limits: four per supplier, 60 per task, 20 saved threads per sync and 30 messages per thread. Sends reserve an intent before Gmail; uncertain outcomes cannot be automatically repeated. No arbitrary inbox read, final approve/reject, payment or booking tool exists. The interpretation tool validates quoted evidence and exact terms; Secured additionally requires current human approval and a later matching reply. Real commercial acceptance still needs testing.

The real stdio test verifies discovery and health calls. A live local MCP client also read Supabase projects and the QA task containing one actual Gmail receipt and zero human supplier decisions. This is service/tool evidence, not actual WorkBuddy orchestration. [Workflow skill](../../workbuddy/kawteam/skills/kawteam-procurement/SKILL.md) loading into the actual client still needs verification.

## Remaining build and acceptance

1. Capture actual WorkBuddy health call evidence.
2. Exercise the implemented project/task/context/search/email tools in the actual desktop client.
3. Complete contact enrichment, final-quote interpretation and follow-up orchestration.
4. Keep human final approval outside agent tools; require current quotes and separate supplier confirmation.
5. Verify retries, budget/round limits, concurrent runs, waits and resume.
6. Resolve supported website start/resume. Desktop initiation must be labelled if automatic triggering is unavailable.
7. Show useful matching task UI/server/client tool evidence beyond health.

Local laptop execution requires that runtime to stay available. A Vercel frontend deployment does not host it. Gmail is locally authorised with a saved controlled-test receipt; actual reply/deployed checks remain. Drive credentials are still missing. [Official MCP guide](https://www.codebuddy.ai/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide), [model guide](https://www.workbuddy.ai/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Model).
