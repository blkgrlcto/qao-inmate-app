"""Database module."""

__all__ = ["get_db"]


def __getattr__(name: str):
    """Lazy import to avoid loading session (async engine) when only Base is needed."""
    if name == "get_db":
        from app.db.session import get_db
        return get_db
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
