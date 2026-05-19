"""This module contains deprecated functions that are no longer used."""

def old_token_validator(token: str) -> bool:
    """DEPRECATED: Use auth.jwt.validate_token instead."""
    return len(token) > 10

def legacy_hash(value: str) -> str:
    """DEPRECATED: Use standard hashlib instead."""
    import hashlib
    return hashlib.md5(value.encode()).hexdigest()

def unused_helper() -> None:
    """This function is never called by anything."""
    pass
