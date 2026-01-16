"""Shared utility functions for the Monzo MCP server."""

from datetime import datetime
from typing import Any


def format_money(amount: int, currency: str = "GBP") -> str:
    """Format amount in pence/cents to human readable string."""
    if currency == "GBP":
        return f"£{amount / 100:.2f}"
    return f"{amount / 100:.2f} {currency}"


def parse_date(date_str: str) -> datetime:
    """Parse ISO 8601 date string to datetime."""
    # Handle both "2026-01-14T10:30:45.123Z" and "2026-01-14T10:30:45Z"
    if "." in date_str:
        date_str = date_str.split(".")[0] + "Z"
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")


def get_merchant_name(transaction: dict[str, Any]) -> str:
    """Extract merchant name from a transaction."""
    merchant = transaction.get("merchant")
    if merchant and isinstance(merchant, dict):
        return merchant.get("name", transaction.get("description", "Unknown"))
    return transaction.get("description", "Unknown")
