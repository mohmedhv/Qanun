"""LLM-assisted extraction on the amendment records the rules cannot handle.

Hard cases in data/interim/amendments.csv (P2 rule output):
  - action == term_substitution
  - partial == True
  - needs_review == True   (e.g. the uncertain 87 bis repeal)

Records sharing one amending instruction are sent in a single call. Only the
public passage of the law (from data/interim/evolution_blocks.json) is sent.
Every output row keeps extraction_method=llm and status="à vérifier".

Run from the repo root:  python -m eval.llm_extraction
"""
from __future__ import annotations

import json
import unicodedata
import re

import pandas as pd

from src.common.config import ROOT, load_config
from src.rag.llm_cache import generate_cached

AMENDMENTS = ROOT / "data/interim/amendments.csv"
BLOCKS = ROOT / "data/interim/evolution_blocks.json"
OUTPUT = ROOT / "data/interim/amendments_llm.csv"
CONTEXT_BEFORE = 500  # characters before the instruction (holds the amending text's header)

SYSTEM = """Tu es un outil d'extraction pour des textes juridiques algériens publics.
On te donne un passage qui modifie la loi n° 90-11 du 21 avril 1990.
Extrais UNIQUEMENT ce que le passage dit, sans rien ajouter de mémoire.

Réponds avec un seul objet JSON, sans texte autour :
{"records": [
  {"target_article": "numéro de l'article de la loi 90-11 visé, ex. \\"12\\" ou \\"87 bis\\"",
   "action": "modify | complete | insert | repeal | term_substitution",
   "modifying_text_type": "Loi | Ordonnance | Décret législatif | Décret exécutif | null",
   "modifying_text_number": "ex. \\"96-21\\", ou null si incertain",
   "amending_article": "article du texte modificateur, ex. \\"Art. 2\\"",
   "partial": true ou false,
   "uncertain": true ou false,
   "evidence": "citation EXACTE et courte du passage qui justifie cet enregistrement"}
]}

Règles :
- Un enregistrement par article de la loi 90-11 visé (si une phrase vise 17 articles, 17 enregistrements).
- complete = ajout d'alinéas/paragraphes ; modify = article modifié ou réécrit ;
  insert = nouvel article ajouté ; repeal = abrogation ;
  term_substitution = un terme est ajouté ou remplacé sans réécrire l'article.
- partial = true si le passage ne donne qu'une partie du nouveau texte.
- Si le texte modificateur n'est pas clairement identifié dans le passage,
  mets modifying_text_number à null et uncertain à true.
"""


def hard_cases(rows: pd.DataFrame) -> pd.DataFrame:
    mask = ((rows["action"] == "term_substitution")
            | (rows["partial"].astype(str) == "True")
            | (rows["needs_review"].astype(str) == "True"))
    return rows[mask]


def passage_for(instruction: str, new_content: str, blocks: list[dict]) -> str:
    """Public source passage: header context + instruction + quoted new text."""
    for block in blocks:
        text = block["text"]
        pos = text.find(instruction[:60])
        if pos >= 0:
            start = text.rfind("\n", 0, max(0, pos - CONTEXT_BEFORE)) + 1
            end = pos + len(instruction) + len(new_content) + 200
            return text[start:end]
    return instruction + ("\n" + new_content if new_content else "")


def normalize(text: str) -> str:
    """Lowercase, unify quotes/dashes/apostrophes, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text)
    for src, dst in (("’", "'"), ("‘", "'"), ("«", '"'), ("»", '"'), ("“", '"'),
                     ("”", '"'), ("‑", "-"), ("–", "-"), ("—", "-")):
        text = text.replace(src, dst)
    return re.sub(r"\s+", " ", text).strip().lower()


def evidence_found(evidence: str, passage: str) -> bool:
    """True if every piece of the quote (split on ... or …) appears in the passage."""
    pieces = [p.strip(" .,:;\"") for p in re.split(r"\.\.\.|…", normalize(evidence))]
    pieces = [p for p in pieces if len(p) >= 15]
    page = normalize(passage)
    return bool(pieces) and all(p in page for p in pieces)


def parse_json(answer: str) -> list[dict]:
    """Read the JSON object even if the model wrapped it in a code fence."""
    match = re.search(r"\{.*\}", answer, re.DOTALL)
    if not match:
        raise ValueError("no JSON object in the model answer")
    return json.loads(match.group(0)).get("records", [])


def main() -> None:
    config = load_config()
    model = config["llm"]["model"]
    rules = pd.read_csv(AMENDMENTS, encoding="utf-8-sig", dtype=str).fillna("")
    blocks = json.loads(BLOCKS.read_text(encoding="utf-8"))
    hard = hard_cases(rules)
    groups = hard.groupby(["modifying_text_id", "amending_article", "instruction"], sort=False)
    print(f"{len(hard)} hard records in {len(groups)} groups -> {len(groups)} LLM prompts")

    out = []
    for group_id, ((text_id, amending_article, instruction), members) in enumerate(groups, start=1):
        passage = passage_for(instruction, members.iloc[0]["new_content"], blocks)
        prompt = f"PASSAGE :\n{passage}"
        targets = ", ".join(members["target_article"])
        print(f"G{group_id}: {text_id} {amending_article} -> rule targets {targets}")
        answer = generate_cached(prompt, system_instruction=SYSTEM, config=config)
        try:
            records, error = parse_json(answer), ""
        except (ValueError, json.JSONDecodeError) as exc:
            records, error = [], f"parse error: {exc}"
        if not records:
            records = [{}]
        for rec in records:
            evidence = str(rec.get("evidence") or "")
            out.append({
                "group_id": f"G{group_id}",
                "rule_modifying_text_id": text_id,
                "rule_amending_article": amending_article,
                "rule_targets": targets,
                "target_article": str(rec.get("target_article") or ""),
                "action": rec.get("action") or "",
                "modifying_text_type": rec.get("modifying_text_type") or "",
                "modifying_text_number": rec.get("modifying_text_number") or "",
                "amending_article": rec.get("amending_article") or "",
                "partial": rec.get("partial"),
                "uncertain": rec.get("uncertain"),
                "evidence": evidence,
                "evidence_in_passage": evidence_found(evidence, passage),
                "passage": passage,
                "extraction_method": "llm",
                "status": "à vérifier",
                "model": model,
                "error": error,
            })
    pd.DataFrame(out).to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"Wrote {len(out)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
