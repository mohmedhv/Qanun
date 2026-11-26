"""Tests for the P5 citation verifier (eval/citation_verifier.py)."""
from eval.citation_verifier import verify_citations

# What P4's search() might return for "Un contrat de travail peut-il être oral ?"
RETRIEVED = [
    {"number": "8", "text": "La relation de travail prend naissance par le contrat écrit ou non écrit."},
    {"number": "10", "text": "La preuve du contrat peut être faite par tout moyen."},
    {"number": "11", "text": "Le contrat oral est présumé à durée indéterminée."},
    {"number": "13", "text": "Conditions du temps partiel."},
    {"number": "63", "text": "Modification du contrat."},
]


def test_valid_citations_pass():
    answer = "Selon Article 8 et Article 10, un contrat oral est valable."
    assert verify_citations(answer, RETRIEVED) is True


def test_article_not_retrieved_fails():
    answer = "Oui (Article 8). Voir aussi Article 99."
    assert verify_citations(answer, RETRIEVED) is False


def test_french_code_reference_fails():
    answer = "Oui (Article 8), mais le CDD doit être écrit (article L1242-1)."
    assert verify_citations(answer, RETRIEVED) is False


def test_answer_without_citation_fails():
    answer = "Oui, un contrat de travail peut être oral."
    assert verify_citations(answer, RETRIEVED) is False
