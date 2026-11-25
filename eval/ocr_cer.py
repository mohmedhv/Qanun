"""Compute character and word error rates between a reference and OCR text."""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ErrorCounts:
    substitutions: int
    deletions: int
    insertions: int

    @property
    def distance(self) -> int:
        return self.substitutions + self.deletions + self.insertions


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def levenshtein_counts(reference: str, hypothesis: str) -> ErrorCounts:
    rows, columns = len(reference) + 1, len(hypothesis) + 1
    distance = [[0] * columns for _ in range(rows)]
    for i in range(rows):
        distance[i][0] = i
    for j in range(columns):
        distance[0][j] = j

    for i in range(1, rows):
        for j in range(1, columns):
            substitution_cost = 0 if reference[i - 1] == hypothesis[j - 1] else 1
            distance[i][j] = min(
                distance[i - 1][j] + 1,
                distance[i][j - 1] + 1,
                distance[i - 1][j - 1] + substitution_cost,
            )

    substitutions = deletions = insertions = 0
    i, j = len(reference), len(hypothesis)
    while i or j:
        if i and j:
            cost = 0 if reference[i - 1] == hypothesis[j - 1] else 1
            if distance[i][j] == distance[i - 1][j - 1] + cost:
                substitutions += cost
                i -= 1
                j -= 1
                continue
        if i and distance[i][j] == distance[i - 1][j] + 1:
            deletions += 1
            i -= 1
        else:
            insertions += 1
            j -= 1
    return ErrorCounts(substitutions, deletions, insertions)


def rate(counts: ErrorCounts, reference_units: int) -> float:
    if reference_units == 0:
        raise ValueError("La référence normalisée ne peut pas être vide.")
    return counts.distance / reference_units


def evaluate(reference_text: str, ocr_text: str) -> tuple[ErrorCounts, float, ErrorCounts, float, int, int]:
    reference = normalize_whitespace(reference_text)
    hypothesis = normalize_whitespace(ocr_text)
    character_counts = levenshtein_counts(reference, hypothesis)
    reference_words = reference.split() if reference else []
    hypothesis_words = hypothesis.split() if hypothesis else []
    word_counts = levenshtein_counts(reference_words, hypothesis_words)
    return (
        character_counts,
        rate(character_counts, len(reference)),
        word_counts,
        rate(word_counts, len(reference_words)),
        len(reference),
        len(reference_words),
    )


def format_rate(value: float) -> str:
    return f"{value:.6f}".replace(".", ",")


def markdown_row(reference_path: Path, ocr_path: Path, results: tuple) -> str:
    character_counts, cer, word_counts, wer, reference_characters, reference_words = results
    operations = f"{character_counts.substitutions} / {character_counts.deletions} / {character_counts.insertions}"
    return (
        f"| À renseigner | À relever | `{reference_path.name}` | `{ocr_path.name}` | "
        f"{operations} | {format_rate(cer)} ({reference_characters} caractères) | "
        f"{format_rate(wer)} ({reference_words} mots) | À renseigner |"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculer le CER et le WER entre une transcription et un OCR.")
    parser.add_argument("transcription_reference", type=Path, help="Fichier de transcription de référence")
    parser.add_argument("ocr_brut", type=Path, help="Fichier de texte OCR brut")
    args = parser.parse_args()
    reference = args.transcription_reference.read_text(encoding="utf-8")
    ocr = args.ocr_brut.read_text(encoding="utf-8")
    results = evaluate(reference, ocr)
    print("| Page source | Articles repérés | Transcription de référence | OCR brut comparé | Substitutions / suppressions / insertions | CER | WER | Vérificateur et date |")
    print("|---|---|---|---|---|---:|---:|---|")
    print(markdown_row(args.transcription_reference, args.ocr_brut, results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
