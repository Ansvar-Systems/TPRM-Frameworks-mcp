"""Streamable HTTP transport for TPRM Frameworks MCP server.

Enables the server to run as an HTTP endpoint (for Docker or standalone)
in addition to the default stdio transport. Uses a raw ASGI app with
StreamableHTTPSessionManager to handle MCP protocol requests at /mcp.
"""

import asyncio
import json
from datetime import datetime, UTC

import uvicorn
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from .config import config
from .logging_config import setup_logging
from .server import create_mcp_server, health_check, SERVER_VERSION

logger = setup_logging()


async def _run_streamable_http(host: str, port: int) -> None:
    """Run MCP server using Streamable HTTP transport."""
    mcp_server = create_mcp_server()
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        json_response=True,
    )

    async def asgi_app(scope, receive, send):
        """Raw ASGI app with /mcp and /health routing."""
        if scope["type"] == "lifespan":
            msg = await receive()
            if msg["type"] == "lifespan.startup":
                scope["state"] = scope.get("state", {})
                scope["state"]["_sm_cm"] = session_manager.run()
                await scope["state"]["_sm_cm"].__aenter__()
                logger.info(
                    "TPRM Frameworks MCP HTTP server started",
                    extra={"version": SERVER_VERSION, "host": host, "port": port},
                )
                await send({"type": "lifespan.startup.complete"})
            msg = await receive()
            if msg["type"] == "lifespan.shutdown":
                await scope["state"]["_sm_cm"].__aexit__(None, None, None)
                logger.info("TPRM Frameworks MCP HTTP server shut down")
                await send({"type": "lifespan.shutdown.complete"})
            return

        if scope["type"] != "http":
            return

        path = scope.get("path", "")

        if path == "/health":
            try:
                health = await health_check()
                status = "ok" if health["status"] == "healthy" else "degraded"
                body = json.dumps({
                    "status": status,
                    "version": SERVER_VERSION,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "frameworks_loaded": health.get("frameworks", {}).get("loaded", 0),
                    "tools_available": health.get("tools_available", 0),
                }).encode()
            except Exception as e:
                body = json.dumps({"status": "error", "error": str(e)}).encode()
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"application/json"]],
            })
            await send({"type": "http.response.body", "body": body})
            return

        if path in ("/mcp", "/mcp/"):
            await session_manager.handle_request(scope, receive, send)
            return

        body = json.dumps({"error": "not found"}).encode()
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({"type": "http.response.body", "body": body})

    uvi_config = uvicorn.Config(asgi_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(uvi_config)
    await server.serve()


def run_http_server(host: str = "0.0.0.0", port: int | None = None):
    """Run the HTTP server with uvicorn."""
    port = port or config.server.port
    logger.info(f"Starting HTTP server on {host}:{port} with MCP routes at /mcp")
    asyncio.run(_run_streamable_http(host, port))
