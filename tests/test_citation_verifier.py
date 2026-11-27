"""Tests of eval/citation_verifier.py (replaces the old root script test_verifier.py)."""
from eval.citation_verifier import verify_citations

# Same shape as the documents returned by src.search.search_service.search (key "number").
SEARCH_DOCS = [
    {"number": "8", "text": "La relation de travail prend naissance par le contrat écrit ou non écrit."},
    {"number": "10", "text": "La preuve du contrat peut être faite par tout moyen."},
    {"number": "11", "text": "Le contrat oral est présumé à durée indéterminée."},
]
# Older shape used by the first version of the script (key "article_number").
OLD_DOCS = [{"article_number": d["number"], "text": d["text"]} for d in SEARCH_DOCS]


def test_valid_citations_pass_with_both_shapes():
    answer = "Selon Article 8 et Article 10, un contrat oral est valable."
    assert verify_citations(answer, SEARCH_DOCS) is True
    assert verify_citations(answer, OLD_DOCS) is True


def test_invented_article_is_rejected():
    answer = "Oui (Article 8). Et aussi Article 99 qui n'existe pas."
    assert verify_citations(answer, SEARCH_DOCS) is False
    assert verify_citations(answer, OLD_DOCS) is False


def test_foreign_law_reference_is_rejected():
    answer = "Un CDD impose l'écrit (article L1242-1)."
    assert verify_citations(answer, SEARCH_DOCS) is False


def test_answer_without_citation_is_rejected():
    assert verify_citations("Oui, c'est possible.", SEARCH_DOCS) is False
