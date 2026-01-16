"""Feed-related MCP tools."""

import logging

from mcp.server.fastmcp import FastMCP

from ..models import MonzoAPIError
from ..monzo_client import MonzoClient

logger = logging.getLogger("monzo-mcp")


def register_feed_tools(mcp: FastMCP, get_client: callable) -> None:
    """Register feed-related tools with the MCP server."""

    @mcp.tool()
    async def create_feed_item(
        account_id: str,
        title: str,
        body: str,
    ) -> str:
        """Send a notification to the user's Monzo app.

        This creates a feed item that appears in the user's Monzo app feed.
        Useful for sending reminders or custom notifications.

        Args:
            account_id: The account ID (get this from get_accounts)
            title: The notification title (keep it short)
            body: The notification body text
        """
        try:
            client: MonzoClient = get_client()
            await client.create_feed_item(account_id, title, body)
            return f"Feed item created successfully: '{title}'"
        except MonzoAPIError as e:
            return f"Error: {e.message}"
        except Exception as e:
            logger.exception("Error creating feed item")
            return f"Error: {str(e)}"
