"""Tests for utility functions."""

from datetime import datetime

import pytest

from monzo_mcp.utils import format_money, get_merchant_name, parse_date


class TestFormatMoney:
    """Tests for format_money function."""

    def test_format_gbp_positive(self) -> None:
        """Test formatting positive GBP amount."""
        assert format_money(1234, "GBP") == "£12.34"

    def test_format_gbp_negative(self) -> None:
        """Test formatting negative GBP amount."""
        assert format_money(-1500, "GBP") == "£-15.00"

    def test_format_gbp_zero(self) -> None:
        """Test formatting zero amount."""
        assert format_money(0, "GBP") == "£0.00"

    def test_format_other_currency(self) -> None:
        """Test formatting non-GBP currency."""
        assert format_money(1000, "USD") == "10.00 USD"

    def test_format_default_currency(self) -> None:
        """Test that GBP is the default currency."""
        assert format_money(500) == "£5.00"


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_with_milliseconds(self) -> None:
        """Test parsing ISO date with milliseconds."""
        result = parse_date("2026-01-14T10:30:45.123Z")
        assert result == datetime(2026, 1, 14, 10, 30, 45)

    def test_parse_without_milliseconds(self) -> None:
        """Test parsing ISO date without milliseconds."""
        result = parse_date("2026-01-14T10:30:45Z")
        assert result == datetime(2026, 1, 14, 10, 30, 45)

    def test_parse_invalid_format(self) -> None:
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError):
            parse_date("not-a-date")


class TestGetMerchantName:
    """Tests for get_merchant_name function."""

    def test_with_merchant_dict(self, sample_transaction: dict) -> None:
        """Test extracting name from merchant dict."""
        assert get_merchant_name(sample_transaction) == "Netflix"

    def test_without_merchant(self) -> None:
        """Test fallback to description when no merchant."""
        tx = {"description": "Bank Transfer", "merchant": None}
        assert get_merchant_name(tx) == "Bank Transfer"

    def test_merchant_without_name(self) -> None:
        """Test fallback when merchant dict has no name."""
        tx = {"description": "Test", "merchant": {"category": "general"}}
        assert get_merchant_name(tx) == "Test"

    def test_empty_transaction(self) -> None:
        """Test handling of empty transaction."""
        assert get_merchant_name({}) == "Unknown"
