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
WorkBuddy -> our KawTeam MCP server -> task tools (not implemented yet)
Website -> WorkBuddy agent run -> requires a separate verified trigger
```

Add MCP lets WorkBuddy consume tools. It does not expose a WorkBuddy agent API to KawTeam, automate a desktop run from the website or spend desktop credits through Gemini. WorkBuddy model settings accept external model credentials, not necessarily inbound agent credentials.

Tencent documents Enterprise Managed Agents/ADK APIs, but the user's personal Google-login account has not established access. Do not assume entitlement or require a paid upgrade. No unofficial personal-account proxy or undocumented endpoint is authorised. See [official Enterprise API documentation](https://cloud.tencent.com/document/api/1831/138581).

## Existing tool and limits

`apps/api/src/kawteam/mcp/server.py` exposes only `kawteam_health(request_id)`. It returns a structured health result with product/status/capabilities and a historical phase label. It does not access Supabase/project context, research, Gmail, website chats or final decisions. Its Python process does not need the web server for a health call.

The MCP SDK test in `apps/api/tests/test_mcp_stdio.py` is genuine local transport evidence, not proof of WorkBuddy planning/orchestration or email execution. Current guidance lives in [the workflow skill](../../workbuddy/kawteam/skills/kawteam-procurement/SKILL.md); installation/loading into the actual client is not verified.

## Remaining build and acceptance

1. Capture actual WorkBuddy health call evidence.
2. Implement scoped project/task/context and checkpoint tools using shared backend services.
3. Add discovery and non-binding liaison/reply tools after contact/email providers exist.
4. Keep human final approval outside agent tools; require current quotes and separate supplier confirmation.
5. Verify retries, budget/round limits, concurrent runs, waits and resume.
6. Resolve supported website start/resume. Desktop initiation must be labelled if automatic triggering is unavailable.
7. Show useful matching task UI/server/client tool evidence beyond health.

Local laptop execution requires that runtime to stay available. A Vercel frontend deployment does not host it. Gmail and Drive credentials/providers remain separate requirements. [Official MCP guide](https://www.codebuddy.ai/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide), [model guide](https://www.workbuddy.ai/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Model).
