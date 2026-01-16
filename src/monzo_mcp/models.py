"""Data models used throughout the Monzo MCP server."""

from dataclasses import dataclass
from datetime import datetime


class MonzoAPIError(Exception):
    """Raised when Monzo API returns an error."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Monzo API error ({status_code}): {message}")


@dataclass
class Subscription:
    """Represents a detected subscription."""

    merchant: str
    amount: int  # in pence
    currency: str
    frequency: str  # "weekly", "monthly", "annual"
    last_date: datetime
    next_date: datetime
    transaction_count: int


@dataclass
class FrequentMerchant:
    """Represents a frequently used merchant."""

    merchant: str
    transaction_count: int
    total_spent: int  # in pence
    average_amount: int  # in pence
    currency: str
    first_date: datetime
    last_date: datetime
    categories: list[str]
