import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_health_is_discovered_and_called_over_real_mcp_transport():
    async def probe():
        server = StdioServerParameters(
            command=sys.executable,
            args=[str(Path(__file__).parents[1] / "src/kawteam/mcp/server.py")],
        )
        async with (
            stdio_client(server) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            tools = await session.list_tools()
            assert "kawteam_health" in [tool.name for tool in tools.tools]
            names = {tool.name for tool in tools.tools}
            assert {
                "kawteam_projects",
                "kawteam_task",
                "kawteam_research",
                "kawteam_email_status",
                "kawteam_send_enquiry",
                "kawteam_sync_replies",
                "kawteam_interpret_quote",
            }.issubset(names)
            assert not any("approve" in name or "reject" in name for name in names)
            result = await session.call_tool("kawteam_health", {"request_id": "stdio-phase-zero"})
            assert not result.is_error
            assert result.structured_content["request_id"] == "stdio-phase-zero"

    anyio.run(probe)
