import pytest
from src.search.legal_query_expansion import expand_queries, expanded_query_text

def test_original_query_is_first_and_negation_is_preserved():
    q = "Un salarié ne peut pas renoncer à ses droits."
    variants = expand_queries(q)
    assert variants[0] == q
    assert "ne peut pas" in variants[0]

def test_empty_query_rejected():
    with pytest.raises(ValueError):
        expand_queries(" ")

def test_variant_count_is_bounded():
    result = expand_queries("Les travailleurs salariés et la relation salariée.", max_variants=2)
    assert len(result) <= 3

def test_cdd_expands_to_full_expression():
    result = expand_queries("Dans quels cas peut-on utiliser un CDD ?")
    assert any("contrat à durée déterminée" in x.lower() for x in result[1:])

def test_no_article_ids_are_injected():
    result = expand_queries("Qui est considéré comme salarié ?")
    joined = " ".join(result).lower()
    assert "loi-90-11-art-" not in joined
    assert "article 2" not in joined

def test_bm25_query_keeps_original():
    q = "Quels travailleurs salariés sont concernés ?"
    assert q in expanded_query_text(q)
