"""Entry point for the TPRM Frameworks MCP server (MCPB bundle)."""

import asyncio

from tprm_frameworks_mcp.server import main

asyncio.run(main())
