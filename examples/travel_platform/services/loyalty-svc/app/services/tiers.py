_TIERS = [
    ("platinum", 100_000),
    ("gold", 50_000),
    ("silver", 10_000),
    ("bronze", 0),
]


def recompute_tier(points: int) -> str:
    for name, threshold in _TIERS:
        if points >= threshold:
            return name
    return "bronze"
