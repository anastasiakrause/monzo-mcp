"""MCP tools for Monzo API.

This module provides the registration functions for all Monzo MCP tools.
"""

from mcp.server.fastmcp import FastMCP

from .accounts import register_account_tools
from .analysis import register_analysis_tools
from .feed import register_feed_tools
from .pots import register_pot_tools
from .transactions import register_transaction_tools


def register_all_tools(mcp: FastMCP, get_client: callable) -> None:
    """Register all Monzo tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: A callable that returns the MonzoClient instance
    """
    register_account_tools(mcp, get_client)
    register_transaction_tools(mcp, get_client)
    register_analysis_tools(mcp, get_client)
    register_pot_tools(mcp, get_client)
    register_feed_tools(mcp, get_client)


__all__ = [
    "register_all_tools",
    "register_account_tools",
    "register_transaction_tools",
    "register_analysis_tools",
    "register_pot_tools",
    "register_feed_tools",
]
