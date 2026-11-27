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


# --- Week 3: refusals, non-breaking hyphen, real quotes, articles named in context ---
from eval.citation_verifier import check_citations, extract_citations

ART_73_4 = {"number": "73-4", "text": (
    "Si le licenciement d’un travailleur survient en violation des procédures légales et/ou "
    "conventionnelles obligatoires, le tribunal saisi annule la décision de licenciement. "
    "Si le licenciement d’un travailleur survient en violation des dispositions de l’article 73 "
    "ci-dessus, il est présumé abusif.")}
ART_73 = {"number": "73", "text": "Le licenciement à caractère disciplinaire intervient dans les cas de fautes graves."}
ART_12_BIS = {"number": "12 bis", "text": (
    "L’inspecteur du travail s’assure que le contrat de travail à durée déterminée est conclu "
    "pour l’un des cas expressément cités par l’article 12 de la présente loi.")}


def test_correct_refusal_without_citation_is_valid():
    assert verify_citations("(a) Je ne trouve pas de règle dans le corpus.", RETRIEVED) is True


def test_refusal_with_invented_article_fails():
    answer = "Je ne trouve pas de règle dans le corpus. Voir toutefois l'Article 99."
    assert verify_citations(answer, RETRIEVED) is False


def test_non_breaking_hyphen_is_read():
    assert extract_citations("Selon l’Article 73‑4 (U+2011) et l’Art. 73–4") == ["73-4"]
    assert verify_citations("Voir l’Article 73‑4.", [ART_73_4]) is True


def test_exact_quote_passes():
    answer = "Article 73 : « Le licenciement à caractère disciplinaire intervient dans les cas de fautes graves. »"
    assert verify_citations(answer, [ART_73]) is True


def test_quote_with_ellipsis_and_formatting_passes():
    answer = ("Article 73-4 : « Si le licenciement d'un travailleur survient en violation des procédures "
              "légales… le tribunal saisi annule la décision de licenciement »")
    assert verify_citations(answer, [ART_73_4]) is True


def test_altered_quote_fails():
    # Joins two paragraphs and changes the meaning (seen in the RAG run, Q08).
    answer = ("Article 73-4 : « Si le licenciement d’un travailleur survient en violation des procédures "
              "légales, il est présumé abusif et donne droit à douze mois de salaire. »")
    result = check_citations(answer, [ART_73_4])
    assert result["valid"] is False
    assert result["quotes_missing"][0]["attached_to"] == "73-4"


def test_quote_attached_to_wrong_article_fails():
    answer = "Article 73 : « il est présumé abusif si le licenciement d’un travailleur survient en violation »"
    assert verify_citations(answer, [ART_73, ART_73_4]) is False


def test_article_named_inside_real_quote_is_not_flagged():
    answer = ("Article 12 bis : « L’inspecteur du travail s’assure que le contrat de travail à durée "
              "déterminée est conclu pour l’un des cas expressément cités par l’article 12 de la présente loi. »")
    result = check_citations(answer, [ART_12_BIS])
    assert result["cited"] == ["12 bis"]
    assert result["valid"] is True


def test_article_named_in_context_is_reported_not_invented():
    answer = "Le CDD n'est possible que dans les cas de l'Article 12 (voir Article 12 bis)."
    result = check_citations(answer, [ART_12_BIS])
    assert result["named_in_context"] == ["12"]
    assert result["hallucinated"] == []
    assert result["valid"] is True
