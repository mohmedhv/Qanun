"""P5 week 3: answers from the knowledge graph (no LLM call)."""
from eval.citation_verifier import verify_graph_citations
from src.rag.graph_answer import answer, article_from_question, events_for, load_graph


def _pairs(result):
    return [(e["text_id"], e["provision"], e["relation"]) for e in result["events"]]


def test_article_73_modified_by_loi_91_29_art_2():
    result = answer("Quel texte a modifié l'article 73 ?")
    assert _pairs(result) == [("loi-91-29", "Art. 2", "modifies")]
    event = result["events"][0]
    assert event["date_signed"] == "1991-12-21"
    assert "F1991068" in event["source_url"]
    assert event["version_check"]["status"] == "confirmed"
    assert result["current"]["in_force"] is True
    assert result["citations_valid"] is True
    assert result["confidence"] == "élevé"


def test_article_87_bis_added_then_repealed_by_loi_14_10_art_90():
    result = answer("Qui a abrogé l’article 87 bis ?")
    assert _pairs(result) == [("decret-legislatif-94-03", "Art. 1er", "adds"),
                              ("loi-14-10", "Art. 90", "repeals")]
    assert all(e["version_check"]["status"] == "confirmed" for e in result["events"])
    assert result["current"] == {"tracked": True, "in_force": False, "last_status": "repealed"}
    assert result["citations_valid"] is True


def test_article_73_4_reports_version_mismatch():
    # The graph says loi 91-29 added 73-4; P3's only version starts with ord. 96-21.
    result = answer("Quel texte a modifié l'article 73‑4 ?")  # non-breaking hyphen
    checks = {e["text_id"]: e["version_check"]["status"] for e in result["events"]}
    assert checks == {"loi-91-29": "mismatch", "ordonnance-96-21": "confirmed"}
    assert result["confidence"] == "faible"


def test_article_22_repealed_and_not_tracked_by_p3():
    result = answer("Quel texte a abrogé l'article 22 ?")
    assert _pairs(result) == [("ordonnance-97-03", "Art. 8", "repeals")]
    assert result["events"][0]["version_check"]["status"] == "not_tracked"
    assert result["confidence"] == "moyen"


def test_unknown_article_or_no_article_is_refused():
    for question in ("Quel texte a modifié l'article 999 ?", "Quel texte a modifié la loi ?"):
        result = answer(question)
        assert result["refused"] is True
        assert "Je ne trouve pas de règle dans le corpus." in result["text"]


def test_question_parsing():
    assert article_from_question("Quel texte a modifié l'article 73 ?") == "73"
    assert article_from_question("Qui a abrogé l’article 87 bis ?") == "87 bis"
    assert article_from_question("article 73‑4") == "73-4"
    assert article_from_question("Bonjour") is None


def test_answer_uses_only_text_to_article_edges():
    assert all(e["relation"] in {"modifies", "repeals", "adds"} for e in events_for("12"))


def test_graph_citation_verifier():
    edges, _ = load_graph()
    real = [{"text_id": "loi-91-29", "article": "73", "relation": "modifies", "provision": "Art. 2"}]
    fake = [{"text_id": "loi-91-29", "article": "87 bis", "relation": "repeals", "provision": "Art. 2"}]
    assert verify_graph_citations(real, list(edges)) is True
    assert verify_graph_citations(fake, list(edges)) is False
    assert verify_graph_citations([], list(edges)) is False
