"""Pytest configuration and fixtures for Monzo MCP tests."""

import pytest


@pytest.fixture
def sample_transaction() -> dict:
    """Return a sample transaction for testing."""
    return {
        "id": "tx_test123",
        "amount": -1500,  # -£15.00
        "currency": "GBP",
        "created": "2026-01-14T10:30:45.123Z",
        "description": "NETFLIX",
        "category": "entertainment",
        "merchant": {
            "name": "Netflix",
            "category": "entertainment",
            "address": {
                "short_formatted": "Online",
            },
        },
    }


@pytest.fixture
def sample_account() -> dict:
    """Return a sample account for testing."""
    return {
        "id": "acc_test123",
        "type": "uk_retail",
        "description": "user_test",
        "closed": False,
    }


@pytest.fixture
def sample_balance() -> dict:
    """Return a sample balance response for testing."""
    return {
        "balance": 123456,  # £1,234.56
        "total_balance": 150000,  # £1,500.00
        "currency": "GBP",
        "spend_today": -4520,  # -£45.20
    }
