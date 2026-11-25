"""Compare BM25 and E5 retrieval on the 10 teacher questions and P2 chunks."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from src.search.bm25_search import BM25Index
from src.search.search_service import load_documents
from src.search.semantic_search import E5Index

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS_PATH = ROOT / "eval" / "questions.csv"
REPORT_PATH = ROOT / "docs" / "retrieval_comparison.md"
TOP_K = 3


def top_articles(ranked, k: int = TOP_K) -> list[dict]:
    """Return the first k distinct article citations from a passage ranking."""
    result = []
    seen = set()
    for document, _score in ranked:
        citation = document["cite_id"]
        if citation in seen:
            continue
        seen.add(citation)
        result.append(document)
        if len(result) == k:
            break
    return result


def score_top(top: list[dict] | None, references: set[str]) -> tuple[str, str, str]:
    if top is None or not references:
        return "n/a", "n/a", "n/a"
    found = {str(document["number"]) for document in top} & references
    hit = "oui" if found else "non"
    return hit, f"{len(found)}/{TOP_K}", f"{len(found)}/{len(references)}"


def main() -> int:
    questions = []
    with QUESTIONS_PATH.open(encoding="utf-8-sig", newline="") as handle:
        questions = list(csv.DictReader(handle))
    if len(questions) != 10:
        raise ValueError(f"Expected the teacher's 10 questions; found {len(questions)}")
    if len({row["question_id"] for row in questions}) != len(questions):
        raise ValueError("Question IDs must be unique")

    documents = load_documents()
    article_ids = {document["cite_id"] for document in documents}
    if not documents or len(article_ids) != 158:
        raise ValueError(f"Expected passages for 158 articles; found {len(article_ids)} article IDs")
    article_numbers = {str(document["number"]) for document in documents}
    for row in questions:
        references = {value.strip() for value in row["reference_articles"].split(";") if value.strip()}
        missing = references - article_numbers
        if missing:
            raise ValueError(f"{row['question_id']} refers to missing article(s): {sorted(missing)}")

    bm25 = BM25Index(documents)
    try:
        e5 = E5Index(documents)
        e5_rankings = {
            row["question_id"]: top_articles(e5.search(row["question"], k=len(documents)))
            for row in questions
        }
        e5_note = f"Disponible : modèle `{e5.model_name}`, {len(e5.vectors)} vecteurs de passages en cache; les 10 questions ont été encodées."
    except Exception as exc:
        e5 = None
        e5_rankings = {}
        e5_note = f"Indisponible ({type(exc).__name__} : {exc})."

    rows = []
    for question in questions:
        references = {value.strip() for value in question["reference_articles"].split(";") if value.strip()}
        bm_top = top_articles(bm25.search(question["question"], k=len(documents)))
        e5_top = e5_rankings.get(question["question_id"]) if e5 else None
        bm_hit, bm_precision, bm_recall = score_top(bm_top, references)
        e5_hit, e5_precision, e5_recall = score_top(e5_top, references)
        rows.append({
            "question": question,
            "references": references,
            "bm_top": bm_top,
            "e5_top": e5_top,
            "bm_hit": bm_hit,
            "bm_precision": bm_precision,
            "bm_recall": bm_recall,
            "e5_hit": e5_hit,
            "e5_precision": e5_precision,
            "e5_recall": e5_recall,
        })

    verified = [
        row for row in rows
        if row["question"]["verified"].strip().casefold() == "oui"
        and row["question"]["category"].strip().casefold() != "hors_perimetre"
        and row["references"]
    ]

    lines = [
        "# Comparaison de la recherche — loi 90-11",
        "",
        f"Date d'exécution : {date.today().isoformat()}.",
        "",
        "## Corpus et protocole",
        "",
        f"- Corpus P2 : {len(documents)} passages pour {len(article_ids)} articles distincts, chargés par `src.search.search_service.load_documents()` depuis les chunks du dépôt.",
        "- Les articles 7 et 94 sont découpés en deux passages chacun; la métrique déduplique les résultats par citation d'article avant le top 3.",
        "- Questions : les 10 lignes de `eval/questions.csv`; les références sont les numéros d'articles inscrits dans ce fichier.",
        "- BM25 : l'index partagé `src.search.bm25_search.BM25Index`, `k1=1.5`, `b=0.75`.",
        f"- E5 : {e5_note}",
        "- Hit@3 vaut oui si au moins un article de référence apparaît dans les trois premiers articles distincts. P@3 divise les références trouvées par 3; R@3 les divise par le nombre de références attendues.",
        "- Le résultat agrégé n'inclut que les questions `verified=oui` et dans le périmètre; Q08–Q09 restent visibles mais non vérifiées, Q10 est hors périmètre.",
        "- Cette comparaison porte sur le corpus français original de 1990. Elle ne valide pas les versions historiques ni les références juridiques; Q09 (1997) est donc affichée, mais exclue de l'agrégat.",
        "- Le calcul des embeddings est local et n'appelle aucun LLM ni API générative.",
        "",
        "## Résultats par question",
        "",
        "| ID | Références | Validation | BM25 top 3 | Hit@3 | P@3 | R@3 | E5 top 3 | Hit@3 | P@3 | R@3 |",
        "|---|---|---|---|---:|---:|---:|---|---:|---:|---:|",
    ]
    for row in rows:
        question = row["question"]
        refs = ", ".join(sorted(row["references"], key=int))
        bm_numbers = ", ".join(str(document["number"]) for document in row["bm_top"])
        e5_numbers = ", ".join(str(document["number"]) for document in row["e5_top"]) if row["e5_top"] else "en attente"
        lines.append(
            f"| {question['question_id']} | {refs or '—'} | {question['verified']} | {bm_numbers} | {row['bm_hit']} | {row['bm_precision']} | {row['bm_recall']} | {e5_numbers} | {row['e5_hit']} | {row['e5_precision']} | {row['e5_recall']} |"
        )

    lines.extend([
        "",
        "## Résultats agrégés — questions vérifiées et dans le périmètre",
        "",
        "| Méthode | Questions évaluées | Hit@3 | P@3 moyen | R@3 moyen |",
        "|---|---:|---:|---:|---:|",
    ])
    for name, display in (("bm", "BM25"), ("e5", "E5")):
        evaluated = [row for row in verified if row[f"{name}_top"] is not None]
        if not evaluated:
            lines.append(f"| {display} | 0/{len(verified)} | n/a | n/a | n/a |")
            continue
        hits = sum(row[f"{name}_hit"] == "oui" for row in evaluated)
        precisions = [int(row[f"{name}_precision"].split("/")[0]) / TOP_K for row in evaluated]
        recalls = [
            int(row[f"{name}_recall"].split("/")[0]) / len(row["references"])
            for row in evaluated
        ]
        lines.append(
            f"| {display} | {len(evaluated)}/{len(verified)} | {hits}/{len(evaluated)} ({hits / len(evaluated):.1%}) | {sum(precisions) / len(precisions):.3f} | {sum(recalls) / len(recalls):.3f} |"
        )

    lines.extend([
        "",
        "## Limites et reproduction",
        "",
        "Les étiquettes `oui` viennent du fichier de questions et n'ont pas été revues par une seconde personne pendant ce calcul. Les références Q08 et Q09 restent à vérifier; Q10 sert de contrôle hors périmètre. Les scores mesurent le classement des références fournies, pas la justesse juridique.",
        "",
        "Reproduction : exécuter `python -m eval.retrieval_comparison` depuis la racine. Le cache E5 des passages doit correspondre aux chunks chargés; `E5Index` le valide par identifiants et empreinte SHA-256 du corpus. Installer les dépendances de `requirements.txt` et disposer localement des poids `intfloat/multilingual-e5-small`.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    report = "\n".join(lines)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
