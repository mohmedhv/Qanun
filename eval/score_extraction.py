"""Score LLM extraction vs rule extraction on the hard amendment cases.

Gold standard: the VERIFIED rows of P3_Modified_Articles.csv (Mohcem, P3).
A group (amending text + amending article) is scored only if P3 has verified
rows for it; other groups are listed as "à vérifier", never as right/wrong.

Unit compared: (target_article, action, modifying_text_number).
No API call is made. Run from the repo root:  python -m eval.score_extraction
"""
from __future__ import annotations

import json
import re

import pandas as pd

from eval.llm_extraction import AMENDMENTS, OUTPUT as LLM_CSV, hard_cases, normalize
from src.common.config import ROOT

P3_CSV = ROOT / "P3_Modified_Articles.csv"
RESULT = ROOT / "eval/results/extraction_scores.json"

ACTION_FROM_P3 = (("terminology", "term_substitution"), ("completed", "complete"),
                  ("modified", "modify"), ("new article", "insert"), ("repealed", "repeal"))


def art(value: str) -> str:
    """'87  bis' / '73-1' / 'Art. 2' -> comparable form."""
    value = re.sub(r"^\s*art(icle)?\.?\s*", "", str(value), flags=re.I)
    return re.sub(r"\s+", " ", value.replace("er", "")).strip().lower()


def text_number(value: str) -> str:
    match = re.search(r"\d{2}-\d{1,3}", str(value))
    return match.group(0) if match else ""


def p3_action(operation_type: str) -> str:
    low = operation_type.lower()
    return next((action for key, action in ACTION_FROM_P3 if low.startswith(key)), "other")


def prf(system: set, gold: set) -> dict:
    tp = len(system & gold)
    return {"system_records": len(system), "gold_records": len(gold), "true_positives": tp,
            "precision": round(tp / len(system), 3) if system else None,
            "recall": round(tp / len(gold), 3) if gold else None}


def main() -> None:
    rules = hard_cases(pd.read_csv(AMENDMENTS, encoding="utf-8-sig", dtype=str).fillna(""))
    llm = pd.read_csv(LLM_CSV, encoding="utf-8-sig", dtype=str).fillna("")
    p3 = pd.read_csv(P3_CSV, encoding="utf-8-sig", dtype=str).fillna("")
    verified = p3[p3["verification_status"].str.startswith("VERIFIED")]

    gold_by_group: dict[tuple, set] = {}
    for _, row in verified.iterrows():
        group = (text_number(row["amending_legal_text"]), art(row["amending_text_article"]))
        gold_by_group.setdefault(group, set()).add(
            (art(row["law_90_11_article"]), p3_action(row["operation_type"]), group[0]))
    all_verified = set().union(*gold_by_group.values())

    def group_of(text_id: str, amending_article: str) -> tuple:
        return (text_number(text_id), art(amending_article))

    groups = {group_of(t, a) for t, a in zip(rules["modifying_text_id"], rules["amending_article"])}
    scored = {g for g in groups if g in gold_by_group}
    gold = set().union(*(gold_by_group[g] for g in scored)) if scored else set()

    rule_keys = {(art(r.target_article), r.action, text_number(r.modifying_text_id))
                 for r in rules.itertuples() if group_of(r.modifying_text_id, r.amending_article) in scored}

    llm["group"] = [group_of(t, a) for t, a in zip(llm["rule_modifying_text_id"], llm["rule_amending_article"])]
    llm["key"] = [(art(r.target_article), r.action, text_number(r.modifying_text_number)) for r in llm.itertuples()]
    llm["own_group"] = [(text_number(r.modifying_text_number), art(r.amending_article)) for r in llm.itertuples()]
    in_scored = llm[llm["group"].isin(scored)]
    # Records about a different amending article than the one asked (e.g. 12 bis, Art. 3)
    # are kept apart: they are outside the hard case, not errors of it.
    on_target = in_scored[[own == grp for own, grp in zip(in_scored["own_group"], in_scored["group"])]]
    off_target = in_scored.drop(on_target.index)
    llm_keys = set(on_target["key"])

    def loose(keys: set) -> set:  # ignore the action label
        return {(a, t) for a, _, t in keys}

    inventions = []
    for r in llm.itertuples():
        page = normalize(r.passage)
        reasons = []
        if r.evidence_in_passage != "True":
            reasons.append("evidence quote not in passage")
        if r.target_article and art(r.target_article) not in page:
            reasons.append("target article not in passage")
        if r.modifying_text_number and text_number(r.modifying_text_number) not in page:
            reasons.append("modifying text number not in passage")
        if reasons:
            inventions.append({"group": r.group_id, "target": r.target_article, "reasons": reasons})

    def describe(rows: pd.DataFrame) -> list[dict]:
        return [{"group": r.group_id, "target_article": r.target_article, "action": r.action,
                 "modifying_text": f"{r.modifying_text_type} {r.modifying_text_number}".strip(),
                 "amending_article": r.amending_article, "uncertain": r.uncertain,
                 "matches_verified_p3": r.key in all_verified,
                 # same article and action as a verified P3 row, but a different amending text
                 "contradicts_verified_p3": bool(r.key[2]) and any(
                     a == r.key[0] and act == r.key[1] and t != r.key[2] for a, act, t in all_verified)}
                for r in rows.itertuples()]

    disagreements = sorted(
        {"target_article": a, "llm_action": la, "gold_action": ga}
        for a, la, t in llm_keys for ga_a, ga, gt in gold if a == ga_a and t == gt and la != ga
    ) if llm_keys else []

    unscored = llm[~llm["group"].isin(scored)]
    report = {
        "model": ", ".join(sorted(set(llm["model"]))),
        "hard_rule_records": len(rules),
        "llm_records": len(llm),
        "scored_groups": sorted(f"{t} {a}" for t, a in scored),
        "strict": {"rules": prf(rule_keys, gold), "llm": prf(llm_keys, gold)},
        "ignoring_action_label": {"rules": prf(loose(rule_keys), loose(gold)),
                                  "llm": prf(loose(llm_keys), loose(gold))},
        "action_disagreements_llm_vs_p3": [dict(d) for d in disagreements],
        "llm_invention": {"records_checked": len(llm), "invented": len(inventions),
                          "rate": round(len(inventions) / len(llm), 3) if len(llm) else None,
                          "details": inventions},
        "llm_extra_records_outside_hard_case": describe(off_target),
        "unscored_a_verifier": describe(unscored),
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
