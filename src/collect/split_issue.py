"""Split OCR text into records for individual legal texts."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OCR_DIR = ROOT / "data" / "processed" / "ocr"
TEXT_DIR = ROOT / "data" / "processed" / "texts"
REGISTRY = ROOT / "data" / "processed" / "download_registry.csv"

HEADER_RE = re.compile(
    r"^\s*(L[O0]I|ORDONNANCE|D[E3]CRET(?:\s+PRESIDENTIEL|\s+EXECUTIF|\s+LEGISLATIF)?|"
    r"ARR[E3]T[E3](?:\s+INTERMINISTERIEL)?|C[I1]RCULAIRE|DEC[I1]SION|AVIS|COMMUNICATION)\b",
    re.I,
)
BODY_RE = re.compile(
    r"^(?:le president|le premier ministre|le ministre|vu\b|art\.?\s*\d|article\s+\d|par\s+(?:decret|arrete))",
    re.I,
)
MONTHS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
}
PREFIXES = {
    "loi": ("loi", 2, "LOI"), "ordonnance": ("ordonnance", 2, "ORD"),
    "decret presidentiel": ("decret_presidentiel", 3, "DEC-PRES"),
    "decret executif": ("decret_executif", 3, "DEC-EXE"),
    "arrete": ("arrete", 4, "ARR"), "circulaire": ("circulaire", 5, "CIRC"),
}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", value).strip()


def header_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", value).strip()


def is_header(line: str, page_number: int) -> re.Match[str] | None:
    if page_number <= 1:
        return None
    if re.search(r"\.{5,}|…{2,}|\bp\.?\s*\d{2,4}\.?\s*$", line, re.I):
        return None
    normalized = header_text(line).replace("œ", "oe")
    match = HEADER_RE.match(normalized)
    if not match:
        return None
    if not match.group(1).isupper():
        return None
    if re.match(r"^art(?:icle)?\b", normalized, re.I):
        return None
    label = match.group(1).lower()
    tail = normalized[match.end():].strip()
    has_number = re.match(r"^n\s*[°º]\s*\d+\b", tail, re.I)
    has_object = re.search(
        r"\b(?:portant|relative?|relatif|relatives|relatifs|fixant|modifiant|completant|"
        r"instituant|creant|declarant|chargeant|ratifiant|abrogeant|nommant|prevoyant|"
        r"autorisant|determinant|approuvant|mettant|transférant|transferant)\b",
        norm(tail), re.I,
    )
    if not has_number and not has_object:
        return None
    if label in {"decret", "decision", "avis", "communication"} and (not tail or label.isupper()):
        return None
    if label == "decret" and not re.search(r"\b(?:n\s*[°o]|du\s+\d)", norm(tail)):
        return None
    return match


def classify(header: str) -> tuple[str, int, str]:
    normalized = norm(header).translate(str.maketrans({"0": "o", "1": "i", "3": "e"}))
    for prefix, values in PREFIXES.items():
        if normalized.startswith(prefix):
            return values
    return "autre", 5, "AUTRE"


def parse_date(text: str) -> str | None:
    normalized = norm(text)
    m = re.search(r"\bcorrespondant\s+au\s+(\d{1,2})(?:er)?\s+([a-z]+)\s+(\d{4})", normalized)
    if not m:
        m = re.search(r"\bdu\s+(\d{1,2})(?:er)?\s+([a-z]+)\s+(\d{4})", normalized)
    if not m or m.group(2) not in MONTHS:
        return None
    return f"{m.group(3)}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"


def read_registry(stem: str) -> dict[str, str]:
    import csv
    with REGISTRY.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("file") == f"{stem}.pdf":
                return row
    raise ValueError(f"No download registry row for {stem}.pdf")


def clean_lines(text: str) -> tuple[list[str], list[bool], list[int]]:
    lines, from_ocr, pages = [], [], []
    current_ocr = False
    current_page = 0
    for line in text.splitlines():
        marker = re.match(r"^=== page (\d+) \(([^)]+)\) ===$", line.strip())
        if marker:
            current_page = int(marker.group(1))
            current_ocr = marker.group(2).lower().startswith("ocr")
            continue
        normalized = norm(line)
        if ("journal officiel" in normalized or "republique algerienne" in normalized) and re.search(r"\bn\s*[°o]\s*\d", normalized):
            continue
        if re.fullmatch(r"\s*\d{1,4}\s*", line) and len(lines) and not lines[-1].strip():
            continue
        line = re.sub(r"^\s*\|\s*|\s*\|\s*$", "", line)
        lines.append(line)
        from_ocr.append(current_ocr)
        pages.append(current_page)
    return lines, from_ocr, pages


def split_text(stem: str) -> list[dict]:
    source = OCR_DIR / f"{stem}.txt"
    registry = read_registry(stem)
    lines, ocr_flags, page_numbers = clean_lines(source.read_text(encoding="utf-8"))
    starts = [(i, is_header(line, page_numbers[i])) for i, line in enumerate(lines)]
    starts = [(i, match) for i, match in starts if match]
    dotted_counts = Counter(
        page_numbers[i] for i, line in enumerate(lines)
        if re.search(r"\.{5,}|…{2,}", line)
    )
    toc_pages = {page for page, count in dotted_counts.items() if count >= 3}
    starts = [(i, match) for i, match in starts if page_numbers[i] not in toc_pages]
    records = []
    counters: Counter[tuple[str, str]] = Counter()
    used_ids: Counter[str] = Counter()
    jo_number = str(int(registry["number"]))
    for pos, (start, match) in enumerate(starts):
        stop = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        chunk_lines = lines[start:stop]
        while chunk_lines and not chunk_lines[-1].strip():
            chunk_lines.pop()
        header = match.group(1)
        kind, rank, code = classify(header)
        chunk = "\n".join(chunk_lines).strip()
        # Exclude all-caps section labels without a date or identifying number.
        if header.upper() in {"DECRETS", "DECISIONS", "AVIS", "COMMUNICATIONS"}:
            continue
        if re.search(r"\.{5,}|…{2,}", chunk_lines[0]):
            continue
        title_lines = []
        for line in chunk_lines:
            if title_lines and BODY_RE.match(norm(line).lstrip("| ._")):
                break
            title_lines.append(line)
        title = re.sub(r"\s+", " ", " ".join(title_lines)).strip(" |")
        number_match = re.search(r"\bn\s*[°º]\s*(\d[A-Z0-9./-]*)", norm(chunk_lines[0]), re.I)
        number = number_match.group(1) if number_match else None
        date = parse_date(title)
        # Keep body text intact apart from explicitly requested marker/header/edge cleanup.
        raw_text = chunk
        key = (code, date or jo_number)
        counters[key] += 1
        if number:
            safe_number = number.replace("/", "-").replace("\\", "-")
            text_id = f"{code}-{safe_number}"
        else:
            text_id = f"{code}-{date or jo_number}-{counters[key]}"
        used_ids[text_id] += 1
        if used_ids[text_id] > 1:
            text_id += f"-{used_ids[text_id]}"
        records.append({
            "text_id": text_id, "type": kind, "number": number, "title": title,
            "date_signed": date, "jo_number": jo_number, "jo_date": None, "language": "fr",
            "rank_level": rank, "source_url": registry.get("url"),
            "pdf_path": f"data/raw_pdf/{stem}.pdf",
            "ocr_used": any(ocr_flags[start:stop]), "raw_text": raw_text,
        })
    return records


def write_issue(stem: str) -> list[dict]:
    records = split_text(stem)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    existing = []
    for path in TEXT_DIR.glob("*.json"):
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        existing.append((path, old))
    own_ids: set[str] = set()
    for record in records:
        own = next((old for _, old in existing
                    if old.get("pdf_path") == f"data/raw_pdf/{stem}.pdf"
                    and old.get("raw_text") == record["raw_text"]
                    and old.get("type") == record["type"]
                    and (old.get("text_id") == record["text_id"]
                         or old.get("text_id", "").startswith(record["text_id"] + "-"))
                    and old.get("text_id") not in own_ids), None)
        if own:
            record["text_id"] = own["text_id"]
            own_ids.add(record["text_id"])
            continue
        target = TEXT_DIR / f"{record['text_id']}.json"
        occupied = next((old for path, old in existing if path == target), None)
        if occupied and occupied.get("pdf_path") != f"data/raw_pdf/{stem}.pdf":
            base_id = record["text_id"]
            suffix = 2
            while True:
                candidate = f"{base_id}-{suffix}"
                candidate_path = TEXT_DIR / f"{candidate}.json"
                existing_candidate = next((old for path, old in existing if path == candidate_path), None)
                if existing_candidate is None:
                    record["text_id"] = candidate
                    break
                suffix += 1
    active_ids = {record["text_id"] for record in records}
    for path in TEXT_DIR.glob("*.json"):
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if old.get("pdf_path") == f"data/raw_pdf/{stem}.pdf" and old.get("text_id") not in active_ids:
            path.unlink()
    for record in records:
        (TEXT_DIR / f"{record['text_id']}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    counts = Counter(r["type"] for r in records)
    print(f"{stem}: {len(records)} texts; by type: {dict(counts)}")
    print(f"Missing number: {sum(r['number'] is None for r in records)}; missing date_signed: {sum(r['date_signed'] is None for r in records)}")
    print("IDs: " + ", ".join(r["text_id"] for r in records))
    import re
    ocr_text = (OCR_DIR / f"{stem}.txt").read_text(encoding="utf-8")
    pages = {int(n) for n in re.findall(r"^=== page (\d+) \(", ocr_text, re.M)}
    pdf_path = ROOT / "data" / "raw_pdf" / f"{stem}.pdf"
    if pdf_path.exists():
        import fitz
        pdf_pages = len(fitz.open(pdf_path))
        if pages != set(range(1, pdf_pages + 1)) and pages and records:
            page_range = f"p{min(pages)}-p{max(pages)}"
            print(f"Possibly incomplete (OCR range {page_range}): {records[0]['text_id']}, {records[-1]['text_id']}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stem", required=True)
    args = parser.parse_args()
    write_issue(args.stem)


if __name__ == "__main__":
    main()
