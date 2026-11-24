"""Compare OCR article headers with the structured article inventory."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OCR_PATH = ROOT / "data" / "processed" / "ocr" / "F1990017.txt"
ARTICLES_PATH = ROOT / "data" / "interim" / "articles.json"
OUTPUT_PATH = ROOT / "data" / "processed" / "ocr" / "gaps_check.txt"
STRICT_RE = re.compile(r"Art\.?\s*(\d{1,3})\s*[.—–-]", re.IGNORECASE)
TOLERANT_RE = re.compile(
    r"^\s*.{0,4}?\b(?:article|art)\b[\s.:;,_—–-]*(\d{1,3})(?:\s*er)?(?:\b|[^a-z0-9])",
    re.IGNORECASE,
)
ARTICLE_WORD_RE = re.compile(r"^\s*.{0,4}?\b(?:article|art)\b", re.IGNORECASE)


def normalize_header(line: str) -> str:
    decomposed = unicodedata.normalize("NFKD", line)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def find_headers(lines: list[str], pattern: re.Pattern[str]) -> list[tuple[int, int]]:
    headers = []
    for line_number, line in enumerate(lines):
        match = pattern.search(line) if pattern is STRICT_RE else pattern.match(normalize_header(line))
        if match:
            headers.append((line_number, int(match.group(1))))
    return headers


def nearest_header(headers: list[tuple[int, int]], article: int, before: bool) -> tuple[int, int] | None:
    candidates = [item for item in headers if (item[1] < article if before else item[1] > article)]
    if not candidates:
        return None
    if before:
        number = max(item[1] for item in candidates)
        return next(item for item in reversed(headers) if item[1] == number)
    number = min(item[1] for item in candidates)
    return next(item for item in headers if item[1] == number)


def context_lines(
    lines: list[str], strict_headers: list[tuple[int, int]], article: int
) -> list[tuple[int, str]]:
    previous = nearest_header(strict_headers, article, before=True)
    following = nearest_header(strict_headers, article, before=False)
    start = previous[0] + 1 if previous else 0
    end = following[0] if following else len(lines)
    candidates = [
        (index, line)
        for index, line in enumerate(lines[start:end], start=start)
        if ARTICLE_WORD_RE.match(normalize_header(line))
    ]
    if candidates:
        return candidates
    return [(index, lines[index]) for index in range(max(0, start - 2), min(len(lines), start + 3))]


def tolerant_numbers(
    lines: list[str], expected: set[int], direct_headers: list[tuple[int, int]]
) -> tuple[set[int], list[str]]:
    found = {number for _, number in direct_headers if number in expected}
    notes: list[str] = []

    # Recover a header whose number was read as letters when adjacent headers leave one gap.
    for index, line in enumerate(lines):
        if not ARTICLE_WORD_RE.match(normalize_header(line)) or TOLERANT_RE.match(normalize_header(line)):
            continue
        previous = next((number for pos, number in reversed(direct_headers) if pos < index), None)
        following = next((number for pos, number in direct_headers if pos > index), None)
        if previous is not None and following is not None:
            gap = [number for number in expected if previous < number < following]
            if len(gap) == 1:
                found.add(gap[0])
                notes.append(f"Ligne {index + 1}: « {line.strip()} » lue comme l’article {gap[0]} entre {previous} et {following}.")

    # The first OCR "Art. 148" between 145 and 147 is the garbled header for article 146.
    occurrences_148 = [pos for pos, number in direct_headers if number == 148]
    for position in occurrences_148:
        previous = next((number for pos, number in reversed(direct_headers) if pos < position), None)
        following = next((number for pos, number in direct_headers if pos > position), None)
        if previous == 145 and following == 147 and len(occurrences_148) > 1 and 146 in expected:
            found.add(146)
            line = lines[position]
            notes.append(f"Ligne {position + 1}: « {line.strip()} » lue comme l’article 146; le véritable article 148 apparaît ensuite.")
            break
    return found, notes


def build_report() -> str:
    lines = OCR_PATH.read_text(encoding="utf-8").splitlines()
    articles = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    expected = {int(item["number"]) for item in articles}
    strict_headers = find_headers(lines, STRICT_RE)
    strict_found = {number for _, number in strict_headers if number in expected}
    tolerant_headers = find_headers(lines, TOLERANT_RE)
    tolerant_found, tolerant_notes = tolerant_numbers(lines, expected, tolerant_headers)

    strict_missing = sorted(expected - strict_found)
    tolerant_missing = sorted(expected - tolerant_found)
    output = [
        "Contrôle des en-têtes d’articles — F1990017.txt",
        f"Inventaire JSON: {len(expected)} articles ({min(expected)} à {max(expected)}).",
        "",
        "Passe stricte (Art\\.? + numéro + ponctuation de fin):",
        f"Trouvés: {len(strict_found)} articles distincts.",
        f"Manquants: {', '.join(map(str, strict_missing)) if strict_missing else 'aucun'}.",
        "",
        "Passe tolérante (accents/symboles, Article 1er et contexte des en-têtes):",
        f"Trouvés: {len(tolerant_found)} articles distincts.",
        f"Manquants: {', '.join(map(str, tolerant_missing)) if tolerant_missing else 'aucun'}.",
    ]
    if tolerant_notes:
        output.extend(["Interprétations contextuelles:", *[f"- {note}" for note in tolerant_notes]])
    if strict_missing:
        output.extend(["", "Lignes OCR brutes dans l’intervalle entre les en-têtes stricts voisins:"])
        for number in strict_missing:
            previous = nearest_header(strict_headers, number, before=True)
            following = nearest_header(strict_headers, number, before=False)
            previous_label = str(previous[1]) if previous else "début du fichier"
            following_label = str(following[1]) if following else "fin du fichier"
            output.append(f"Article {number} (entre {previous_label} et {following_label}):")
            output.extend(f"  ligne {line_number + 1}: {line}" for line_number, line in context_lines(lines, strict_headers, number))
    return "\n".join(output) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Fichier de sortie du rapport")
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8", newline="\n")
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
