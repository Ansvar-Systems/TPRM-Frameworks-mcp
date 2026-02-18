"""Streamable HTTP transport for TPRM Frameworks MCP server.

Enables the server to run as an HTTP endpoint (for Vercel, Docker, or standalone)
in addition to the default stdio transport.
"""

import contextlib
import json
import time
from datetime import datetime, UTC

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .config import config
from .logging_config import setup_logging

logger = setup_logging()

# Lazy-import to share tool definitions with stdio server
from .server import health_check, SERVER_VERSION


async def health_endpoint(request: Request) -> JSONResponse:
    """Health endpoint returning structured JSON status.

    Returns:
        JSON with status (ok/degraded/stale), version, uptime, framework count,
        tool count, and data freshness timestamp.
    """
    try:
        health = await health_check()
        status = "ok" if health["status"] == "healthy" else "degraded"

        return JSONResponse({
            "status": status,
            "version": SERVER_VERSION,
            "timestamp": datetime.now(UTC).isoformat(),
            "frameworks_loaded": health.get("frameworks", {}).get("loaded", 0),
            "tools_available": health.get("tools_available", 0),
            "storage": health.get("storage", {}).get("status", "unknown"),
            "memory_mb": health.get("memory", {}).get("rss_mb", 0),
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            {"status": "error", "error": str(e)},
            status_code=503,
        )


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    """Manage server lifecycle."""
    logger.info("TPRM Frameworks MCP HTTP server starting", extra={"version": SERVER_VERSION})
    yield
    logger.info("TPRM Frameworks MCP HTTP server shutting down")


def create_http_app() -> Starlette:
    """Create the Starlette ASGI application with MCP and health routes."""
    app = Starlette(
        routes=[
            Route("/health", health_endpoint, methods=["GET"]),
        ],
        lifespan=lifespan,
    )
    return app


def run_http_server(host: str = "0.0.0.0", port: int | None = None):
    """Run the HTTP server with uvicorn."""
    port = port or config.server.port
    app = create_http_app()
    logger.info(f"Starting HTTP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
