"""Monzo MCP Server - Read-only access to Monzo banking data."""

import logging
import sys

from mcp.server.fastmcp import FastMCP

from .monzo_client import MonzoClient
from .tools import register_all_tools

# Configure logging to stderr (stdout breaks MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("monzo-mcp")

# Initialize FastMCP server
mcp = FastMCP("monzo")

# Lazy-initialized client (created on first tool call)
_client: MonzoClient | None = None


def get_client() -> MonzoClient:
    """Get or create the Monzo client."""
    global _client
    if _client is None:
        _client = MonzoClient()
    return _client


# Register all tools with the MCP server
register_all_tools(mcp, get_client)


def main():
    """Run the Monzo MCP server."""
    logger.info("Starting Monzo MCP server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
