"""P3 graph vocabulary and endpoint contract used by the graph builder.

Endpoint directions follow the shared graph contract. This contract describes
permitted graph structure, not independent legal verification. For example,
the wording introduced in inventory row 9 (article 87 bis) cites article 87.
Decree 15-59 implements article 87, the target of row 54. See docs/ontology.md
for sources.
"""
ENTITIES = ("Text", "Article", "Version", "Concept")
RELATIONS = ("belongs_to", "modifies", "repeals", "applies", "adds", "cites", "mentions")

ACTION_RELATIONS = {
    "modify": "modifies", "complete": "modifies",
    "term_substitution": "modifies", "insert": "adds", "repeal": "repeals",
}

# Ownership follows Ikram's newly published graph contract (a621355).
ENDPOINTS = {
    "belongs_to": (("Article", "Text"), ("Version", "Article")),
    "modifies": (("Text", "Article"), ("Text", "Text"), ("Article", "Article")),
    "adds": (("Text", "Article"), ("Article", "Article")),
    "repeals": (("Text", "Article"), ("Article", "Article")),
    "applies": (("Text", "Article"),),
    "cites": (("Text", "Text"), ("Article", "Text"), ("Article", "Article")),
    "mentions": (("Article", "Concept"), ("Version", "Concept")),
}


def relation_for_action(action):
    """Map an inventory operation; unknown operations raise KeyError."""
    return ACTION_RELATIONS[action]


def validate_edge(source_entity, relation, target_entity):
    """Return endpoint errors without asserting legal/source verification."""
    if relation not in ENDPOINTS:
        return [f"Unknown relation: {relation}"]
    if (source_entity, target_entity) not in ENDPOINTS[relation]:
        return [f"Unsupported endpoints: {source_entity} -> {target_entity} for {relation}"]
    return []

