"""Pot-related MCP tools."""

import logging

from mcp.server.fastmcp import FastMCP

from ..models import MonzoAPIError
from ..monzo_client import MonzoClient
from ..utils import format_money

logger = logging.getLogger("monzo-mcp")


def register_pot_tools(mcp: FastMCP, get_client: callable) -> None:
    """Register pot-related tools with the MCP server."""

    @mcp.tool()
    async def list_pots(account_id: str) -> str:
        """List all savings pots for a Monzo account.

        Args:
            account_id: The account ID (get this from get_accounts)

        Note: This is read-only. Moving money to/from pots is not supported.
        """
        try:
            client: MonzoClient = get_client()
            pots = await client.list_pots(account_id)

            if not pots:
                return "No pots found."

            result = []
            for pot in pots:
                if pot.get("deleted"):
                    continue

                name = pot.get("name", "Unnamed")
                balance = format_money(pot.get("balance", 0), pot.get("currency", "GBP"))
                goal = pot.get("goal_amount")
                locked = pot.get("locked", False)

                line = f"- {name}: {balance}"
                if goal:
                    goal_formatted = format_money(goal, pot.get("currency", "GBP"))
                    line += f" / {goal_formatted} goal"
                if locked:
                    line += " (LOCKED)"

                result.append(line)
                result.append(f"  ID: {pot.get('id', 'unknown')}")

            return "Pots:\n" + "\n".join(result)
        except MonzoAPIError as e:
            return f"Error: {e.message}"
        except Exception as e:
            logger.exception("Error listing pots")
            return f"Error: {str(e)}"
