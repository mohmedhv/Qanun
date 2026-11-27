from src.search.graph_candidate_retrieval import (
    detect_relation,
    extract_signed_date,
    graph_candidates,
)


def test_detect_relations():
    assert detect_relation("Quel texte abroge l'art. 72 ?") == "repeals"
    assert detect_relation("Quel texte ajoute l'art. 56 bis ?") == "adds"
    assert detect_relation("Quel texte modifie l'art. 87 ?") == "modifies"
    assert detect_relation("Quel texte applique l'art. 4 ?") == "applies"


def test_extract_signed_date():
    question = "Quel texte juridique, signe le 2005-03-26, applique l'art. 4 ?"
    assert extract_signed_date(question) == "2005-03-26"


def test_graph_candidate_with_date():
    question = (
        "Quel texte juridique, signe le 2005-03-26, "
        "applique l'art. 4 de la loi 90-11 ?"
    )

    candidates = graph_candidates(question)

    assert len(candidates) == 1
    assert candidates[0]["text_id"] == "decret-executif-05-102"


def test_no_relation_returns_empty():
    candidates = graph_candidates(
        "Que prevoit l'article 4 de la loi 90-11 ?"
    )
    assert candidates == []


def test_no_article_returns_empty():
    candidates = graph_candidates(
        "Quel texte juridique modifie la loi 90-11 ?"
    )
    assert candidates == []
