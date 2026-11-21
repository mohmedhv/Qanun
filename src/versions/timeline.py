"""Article version lookup interface."""


def get_version(article_number: str, date: str | None = None):
    """Return the version in force at the given ISO date; current if date is None.

    TODO: implement a database-backed query using valid_from and valid_to.
    Returns None until the lookup is implemented.
    """
    return None

