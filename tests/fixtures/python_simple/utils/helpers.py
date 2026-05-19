from typing import Any

def sanitize_input(value: str) -> str:
    """Sanitize user input."""
    return value.strip()

def format_currency(amount: float, currency: str = "usd") -> str:
    """Format an amount as currency string."""
    symbols = {"usd": "$", "eur": "€", "gbp": "£"}
    return f"{symbols.get(currency, currency)}{amount:.2f}"
