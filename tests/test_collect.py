import json

import pytest

from src.collect import ocr, split_issue, relevance
from eval.filter_eval import confusion


def test_parse_pages():
    assert ocr.parse_pages("3", 8) == [3]
    assert ocr.parse_pages("1-3,8", 8) == [1, 2, 3, 8]
    with pytest.raises(SystemExit):
        ocr.parse_pages("9", 8)


def test_split_issue_synthetic(tmp_path, monkeypatch):
    ocr_dir = tmp_path / "ocr"
    text_dir = tmp_path / "texts"
    ocr_dir.mkdir()
    (ocr_dir / "SYNTH.txt").write_text(
        "=== page 1 (text-layer) ===\n"
        "LOI n° 90-11 correspondant au 21 avril 1990 portant relations de travail ........ 2\n"
        "=== page 2 (ocr-psm6) ===\n"
        "JOURNAL OFFICIEL DE LA REPUBLIQUE ALGERIENNE N° 17 25 Avril 1990\n"
        "LOI n° 90-11 du 21 avril 1990 portant relations de travail\n"
        "Le Président de la République,\n| Vu la loi relative au travail |\n"
        "Loi n° 90-12 portant un renvoi cité dans le corps.\n"
        "l'article 30 de la loi n° 90-11 relative aux relations de travail.\n"
        "Art. 2. Ce marqueur ne commence pas un nouveau texte.\n"
        "DECRET EXECUTIF n° 26-10 du 21 avril 1990 portant contrat de travail\n"
        "Vu les textes en vigueur\n"
        "ARRETE du 21 avril 1990 fixant salaire\n"
        "Article 1er. Le salaire est fixé. |\n"
        "DECISION n° 3 du 21 avril 1990 portant avis\n"
        "Le ministre décide.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(split_issue, "OCR_DIR", ocr_dir)
    monkeypatch.setattr(split_issue, "TEXT_DIR", text_dir)
    monkeypatch.setattr(split_issue, "REGISTRY", tmp_path / "registry.csv")
    split_issue.REGISTRY.write_text(
        "url,file,year,number\nhttps://example.test,SYNTH.pdf,1990,017\n", encoding="utf-8"
    )
    records = split_issue.write_issue("SYNTH")
    assert [record["type"] for record in records] == ["loi", "decret_executif", "arrete", "autre"]
    assert records[0]["text_id"] == "loi-90-11"
    assert records[0]["date_signed"] == "1990-04-21"
    assert records[0]["jo_number"] == "17"
    assert records[0]["source_url"] == "https://example.test"
    assert records[0]["ocr_used"] is True
    assert "........" not in records[0]["raw_text"]
    assert "JOURNAL OFFICIEL" not in records[0]["raw_text"]
    assert "| Vu" not in records[0]["raw_text"]
    assert records[2]["number"] is None
    assert records[2]["rank_level"] == 4
    assert records[3]["rank_level"] == 5
    assert set(records[0]) == {
        "text_id", "type", "number", "title", "date_signed", "jo_number", "jo_date",
        "language", "rank_level", "source_url", "pdf_path", "ocr_used", "raw_text",
    }
    before = {p.name: p.read_bytes() for p in text_dir.glob("*.json")}
    split_issue.write_issue("SYNTH")
    after = {p.name: p.read_bytes() for p in text_dir.glob("*.json")}
    assert before == after


def test_scoring_and_exclusions():
    value, terms = relevance.score("Contrat de travail", "Les contrats de travail et salaires")
    assert value >= 3
    assert "contrat de travail" in terms
    assert "salaire" in terms
    assert relevance.reason_for({"type": "autre", "title": "travail"}, 5, 3) == (False, "type_autre")
    assert relevance.reason_for({"type": "arrete", "title": "Portant nomination"}, 5, 3)[0] is False
    assert relevance.reason_for({"type": "arrete", "title": "Texte"}, 2, 3) == (False, "below_threshold")


def test_confusion_counts():
    assert confusion([(True, True), (False, True), (True, False), (False, False)]) == (1, 1, 1, 1)
