from dataclasses import dataclass


@dataclass
class LoyaltyAccount:
    user_id: str
    points: int
    tier: str
