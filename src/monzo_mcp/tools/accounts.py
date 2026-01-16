"""Account-related MCP tools."""

import logging

from mcp.server.fastmcp import FastMCP

from ..models import MonzoAPIError
from ..monzo_client import MonzoClient
from ..utils import format_money

logger = logging.getLogger("monzo-mcp")


def register_account_tools(mcp: FastMCP, get_client: callable) -> None:
    """Register account-related tools with the MCP server."""

    @mcp.tool()
    async def get_accounts() -> str:
        """List all Monzo accounts for the authenticated user.

        Returns a list of accounts including current accounts, joint accounts, etc.
        Each account has an ID that you'll need for other operations.
        """
        try:
            client: MonzoClient = get_client()
            accounts = await client.list_accounts()

            if not accounts:
                return "No accounts found."

            result = []
            for acc in accounts:
                acc_type = acc.get("type", "unknown")
                acc_id = acc.get("id", "unknown")
                description = acc.get("description", "")
                closed = acc.get("closed", False)

                status = " (CLOSED)" if closed else ""
                result.append(f"- {acc_type}: {description}{status}")
                result.append(f"  ID: {acc_id}")

            return "Accounts:\n" + "\n".join(result)
        except MonzoAPIError as e:
            return f"Error: {e.message}"
        except Exception as e:
            logger.exception("Error listing accounts")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def get_balance(account_id: str) -> str:
        """Get the current balance for a Monzo account.

        Args:
            account_id: The account ID (get this from get_accounts)
        """
        try:
            client: MonzoClient = get_client()
            balance = await client.get_balance(account_id)

            current = format_money(balance.get("balance", 0), balance.get("currency", "GBP"))
            total = format_money(
                balance.get("total_balance", 0), balance.get("currency", "GBP")
            )
            spend_today = format_money(
                abs(balance.get("spend_today", 0)), balance.get("currency", "GBP")
            )

            return f"Balance: {current}\nTotal (inc. pots): {total}\nSpent today: {spend_today}"
        except MonzoAPIError as e:
            return f"Error: {e.message}"
        except Exception as e:
            logger.exception("Error getting balance")
            return f"Error: {str(e)}"
