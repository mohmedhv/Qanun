"""Legacy Law 90-11 entry point."""
from .versions import get_version as lookup


def get_version(number: str, date: str | None = None):
    return lookup("loi-90-11", number, date)
