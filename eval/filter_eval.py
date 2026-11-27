"""Evaluate the relevance filter against hand-filled labels."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.collect.relevance import TEXT_DIR, reason_for, score, normalize

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "eval" / "filter_labels.csv"
REPORT = ROOT / "docs" / "filter_evaluation.md"


def confusion(rows: list[tuple[bool, bool]]) -> tuple[int, int, int, int]:
    tp = sum(actual and predicted for actual, predicted in rows)
    fp = sum(not actual and predicted for actual, predicted in rows)
    fn = sum(actual and not predicted for actual, predicted in rows)
    tn = sum(not actual and not predicted for actual, predicted in rows)
    return tp, fp, fn, tn


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=int, default=3)
    args = parser.parse_args()
    if not LABELS.exists():
        print("0 labeled, 20 needed")
        return 1
    with LABELS.open(encoding="utf-8-sig", newline="") as handle:
        labels = list(csv.DictReader(handle))
    accepted = {"yes": True, "oui": True, "no": False, "non": False}
    label_map = {row["text_id"]: accepted[normalize(row.get("relevant", ""))]
                 for row in labels if normalize(row.get("relevant", "")) in accepted}
    if len(label_map) < 20:
        print(f"{len(label_map)} labeled, 20 needed")
        return 1
    data = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in TEXT_DIR.glob("*.json")}
    missing = [text_id for text_id in label_map if text_id not in data]
    if missing:
        print(f"{len(missing)} labeled ids not found among the texts: {missing[:10]}")
        return 1
    evaluated = []
    for text_id, actual in label_map.items():
        item = data.get(text_id)
        if not item:
            continue
        value, _ = score(item.get("title", ""), item.get("raw_text", ""))
        evaluated.append((item, actual, value))
    relevant_count = sum(actual for _, actual, _ in evaluated)
    lines = ["# Filter evaluation", "", f"Labeled texts: {len(evaluated)}", f"Relevant texts: {relevant_count}", "",
             "| Threshold | TP | FP | FN | TN | Precision | Recall |", "|---:|---:|---:|---:|---:|---:|---:|"]
    for threshold in range(1, 7):
        rows = []
        for item, actual, value in evaluated:
            predicted, _ = reason_for(item, value, threshold)
            rows.append((actual, predicted))
        tp, fp, fn, tn = confusion(rows)
        precision = f"{tp / (tp + fp):.3f}" if tp + fp else "n/a"
        recall = f"{tp / (tp + fn):.3f}" if tp + fn else "n/a"
        lines.append(f"| {threshold} | {tp} | {fp} | {fn} | {tn} | {precision} | {recall} |")
    if relevant_count < 5:
        lines.extend(["", "**Warning:** Fewer than 5 relevant texts were labeled; precision and recall are not meaningful."])
    rows = []
    for item, actual, value in evaluated:
        predicted, _ = reason_for(item, value, args.threshold)
        if predicted != actual:
            rows.append(("false positive" if predicted else "false negative", item["text_id"], item.get("title", "")))
    lines.extend(["", f"## Errors at threshold {args.threshold}", ""])
    for label in ("false positive", "false negative"):
        lines.append(f"### {label.title()}")
        matches = [r for r in rows if r[0] == label]
        lines.extend([f"- `{text_id}` — {title}" for _, text_id, title in matches] or ["- None"])
        lines.append("")
    lines.extend(["Note: the threshold is chosen on the labeled sample, so these figures are optimistic; a second person must re-check 5 labels.", ""])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
