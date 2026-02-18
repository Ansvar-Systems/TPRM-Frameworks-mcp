"""Entry point for TPRM Frameworks MCP server."""

import argparse
import asyncio
import sys

from .server import main as stdio_main


def parse_args():
    parser = argparse.ArgumentParser(description="TPRM Frameworks MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="HTTP server port (default: from config or 8309)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="HTTP server host (default: 0.0.0.0)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.transport == "http":
        from .http_server import run_http_server
        run_http_server(host=args.host, port=args.port)
    else:
        asyncio.run(stdio_main())


if __name__ == "__main__":
    main()
