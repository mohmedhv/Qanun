from __future__ import annotations

import argparse
import csv
import json
import math
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTICLES_PATH = ROOT / "data" / "interim" / "articles.json"
QUESTIONS_PATH = ROOT / "eval" / "questions.csv"
REPORT_PATH = ROOT / "docs" / "retrieval_comparison.md"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    folded = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(char for char in folded if not unicodedata.combining(char))
    return TOKEN_RE.findall(plain)


def bm25_rank(articles: list[dict], query: str, k: int = 3) -> list[dict]:
    corpus = [tokenize(item["content"]) for item in articles]
    n_docs = len(corpus)
    average_length = sum(map(len, corpus)) / n_docs if n_docs else 0.0
    frequencies = [Counter(doc) for doc in corpus]
    document_frequency = Counter(term for doc in frequencies for term in doc)
    query_terms = tokenize(query)
    scored = []
    k1, b = 1.5, 0.75
    for item, terms, counts in zip(articles, corpus, frequencies):
        score = 0.0
        for term in query_terms:
            tf = counts.get(term, 0)
            if not tf:
                continue
            df = document_frequency[term]
            idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
            denom = tf + k1 * (1.0 - b + b * len(terms) / average_length)
            score += idf * tf * (k1 + 1.0) / denom
        scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], int(pair[1]["sort_key"])))
    return [item for _, item in scored[:k]]


def embedding_rank(articles: list[dict], questions: list[dict], model_name: str, k: int = 3):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None, "sentence-transformers is not installed in this environment."
    try:
        model = SentenceTransformer(model_name, local_files_only=True)
        article_vectors = model.encode(
            [item["content"] for item in articles],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        query_vectors = model.encode(
            [row["question"] for row in questions],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    except Exception as exc:
        return None, f"Model unavailable locally ({type(exc).__name__}: {exc})."

    rankings = {}
    for row, query_vector in zip(questions, query_vectors):
        scores = []
        for article, article_vector in zip(articles, article_vectors):
            score = sum(float(left) * float(right) for left, right in zip(query_vector, article_vector))
            scores.append((score, article))
        scores.sort(key=lambda pair: (-pair[0], int(pair[1]["sort_key"])))
        rankings[row["question_id"]] = [item for _, item in scores[:k]]
    return rankings, f"Local SentenceTransformer model: {model_name}."


def metric_values(top: list[dict] | None, references: set[str]) -> tuple[str, str, str]:
    if top is None or not references:
        return "n/a", "n/a", "n/a"
    found = {str(item["number"]) for item in top} & references
    return ("yes" if found else "no", f"{len(found)}/3", f"{len(found)}/{len(references)}")


def fmt_top(top: list[dict] | None) -> str:
    if top is None:
        return "pending"
    return ", ".join(str(item["number"]) for item in top)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare BM25 and local dense embeddings on the 158-article corpus.")
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    args = parser.parse_args()

    articles = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    with QUESTIONS_PATH.open(encoding="utf-8-sig", newline="") as handle:
        questions = list(csv.DictReader(handle))
    if len(articles) != 158:
        raise ValueError(f"Expected 158 article chunks, found {len(articles)}")

    bm25 = {row["question_id"]: bm25_rank(articles, row["question"]) for row in questions}
    dense, dense_note = embedding_rank(articles, questions, args.embedding_model)
    lines = [
        "# Retrieval comparison: Law 90-11",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Corpus and method",
        "",
        f"- Corpus: {len(articles)} chunks, one per article in data/interim/articles.json; article numbers {articles[0]['number']}–{articles[-1]['number']}, with no number gaps.",
        "- The workspace has no built SQLite database in data/db; this run uses the current JSON article base. Confirm it matches Ikram's latest shared database before submission.",
        "- Questions: all 10 rows in eval/questions.csv. The relevance references are the article numbers supplied in that file.",
        "- BM25: standard Okapi BM25 (k1=1.5, b=0.75), Unicode accent normalization and word tokens, top 3.",
        f"- Dense retrieval: {dense_note}",
        "- Hit@3 is yes if at least one reference article appears in the top 3. P@3 divides the relevant hits by 3; R@3 divides by the number of reference articles.",
        "- Aggregate metrics include only the 7 in-scope questions whose reference labels are marked verified=oui. Q08 and Q09 remain visible but are excluded because their labels are unverified; Q10 is out of scope.",
        "",
        "## Per-question results",
        "",
        "| ID | Refs | Label | BM25 top 3 | Hit@3 | P@3 | R@3 | Embedding top 3 | Hit@3 | P@3 | R@3 |",
        "|---|---|---|---|---:|---:|---:|---|---:|---:|---:|",
    ]
    verified_hits: dict[str, list[bool]] = {"bm25": [], "embedding": []}
    verified_precision: dict[str, list[float]] = {"bm25": [], "embedding": []}
    verified_recall: dict[str, list[float]] = {"bm25": [], "embedding": []}
    for row in questions:
        refs = {value.strip() for value in row["reference_articles"].split(";") if value.strip()}
        label = row["verified"] or "non renseigné"
        btop = bm25[row["question_id"]]
        bhit, bp, br = metric_values(btop, refs)
        etop = dense.get(row["question_id"]) if dense is not None else None
        ehit, ep, er = metric_values(etop, refs)
        ref_text = ", ".join(sorted(refs, key=lambda value: int(value) if value.isdigit() else 0))
        lines.append(
            f"| {row['question_id']} | {ref_text} | {label} | {fmt_top(btop)} | {bhit} | {bp} | {br} | {fmt_top(etop)} | {ehit} | {ep} | {er} |"
        )
        if row["verified"].casefold() == "oui" and row["category"] != "hors_perimetre" and refs:
            for name, top, hit, precision, recall in (
                ("bm25", btop, bhit, bp, br),
                ("embedding", etop, ehit, ep, er),
            ):
                verified_hits[name].append(hit == "yes")
                if top is not None:
                    precision_value = len({str(item["number"]) for item in top} & refs) / 3
                    recall_value = len({str(item["number"]) for item in top} & refs) / len(refs)
                    verified_precision[name].append(precision_value)
                    verified_recall[name].append(recall_value)

    lines.extend(["", "## Aggregate on verified, in-scope questions", "", "| Method | Hit@3 | Mean P@3 | Mean R@3 |", "|---|---:|---:|---:|"])
    for name, display in (("bm25", "BM25"), ("embedding", "Embeddings")):
        hits = verified_hits[name]
        if not hits or (name == "embedding" and dense is None):
            lines.append(f"| {display} | n/a | n/a | n/a |")
        else:
            hit_count = sum(hits)
            precision = sum(verified_precision[name]) / len(verified_precision[name])
            recall = sum(verified_recall[name]) / len(verified_recall[name])
            lines.append(f"| {display} | {hit_count}/{len(hits)} ({hit_count / len(hits):.1%}) | {precision:.3f} | {recall:.3f} |")
    lines.extend([
        "",
        "## Status and next step",
        "",
        "A pending embedding result is not a zero score. Install the pinned sentence-transformers dependency and cache the model approved for the project, then rerun this script. It uses local model files only and does not download weights or call an LLM.",
        "",
        "This is article retrieval evaluation, separate from the UpGrowth issue-filter evaluation. The 30 rows in eval/filter_labels.csv currently have no relevance labels, so precision and recall for the issue filter cannot yet be calculated.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
