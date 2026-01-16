"""Constants used throughout the Monzo MCP server."""

# Minimum amount in pence (£1.00) to filter out small recurring charges
MIN_AMOUNT_PENCE = 100

# Frequency detection thresholds for subscription detection
FREQUENCY_PATTERNS = {
    "weekly": {"min_days": 6, "max_days": 8, "min_occurrences": 3},
    "monthly": {"min_days": 27, "max_days": 34, "min_occurrences": 2},
    "annual": {"min_days": 360, "max_days": 370, "min_occurrences": 2},
}

# Frequency display order (for sorting subscriptions)
FREQUENCY_ORDER = {"monthly": 0, "weekly": 1, "annual": 2}
