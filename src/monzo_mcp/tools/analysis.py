"""Analysis-related MCP tools (subscriptions and frequent merchants)."""

import logging

from mcp.server.fastmcp import FastMCP

from ..analysis import (
    detect_frequent_merchants,
    detect_subscriptions,
    format_frequent_merchants,
    format_subscriptions,
)
from ..models import MonzoAPIError
from ..monzo_client import MonzoClient

logger = logging.getLogger("monzo-mcp")


def register_analysis_tools(mcp: FastMCP, get_client: callable) -> None:
    """Register analysis-related tools with the MCP server."""

    @mcp.tool()
    async def list_subscriptions(account_id: str) -> str:
        """Detect recurring payments and subscriptions.

        Analyzes your transaction history to identify recurring charges like
        streaming services, memberships, and other subscriptions.

        Args:
            account_id: The account ID (get this from get_accounts)

        Note: Only analyzes the last 90 days of transactions (API limit).
        Filters out charges under £1.00.
        """
        try:
            client: MonzoClient = get_client()
            # Fetch maximum transactions for better pattern detection
            transactions = await client.list_transactions(account_id, limit=100)

            if not transactions:
                return "No transactions found to analyze."

            subscriptions = detect_subscriptions(transactions)
            return format_subscriptions(subscriptions)
        except MonzoAPIError as e:
            return f"Error: {e.message}"
        except Exception as e:
            logger.exception("Error detecting subscriptions")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def list_frequent_merchants(account_id: str, min_transactions: int = 3) -> str:
        """Identify merchants you use frequently.

        Unlike subscriptions, this finds any merchant you've transacted with
        multiple times, regardless of timing or amount patterns. Useful for
        identifying regular spending habits like transport, coffee shops, etc.

        Args:
            account_id: The account ID (get this from get_accounts)
            min_transactions: Minimum transactions to be considered frequent (default 3)

        Note: Only analyzes the last 90 days of transactions (API limit).
        """
        try:
            client: MonzoClient = get_client()
            transactions = await client.list_transactions(account_id, limit=100)

            if not transactions:
                return "No transactions found to analyze."

            merchants = detect_frequent_merchants(transactions, min_transactions)
            return format_frequent_merchants(merchants)
        except MonzoAPIError as e:
            return f"Error: {e.message}"
        except Exception as e:
            logger.exception("Error detecting frequent merchants")
            return f"Error: {str(e)}"
