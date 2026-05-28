from app.services.locking import acquire_lock, release_lock


def test_acquire_then_release():
    acquire_lock("it_test_1", 3)
    res = release_lock("it_test_1")
    assert res["released"]
