"""Transaction-related MCP tools."""

import logging

from mcp.server.fastmcp import FastMCP

from ..models import MonzoAPIError
from ..monzo_client import MonzoClient
from ..utils import format_money

logger = logging.getLogger("monzo-mcp")


def register_transaction_tools(mcp: FastMCP, get_client: callable) -> None:
    """Register transaction-related tools with the MCP server."""

    @mcp.tool()
    async def list_transactions(
        account_id: str,
        limit: int = 20,
    ) -> str:
        """List recent transactions for a Monzo account.

        Args:
            account_id: The account ID (get this from get_accounts)
            limit: Number of transactions to return (max 100, default 20)

        Note: Due to Strong Customer Authentication, only 90 days of history
        is available via the API after 5 minutes of authentication.
        """
        try:
            client: MonzoClient = get_client()
            transactions = await client.list_transactions(account_id, limit=min(limit, 100))

            if not transactions:
                return "No transactions found."

            result = []
            for txn in transactions:
                amount = format_money(txn.get("amount", 0), txn.get("currency", "GBP"))
                created = txn.get("created", "")[:10]  # Just the date
                description = txn.get("description", "Unknown")

                # Get merchant name if available
                merchant = txn.get("merchant")
                if merchant and isinstance(merchant, dict):
                    name = merchant.get("name", description)
                else:
                    name = description

                # Categorize
                category = txn.get("category", "general")

                result.append(f"- {created}: {amount} - {name} [{category}]")
                result.append(f"  ID: {txn.get('id', 'unknown')}")

            return f"Recent transactions:\n" + "\n".join(result)
        except MonzoAPIError as e:
            return f"Error: {e.message}"
        except Exception as e:
            logger.exception("Error listing transactions")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def get_transaction(transaction_id: str) -> str:
        """Get detailed information about a specific transaction.

        Args:
            transaction_id: The transaction ID (get this from list_transactions)
        """
        try:
            client: MonzoClient = get_client()
            txn = await client.get_transaction(transaction_id)

            if not txn:
                return "Transaction not found."

            amount = format_money(txn.get("amount", 0), txn.get("currency", "GBP"))
            created = txn.get("created", "Unknown")
            description = txn.get("description", "Unknown")
            category = txn.get("category", "general")
            notes = txn.get("notes", "")

            result = [
                f"Transaction: {txn.get('id', 'unknown')}",
                f"Amount: {amount}",
                f"Date: {created}",
                f"Description: {description}",
                f"Category: {category}",
            ]

            if notes:
                result.append(f"Notes: {notes}")

            # Merchant details
            merchant = txn.get("merchant")
            if merchant and isinstance(merchant, dict):
                result.append(f"\nMerchant: {merchant.get('name', 'Unknown')}")
                if merchant.get("address"):
                    addr = merchant["address"]
                    result.append(
                        f"Address: {addr.get('short_formatted', addr.get('address', ''))}"
                    )
                if merchant.get("category"):
                    result.append(f"Merchant category: {merchant['category']}")

            return "\n".join(result)
        except MonzoAPIError as e:
            return f"Error: {e.message}"
        except Exception as e:
            logger.exception("Error getting transaction")
            return f"Error: {str(e)}"
