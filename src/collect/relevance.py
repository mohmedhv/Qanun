"""Rule based relevance scores and label sheet generation."""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEXT_DIR = ROOT / "data" / "processed" / "texts"
FILTER_CSV = ROOT / "data" / "processed" / "filter_results.csv"
LABEL_CSV = ROOT / "eval" / "filter_labels.csv"
TERMS = ("travailleur", "employeur", "contrat de travail", "relations de travail", "travail", "salaire", "conge", "licenciement", "syndicat", "syndical", "greve")
EXCLUDED = ("portant nomination", "mettant fin aux fonctions", "portant delegation de signature")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()


def score(title: str, raw_text: str) -> tuple[int, list[str]]:
    title_norm, text_norm = normalize(title), normalize(raw_text)
    title_matched = {term for term in TERMS if re.search(rf"\b{re.escape(term)}s?\b", title_norm)}
    whole_matched = {term for term in TERMS if re.search(rf"\b{re.escape(term)}s?\b", text_norm)}
    matched = [term for term in TERMS if term in title_matched or term in whole_matched]
    return 3 * len(title_matched) + len(whole_matched), matched


def reason_for(record: dict, value: int, threshold: int) -> tuple[bool, str]:
    title = normalize(record.get("title", ""))
    if record.get("type") == "autre":
        return False, "type_autre"
    excluded = next((term for term in EXCLUDED if term in title), None)
    if excluded:
        return False, excluded
    if value < threshold:
        return False, "below_threshold"
    return True, "kept"


def records() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(TEXT_DIR.glob("*.json"))]


def run_filter(threshold: int) -> list[dict]:
    rows = []
    for record in records():
        value, matched = score(record.get("title", ""), record.get("raw_text", ""))
        kept, reason = reason_for(record, value, threshold)
        rows.append({"text_id": record["text_id"], "type": record.get("type"), "score": value,
                     "matched_terms": ";".join(matched), "kept": str(kept).lower(), "reason": reason})
    FILTER_CSV.parent.mkdir(parents=True, exist_ok=True)
    with FILTER_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text_id", "type", "score", "matched_terms", "kept", "reason"])
        writer.writeheader(); writer.writerows(rows)
    print(f"Wrote {FILTER_CSV}: {sum(r['kept']=='true' for r in rows)} kept, {sum(r['kept']=='false' for r in rows)} rejected")
    return rows


def make_label_sheet(count: int, seed: int) -> None:
    import random
    if LABEL_CSV.exists():
        print(f"Refusing to overwrite existing {LABEL_CSV}")
        return
    items = records()
    random.Random(seed).shuffle(items)
    LABEL_CSV.parent.mkdir(parents=True, exist_ok=True)
    with LABEL_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text_id", "title", "first_300_chars", "relevant"])
        writer.writeheader()
        for item in items[:count]:
            writer.writerow({"text_id": item["text_id"], "title": item.get("title", ""),
                             "first_300_chars": item.get("raw_text", "")[:300], "relevant": ""})
    print(f"Wrote {LABEL_CSV}: {min(count, len(items))} rows; relevant values are blank")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--make-label-sheet", type=int)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.make_label_sheet is not None:
        make_label_sheet(args.make_label_sheet, args.seed)
    else:
        run_filter(args.threshold)


if __name__ == "__main__":
    main()
