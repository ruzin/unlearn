from app.services.accounts import open_account
from app.services.points import award_points


def test_award_lifts_tier():
    open_account("usr_x")
    result = award_points("usr_x", 60_000, "test")
    assert result["tier"] in {"gold", "platinum"}
