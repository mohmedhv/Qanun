"""Reconcile inventories and score the parser without overwriting P3 inputs.

Usage: python -m src.versions.week3_audit
Outputs only data/week3/*.csv and summary.json. It never runs the parser's
default output paths, changes verification statuses, or rebuilds SQLite.
"""
import csv
import json
import re
import tempfile
from collections import Counter
from pathlib import Path

from src.structuring import parse_amendments as parser
from src.versions.load_versions import verification_rows

ROOT = Path(__file__).resolve().parents[2]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def provision(value):
    return re.sub(r"^(?:art\.?|article)\s*", "", str(value).lower()).strip()


def key(row):
    return (row["modifying_text_id"], row["target_article"], provision(row["amending_article"]))


def edge_key(row):
    return (*key(row), row["action"])


def score(expected, actual):
    """Multiset scoring: duplicates count as false positives."""
    gold = Counter(edge_key(r) for r in expected)
    predictions = Counter(edge_key(r) for r in actual)
    tp = sum((gold & predictions).values())
    fp, fn = sum((predictions - gold).values()), sum((gold - predictions).values())
    return dict(tp=tp, fp=fp, fn=fn,
                precision=tp / (tp + fp) if tp + fp else None,
                recall=tp / (tp + fn) if tp + fn else None)


def run_parser(root):
    """Use the teammate's unchanged parser with private temporary outputs."""
    previous = parser.IN, parser.OUT_JSON, parser.OUT_CSV
    try:
        with tempfile.TemporaryDirectory() as directory:
            parser.IN = root / "data/interim/evolution_blocks.json"
            parser.OUT_JSON = Path(directory) / "amendments.json"
            parser.OUT_CSV = Path(directory) / "amendments.csv"
            parser.main()
            return read_json(parser.OUT_JSON)
    finally:
        parser.IN, parser.OUT_JSON, parser.OUT_CSV = previous


def compare(expected, actual):
    """Describe identity, action and wording changes independently."""
    index = {key(r): r for r in expected}
    rows = []
    consumed = set()
    seen = Counter()
    for row in actual:
        identity = key(row)
        seen[identity] += 1
        match = index.get(identity)
        reason = ""
        if seen[identity] > 1:
            category = "duplicate"
        elif match is None:
            candidates = [r for r in expected if r["target_article"] == row["target_article"]
                          and r["action"] == row["action"] and key(r) not in consumed]
            if len(candidates) == 1:
                match = candidates[0]
                category = "changed"
                reason = "Different legal text/provision attribution; candidate matched by target and action."
            else:
                category = "unexpected"
        else:
            fields = [f for f in ("action", "new_content", "partial", "needs_review") if row.get(f) != match.get(f)]
            category = "changed" if fields else "matching"
            reason = ", ".join(fields)
        if match is not None:
            consumed.add(key(match))
        rows.append(dict(modifying_text_id=row["modifying_text_id"], target_article=row["target_article"],
                         provision=row["amending_article"], action=row["action"], category=category,
                         reference_text_id=match["modifying_text_id"] if match else "", reason=reason))
    for row in expected:
        if key(row) not in consumed:
            rows.append(dict(modifying_text_id=row["modifying_text_id"], target_article=row["target_article"],
                             provision=row["amending_article"], action=row["action"], category="missing",
                             reference_text_id=row["modifying_text_id"], reason="Absent from parser output; retain P3 record."))
    return rows


def generate(root=ROOT):
    root = Path(root)
    out = root / "data/week3"
    out.mkdir(exist_ok=True)
    reference = read_json(root / "data/interim/amendments.json")
    old = read_json(out / "baselines/p2_59.json")
    parsed = run_parser(root)
    source = read_csv(root / "P3_Modified_Articles.csv")
    examples = read_csv(root / "P3_Officially_Checked_Examples.csv")
    linked = verification_rows()
    headers = {h["modifying_text_id"] for b in read_json(root / "data/interim/evolution_blocks.json")
               for h in parser.find_headers(b["text"])}
    source_index = {(r["amending_text_date"], r["law_90_11_article"], provision(r["amending_text_article"])): i
                    for i, r in enumerate(source)}
    gold_indices = set()
    for row in examples:
        gold_indices.add(source_index[(row["amending_text_date"], row["law_90_11_article"], provision(row["amending_text_article"]))])
    by_key = {key(r): r for r in reference}
    gold, ledger = [], []
    old_comparison = compare(reference, old)
    old_flags = {(r["target_article"], r["action"]) for r in old if r["needs_review"]}
    old_keys = {key(r) for r in old}
    for index, (csv_row, link) in enumerate(zip(source, linked)):
        identity = (link["modifying_text_id"], link["target_article"], provision(link["provision"]))
        amendment = by_key[identity]
        # The 19-member grouping is documented, but no raw snapshot with these
        # precise flags has been recovered. Keep it explicitly reconstructed.
        historical_19 = amendment["modifying_text_id"] == "loi-17-11" or (
            amendment["modifying_text_id"] == "ordonnance-96-21" and amendment["target_article"] in {"12", "13", "31", "54", "97"})
        ledger.append(dict(reference_row=index + 1, modifying_text_id=identity[0], target_article=identity[1],
                           provision=link["provision"], action=amendment["action"],
                           verification_status=csv_row["verification_status"], database_status=link["verification_status"],
                           source_url=csv_row["source_url"], printed_page=csv_row["pdf_page"],
                           original_28=csv_row["original_status"] == "A_VERIFIER_SOURCE_OFFICIELLE",
                           in_p2_59_exact=identity in old_keys,
                           p2_8_target_action_flag=(identity[1], amendment["action"]) in old_flags,
                           historical_19_reconstructed=historical_19,
                           historical_19_evidence="docs/P3_WEEK2_DELIVERY.md; original flag snapshot needed",
                           needs_textual_review=bool(amendment["needs_review"]), in_gold_51=index in gold_indices))
        if index in gold_indices:
            recoverable = identity[0] in headers
            gold.append(dict(reference_row=index + 1, modifying_text_id=identity[0], target_article=identity[1],
                             amending_article=link["provision"], action=amendment["action"],
                             original_gold_status=examples[next(i for i, r in enumerate(examples) if
                                 (r["amending_text_date"], r["law_90_11_article"], provision(r["amending_text_article"])) ==
                                 (csv_row["amending_text_date"], identity[1], identity[2]))]["verification_status"],
                             source_url=csv_row["source_url"], printed_page=csv_row["pdf_page"],
                             expected_recoverable=recoverable,
                             recovery_basis="Amending-text header occurs in actual parser input; operation scoring, not full wording." if recoverable else
                             "loi-22-16 absent from parser input headers; no parser recall expected on this source.",
                             current_parser_exact_match=any(edge_key(a) == edge_key(amendment) for a in parsed)))
    # Restrict predictions to eligible source texts when scoring the 51-row gold
    # set. Other legal operations are not false positives in this closed slice.
    gold_records = [by_key[key(r)] for r in gold]
    eligible = [by_key[key(r)] for r in gold if r["expected_recoverable"]]
    eligible_texts = {r["modifying_text_id"] for r in eligible}
    predictions = [r for r in parsed if r["modifying_text_id"] in eligible_texts]
    summary = dict(reference_rows=len(reference), p2_baseline_rows=len(old), p2_baseline_flags=sum(r["needs_review"] for r in old),
                   original_28=sum(r["original_28"] for r in ledger), historical_19_reconstructed=sum(r["historical_19_reconstructed"] for r in ledger),
                   textual_review_current=sum(r["needs_textual_review"] for r in ledger),
                   current_parser_rows=len(parsed), current_parser_flags=sum(r["needs_review"] for r in parsed),
                   gold_rows=len(gold), gold_recoverable=len(eligible), gold_missing_source=len(gold)-len(eligible),
                   all_inventory_operation_score=score(reference, parsed), gold_51_score=score(gold_records, predictions),
                   gold_recoverable_score=score(eligible, predictions),
                   interpretation="Operation identity score only. Source and full wording checks are separate; not legal accuracy or graph quality.")
    write_csv(out / "reference_reconciliation.csv", ledger)
    write_csv(out / "parser_59_comparison.csv", old_comparison)
    write_csv(out / "parser_71_comparison.csv", compare(reference, parsed))
    write_csv(out / "gold_51.csv", gold)
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(generate(), ensure_ascii=False, indent=2))
