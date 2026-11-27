"""Detect explicitly mentioned legal articles in questions."""

import re

ARTICLE_PATTERN = re.compile(
    r"\b(?:article|art\.)\s*(\d+(?:\s+bis(?:\s+\d+)?)?)",
    flags=re.IGNORECASE,
)


def extract_article_number(question):
    if not isinstance(question, str):
        raise TypeError("question must be a string")

    match = ARTICLE_PATTERN.search(question)

    if not match:
        return None

    return " ".join(match.group(1).lower().split())


def article_to_graph_node(question, text_id="loi-90-11"):
    """Return a graph node ID for an explicitly named article."""

    number = extract_article_number(question)

    if number is None:
        return None

    suffix = number.replace(" ", "-")

    return f"article:{text_id}-art-{suffix}"
