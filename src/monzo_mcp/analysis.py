"""Transaction analysis logic for detecting subscriptions and frequent merchants."""

from datetime import timedelta
from typing import Any

from .constants import FREQUENCY_ORDER, FREQUENCY_PATTERNS, MIN_AMOUNT_PENCE
from .models import FrequentMerchant, Subscription
from .utils import format_money, get_merchant_name, parse_date


def group_by_merchant(
    transactions: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Group transactions by merchant name, filtering by minimum amount."""
    groups: dict[str, list[dict[str, Any]]] = {}

    for tx in transactions:
        # Skip income (positive amounts) and small charges
        amount = tx.get("amount", 0)
        if amount >= 0 or abs(amount) < MIN_AMOUNT_PENCE:
            continue

        merchant = get_merchant_name(tx)

        if merchant not in groups:
            groups[merchant] = []
        groups[merchant].append(tx)

    return groups


def detect_frequency(dates: list) -> tuple[str | None, float]:
    """
    Detect if dates follow a regular pattern.

    Returns:
        Tuple of (frequency_name, average_interval_days) or (None, 0) if no pattern
    """
    if len(dates) < 2:
        return None, 0

    # Sort dates chronologically
    sorted_dates = sorted(dates)

    # Calculate intervals between consecutive transactions
    intervals = [
        (sorted_dates[i + 1] - sorted_dates[i]).days
        for i in range(len(sorted_dates) - 1)
    ]

    avg_interval = sum(intervals) / len(intervals)

    # Check each frequency pattern
    for freq_name, pattern in FREQUENCY_PATTERNS.items():
        min_occurrences = pattern["min_occurrences"]
        if len(dates) < min_occurrences:
            continue

        if pattern["min_days"] <= avg_interval <= pattern["max_days"]:
            return freq_name, avg_interval

    return None, avg_interval


def amounts_are_consistent(amounts: list[int], tolerance: float = 0.1) -> bool:
    """Check if amounts are consistent within a tolerance (default 10%)."""
    if not amounts:
        return False

    avg_amount = sum(amounts) / len(amounts)
    if avg_amount == 0:
        return False

    for amount in amounts:
        if abs(amount - avg_amount) / abs(avg_amount) > tolerance:
            return False

    return True


def predict_next_date(last_date, frequency: str, avg_interval: float):
    """Predict the next payment date based on frequency."""
    if frequency == "weekly":
        return last_date + timedelta(days=7)
    elif frequency == "monthly":
        # Use actual interval for better prediction
        return last_date + timedelta(days=round(avg_interval))
    elif frequency == "annual":
        return last_date + timedelta(days=365)
    else:
        return last_date + timedelta(days=round(avg_interval))


def detect_subscriptions(transactions: list[dict[str, Any]]) -> list[Subscription]:
    """
    Analyze transactions to detect recurring subscriptions.

    Args:
        transactions: List of transaction dicts from Monzo API

    Returns:
        List of detected Subscription objects
    """
    subscriptions = []
    grouped = group_by_merchant(transactions)

    for merchant, txs in grouped.items():
        if len(txs) < 2:
            continue

        # Extract dates and amounts
        dates = []
        amounts = []
        currency = "GBP"

        for tx in txs:
            try:
                dates.append(parse_date(tx.get("created", "")))
                amounts.append(abs(tx.get("amount", 0)))
                currency = tx.get("currency", "GBP")
            except (ValueError, KeyError):
                continue

        if len(dates) < 2:
            continue

        # Check if this looks like a subscription
        frequency, avg_interval = detect_frequency(dates)

        if frequency and amounts_are_consistent(amounts):
            avg_amount = int(sum(amounts) / len(amounts))
            last_date = max(dates)
            next_date = predict_next_date(last_date, frequency, avg_interval)

            subscriptions.append(
                Subscription(
                    merchant=merchant,
                    amount=avg_amount,
                    currency=currency,
                    frequency=frequency,
                    last_date=last_date,
                    next_date=next_date,
                    transaction_count=len(dates),
                )
            )

    # Sort by frequency (monthly first), then by amount
    subscriptions.sort(key=lambda s: (FREQUENCY_ORDER.get(s.frequency, 99), -s.amount))

    return subscriptions


def detect_frequent_merchants(
    transactions: list[dict[str, Any]], min_transactions: int = 3
) -> list[FrequentMerchant]:
    """
    Identify merchants with multiple transactions.

    Unlike subscription detection, this doesn't require consistent intervals
    or amounts - it simply finds merchants you transact with frequently.

    Args:
        transactions: List of transaction dicts from Monzo API
        min_transactions: Minimum number of transactions to be considered frequent

    Returns:
        List of FrequentMerchant objects sorted by transaction count (descending)
    """
    # Group transactions by merchant
    merchant_data: dict[str, dict[str, Any]] = {}

    for tx in transactions:
        # Skip income (positive amounts)
        amount = tx.get("amount", 0)
        if amount >= 0:
            continue

        merchant = get_merchant_name(tx)
        abs_amount = abs(amount)

        if merchant not in merchant_data:
            merchant_data[merchant] = {
                "transactions": [],
                "total_spent": 0,
                "currency": tx.get("currency", "GBP"),
                "categories": set(),
            }

        try:
            date = parse_date(tx.get("created", ""))
            merchant_data[merchant]["transactions"].append(date)
            merchant_data[merchant]["total_spent"] += abs_amount
            category = tx.get("category", "general")
            merchant_data[merchant]["categories"].add(category)
        except (ValueError, KeyError):
            continue

    # Build FrequentMerchant objects for merchants with enough transactions
    frequent_merchants = []
    for merchant, data in merchant_data.items():
        tx_count = len(data["transactions"])
        if tx_count < min_transactions:
            continue

        dates = sorted(data["transactions"])
        frequent_merchants.append(
            FrequentMerchant(
                merchant=merchant,
                transaction_count=tx_count,
                total_spent=data["total_spent"],
                average_amount=data["total_spent"] // tx_count,
                currency=data["currency"],
                first_date=dates[0],
                last_date=dates[-1],
                categories=list(data["categories"]),
            )
        )

    # Sort by transaction count (descending), then by total spent (descending)
    frequent_merchants.sort(key=lambda m: (-m.transaction_count, -m.total_spent))

    return frequent_merchants


def format_subscriptions(subscriptions: list[Subscription]) -> str:
    """Format detected subscriptions for display."""
    if not subscriptions:
        return "No subscriptions detected.\n\nTip: Subscriptions are detected from recurring payments with consistent amounts over 90 days."

    result = ["Detected Subscriptions:\n"]

    # Group by frequency
    by_frequency: dict[str, list[Subscription]] = {}
    for sub in subscriptions:
        if sub.frequency not in by_frequency:
            by_frequency[sub.frequency] = []
        by_frequency[sub.frequency].append(sub)

    # Calculate monthly total
    monthly_total = 0.0

    # Display in order: monthly, weekly, annual
    for freq in ["monthly", "weekly", "annual"]:
        if freq not in by_frequency:
            continue

        freq_label = freq.capitalize()
        result.append(f"{freq_label}:")

        for sub in by_frequency[freq]:
            amount_str = format_money(sub.amount, sub.currency)
            next_date_str = sub.next_date.strftime("%b %d")

            # Build frequency suffix
            if freq == "weekly":
                suffix = "/week"
                monthly_total += sub.amount * 4.33  # ~4.33 weeks per month
            elif freq == "monthly":
                suffix = "/month"
                monthly_total += sub.amount
            else:  # annual
                suffix = "/year"
                monthly_total += sub.amount / 12

            result.append(f"  - {sub.merchant}: {amount_str}{suffix} (next: ~{next_date_str})")

        result.append("")  # Blank line between sections

    # Add monthly total estimate
    monthly_total_str = format_money(int(monthly_total))
    result.append(f"Estimated monthly total: {monthly_total_str}")

    return "\n".join(result)


def format_frequent_merchants(merchants: list[FrequentMerchant]) -> str:
    """Format frequent merchants for display."""
    if not merchants:
        return "No frequent merchants found.\n\nTip: Merchants need at least 3 transactions to appear here."

    result = ["Frequent Merchants:\n"]
    total_all = 0

    for merchant in merchants:
        total_str = format_money(merchant.total_spent, merchant.currency)
        avg_str = format_money(merchant.average_amount, merchant.currency)
        first_date_str = merchant.first_date.strftime("%b %d")
        last_date_str = merchant.last_date.strftime("%b %d")

        result.append(f"{merchant.merchant} ({merchant.transaction_count} transactions)")
        result.append(f"  Total: {total_str} | Avg: {avg_str}")
        result.append(f"  Period: {first_date_str} - {last_date_str}")
        result.append("")

        total_all += merchant.total_spent

    total_all_str = format_money(total_all, "GBP")
    result.append(f"Total across frequent merchants: {total_all_str}")

    return "\n".join(result)
