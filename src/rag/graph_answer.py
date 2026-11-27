"""Answer "which text modified / repealed / added article X?" from the knowledge graph.

Deterministic: no LLM call. Sources:
  - P2 graph (Ikram): data/graph/edges.csv and nodes.csv (src/graph/build_graph.py)
  - P3 versions (Mohcem): src/versions/versions.py (get_version, list_versions)
Every cited (text, article, relation, provision) is checked against the graph edges by
eval.citation_verifier.verify_graph_citations.

Run from the repo root:
    python -m src.rag.graph_answer "Quel texte a modifié l'article 73 ?"
"""
from __future__ import annotations

import csv
import re
import sys
from functools import lru_cache

from eval.citation_verifier import ARTICLE_RE, _norm_number, article_node, verify_graph_citations
from src.common.config import ROOT
from src.versions.versions import get_version, list_versions

GRAPH_DIR = ROOT / "data" / "graph"
TEXT_ID = "loi-90-11"
RELATIONS = ("modifies", "repeals", "adds")  # text -> article edges used for the answer
VERB = {"modifies": "a modifié", "repeals": "a abrogé", "adds": "a ajouté (créé)"}
TYPE_LABEL = {"loi": "Loi", "ordonnance": "Ordonnance", "decret_legislatif": "Décret législatif",
              "decret-legislatif": "Décret législatif", "decret_executif": "Décret exécutif",
              "decret-executif": "Décret exécutif", "decret_presidentiel": "Décret présidentiel"}
REFUSAL = "Je ne trouve pas de règle dans le corpus."


@lru_cache(maxsize=1)
def load_graph() -> tuple[tuple[dict, ...], dict[str, dict]]:
    """(edges, nodes by id) from data/graph/*.csv, read once."""
    with (GRAPH_DIR / "edges.csv").open(encoding="utf-8") as f:
        edges = tuple(csv.DictReader(f))
    with (GRAPH_DIR / "nodes.csv").open(encoding="utf-8") as f:
        nodes = {row["node_id"]: row for row in csv.DictReader(f)}
    return edges, nodes


def article_from_question(question: str) -> str | None:
    """'Quel texte a modifié l'article 87 bis ?' -> '87 bis'; None if no article is named."""
    match = ARTICLE_RE.search(question)
    return _norm_number(match.group(1)) if match else None


def text_label(node: dict) -> str:
    kind = TYPE_LABEL.get(node.get("type", ""), node.get("type", "").capitalize())
    return f"{kind} n° {node.get('number', '')}".strip()


def events_for(article: str) -> list[dict]:
    """Texts that modified, repealed or added the article, oldest first."""
    edges, nodes = load_graph()
    target = article_node(article, TEXT_ID)
    events = []
    for e in edges:
        if e["target"] != target or e["relation"] not in RELATIONS or not e["source"].startswith("text:"):
            continue
        node = nodes.get(e["source"], {})
        events.append({
            "text_id": e["source"].removeprefix("text:"), "label": text_label(node),
            "relation": e["relation"], "provision": e.get("provision", ""),
            "date_signed": node.get("date_signed", ""), "jo_number": node.get("jo_number", ""),
            "jo_date": node.get("jo_date", ""), "source_url": e.get("source_url") or node.get("source_url", ""),
            "edge_status": e.get("status", ""),
        })
    return sorted(events, key=lambda ev: (ev["date_signed"] or ev["jo_date"], ev["relation"]))


def version_check(article: str, text_id: str) -> dict:
    """Does P3's version history agree that this text changed the article?"""
    versions = list_versions(TEXT_ID, article)
    if not versions:
        return {"status": "not_tracked", "versions": 0}
    matched = [v for v in versions if text_id in (v.get("modifying_text_id"), v.get("repealing_text_id"))]
    return {"status": "confirmed" if matched else "mismatch", "versions": len(versions),
            "version_numbers": [v.get("version_number") for v in matched]}


def current_state(article: str) -> dict:
    """Version in force today according to P3 (None if repealed or not tracked)."""
    versions = list_versions(TEXT_ID, article)
    if not versions:
        return {"tracked": False, "in_force": None}
    current = get_version(TEXT_ID, article)
    if current is None:
        return {"tracked": True, "in_force": False, "last_status": versions[-1].get("status")}
    return {"tracked": True, "in_force": True, "version_number": current.get("version_number"),
            "valid_from": current.get("valid_from")}


def _refuse(question: str, article: str | None, reason: str) -> dict:
    text = (f"(a) RÉPONSE COURTE\n{REFUSAL}\n\n(b) EXPLICATION SIMPLE\n{reason}\n\n"
            "(c) ARTICLES CITÉS\nAucun.\n\n(d) CONFIANCE ET LIMITES\nLe graphe ne couvre que les textes "
            "collectés ; le système informe et ne remplace pas un avocat.")
    return {"question": question, "article": article, "refused": True, "events": [], "citations": [],
            "citations_valid": True, "confidence": "élevé", "text": text}


def answer(question: str) -> dict:
    article = article_from_question(question)
    if article is None:
        return _refuse(question, None, "La question ne cite aucun article de la loi n° 90-11.")
    _, nodes = load_graph()
    if article_node(article, TEXT_ID) not in nodes:
        return _refuse(question, article, f"L'article {article} n'existe pas dans le graphe de la loi n° 90-11.")
    events = events_for(article)
    if not events:
        return _refuse(question, article,
                       f"Le graphe ne contient aucun texte qui modifie, abroge ou ajoute l'article {article}.")

    for ev in events:
        ev["version_check"] = version_check(article, ev["text_id"])
    state = current_state(article)
    citations = [{"text_id": ev["text_id"], "article": article, "relation": ev["relation"],
                  "provision": ev["provision"]} for ev in events]
    edges, _ = load_graph()
    citations_valid = verify_graph_citations(citations, list(edges))

    unverified = [ev for ev in events if ev["edge_status"] != "verifie_jo_officiel"]
    mismatched = [ev for ev in events if ev["version_check"]["status"] == "mismatch"]
    untracked = [ev for ev in events if ev["version_check"]["status"] == "not_tracked"]
    if unverified or mismatched or not citations_valid:
        confidence = "faible"
    elif untracked:
        confidence = "moyen"
    else:
        confidence = "élevé"

    short = "; ".join(f"{ev['label']} ({ev['provision']}, signé le {ev['date_signed']}) {VERB[ev['relation']]} "
                      f"l'article {article}" for ev in events)
    if state["tracked"] and state["in_force"]:
        now = f"Selon les versions P3, l'article {article} est en vigueur (version {state['version_number']} depuis le {state['valid_from']})."
    elif state["tracked"]:
        now = f"Selon les versions P3, l'article {article} n'a plus de version en vigueur (abrogé)."
    else:
        now = f"Les versions de l'article {article} ne sont pas encore suivies par P3."
    cited = "\n".join(
        f"- {ev['label']}, {ev['provision']} — {ev['relation']} — signé le {ev['date_signed']}, "
        f"{ev['jo_number']} du {ev['jo_date']} — {ev['source_url']} — graphe : {ev['edge_status']} — "
        f"versions P3 : {ev['version_check']['status']}" for ev in events)
    limits = []
    if mismatched:
        limits.append("historique P3 en désaccord avec le graphe pour : "
                      + ", ".join(f"{ev['label']} ({ev['provision']})" for ev in mismatched))
    if untracked:
        limits.append(f"les versions de l'article {article} ne sont pas suivies par P3")
    if unverified:
        limits.append("liens non vérifiés au JO officiel : "
                      + ", ".join(f"{ev['label']} ({ev['edge_status']})" for ev in unverified))
    limits.append("le graphe ne couvre que les textes collectés ; le système informe et ne remplace pas un avocat")
    text = (f"(a) RÉPONSE COURTE\n{short}.\n\n(b) EXPLICATION SIMPLE\n"
            f"D'après le graphe des textes, {len(events)} texte(s) ont changé l'article {article} de la loi n° 90-11. {now}\n\n"
            f"(c) ARTICLES CITÉS\n{cited}\n\n(d) CONFIANCE ET LIMITES\nNiveau de confiance : {confidence}.\n"
            f"Limites : {'; '.join(limits)}.")
    return {"question": question, "article": article, "refused": False, "events": events,
            "current": state, "citations": citations, "citations_valid": citations_valid,
            "confidence": confidence, "text": text}


if __name__ == "__main__":
    print(answer(" ".join(sys.argv[1:]) or "Quel texte a modifié l'article 73 ?")["text"])
