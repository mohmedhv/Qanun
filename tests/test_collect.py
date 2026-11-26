import json
import re

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
    assert [record["type"] for record in records] == ["loi", "decret", "arrete", "autre"]
    assert [record["text_id"] for record in records] == [
        "loi-90-11", "decret-executif-26-10", "arrete-1990-04-21-1", "autre-3",
    ]
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
    # Contract: text_id is lowercase and starts with a full-word prefix.
    allowed = ("loi", "ordonnance", "decret-presidentiel", "decret-executif", "arrete", "circulaire", "autre")
    for record in records:
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", record["text_id"])
        assert record["text_id"].startswith(tuple(p + "-" for p in allowed))


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


def test_mixed_case_headers_are_detected():
    # Real Journal officiel lines are capitalised ("Décret présidentiel n° ..."), not all upper case.
    assert split_issue.is_header("Décret présidentiel n° 26-239 du 14 Moharram 1448 correspondant au 29 juin 2026 portant transfert", 2)
    assert split_issue.is_header("Loi n° 90-11 du 21 avril 1990 relative aux relations de travail.", 2)
    # A lowercase "décret" inside a sentence is a reference, not a header.
    assert split_issue.is_header("décret exécutif n° 91-306 du 24 août 1991 fixant la liste des communes", 2) is None


def test_number_with_punctuation_gives_clean_slug(tmp_path, monkeypatch):
    ocr_dir, text_dir = tmp_path / "ocr", tmp_path / "texts"
    ocr_dir.mkdir()
    (ocr_dir / "S2.txt").write_text(
        "=== page 2 (text-layer) ===\n"
        "Décision n° 04/D.C.C/CC/26 du 11 Safar 1448 correspondant au 26 juillet 2026 relative au contrôle\n"
        "Le Conseil constitutionnel décide.\n", encoding="utf-8")
    monkeypatch.setattr(split_issue, "OCR_DIR", ocr_dir)
    monkeypatch.setattr(split_issue, "TEXT_DIR", text_dir)
    monkeypatch.setattr(split_issue, "REGISTRY", tmp_path / "registry.csv")
    split_issue.REGISTRY.write_text("url,file,year,number\nhttps://example.test,S2.pdf,2026,054\n", encoding="utf-8")
    records = split_issue.write_issue("S2")
    assert [r["text_id"] for r in records] == ["autre-04-d-c-c-cc-26"]
