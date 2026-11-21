"""Hierarchy of legal norms (lower numeric value means higher rank)."""
RANK_LEVELS = {1: "Constitution", 2: "Law or ordinance", 3: "Decree", 4: "Order", 5: "Circular"}


def rank_conflict(text_a: dict, text_b: dict) -> dict:
    """Return the higher-ranked text; ties return text_a."""
    return text_a if text_a["rank_level"] <= text_b["rank_level"] else text_b

