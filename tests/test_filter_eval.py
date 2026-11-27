"""filter_eval must stop loudly when a labeled id matches no text (never skip silently)."""
import csv
import json

from eval import filter_eval


def _write_labels(path, ids):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text_id", "title", "first_300_chars", "relevant"])
        writer.writeheader()
        for i, text_id in enumerate(ids):
            writer.writerow({"text_id": text_id, "title": "t", "first_300_chars": "x",
                             "relevant": "yes" if i % 2 == 0 else "no"})


def test_unknown_labeled_ids_fail_loudly(tmp_path, monkeypatch, capsys):
    labels, texts, report = tmp_path / "labels.csv", tmp_path / "texts", tmp_path / "report.md"
    texts.mkdir()
    _write_labels(labels, [f"DEC-EXE-26-{n}" for n in range(20)])  # old uppercase ids: no such text
    monkeypatch.setattr(filter_eval, "LABELS", labels)
    monkeypatch.setattr(filter_eval, "TEXT_DIR", texts)
    monkeypatch.setattr(filter_eval, "REPORT", report)
    monkeypatch.setattr("sys.argv", ["filter_eval"])
    assert filter_eval.main() == 1
    assert "20 labeled ids not found among the texts" in capsys.readouterr().out
    assert not report.exists()


def test_matching_ids_produce_the_report(tmp_path, monkeypatch):
    labels, texts, report = tmp_path / "labels.csv", tmp_path / "texts", tmp_path / "report.md"
    texts.mkdir()
    ids = [f"decret-executif-26-{n}" for n in range(20)]
    for i, text_id in enumerate(ids):
        relevant = i % 2 == 0
        title = "relatif au contrat de travail et au salaire" if relevant else "portant nomination d'un directeur"
        (texts / f"{text_id}.json").write_text(json.dumps(
            {"text_id": text_id, "type": "decret", "title": title, "raw_text": title}), encoding="utf-8")
    _write_labels(labels, ids)
    monkeypatch.setattr(filter_eval, "LABELS", labels)
    monkeypatch.setattr(filter_eval, "TEXT_DIR", texts)
    monkeypatch.setattr(filter_eval, "REPORT", report)
    monkeypatch.setattr("sys.argv", ["filter_eval"])
    assert filter_eval.main() == 0
    assert "Labeled texts: 20" in report.read_text(encoding="utf-8")
