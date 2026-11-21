#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    raise SystemExit("PyMuPDF absent. Installez-le : python -m pip install pymupdf")

HEADERS = [
    "pdf_filename", "page_count", "pages_with_extractable_text",
    "text_characters", "text_extraction_status", "sample_first_page",
    "manual_review", "observed_problems", "ocr_needed", "notes"
]


def examine(path):
    try:
        with fitz.open(path) as doc:
            pages = len(doc)
            lengths = []
            sample = ""
            for i, page in enumerate(doc):
                extracted = page.get_text("text") or ""
                cleaned = extracted.strip()
                lengths.append(len(cleaned))
                if i == 0:
                    sample = " ".join(cleaned.split())[:180]
            present = sum(n >= 100 for n in lengths)
            total = sum(lengths)
            if pages == 0:
                status = "empty_pdf"
            elif present == 0:
                status = "no_substantial_text_detected"
            elif present == pages:
                status = "text_detected_all_pages"
            else:
                status = "mixed_or_low_text_pages"
            return [path.name, pages, present, total, status, sample,
                    "pending", "", "to_be_determined", "Inspect page layout and article numbering manually"]
    except Exception as exc:
        return [path.name, "", "", "", "read_error", "", "pending",
                str(exc), "to_be_determined", "Check whether the file is corrupt or protected"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default="data/raw_pdfs", help="Dossier des PDF fournis par P1")
    parser.add_argument("--output", default="pdf_quality_report.csv", help="Rapport CSV de sortie")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    folder = Path(args.folder)
    if not folder.is_absolute():
        folder = base / folder
    output = Path(args.output)
    if not output.is_absolute():
        output = base / output

    if not folder.is_dir():
        print(f"Dossier inexistant : {folder}. Créez-le et ajoutez les PDF de P1.")
        return 1
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
    if not files:
        print(f"Aucun PDF dans {folder}. Aucun résultat n'a été inventé.")
        print("Placez ici 2 à 3 PDF du Journal officiel reçus de P1, puis relancez.")
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        for file in files:
            row = examine(file)
            writer.writerow(row)
            print(f"{file.name}: {row[4]} ({row[2]}/{row[1]} pages avec >=100 caractères)")
    print(f"Rapport : {output}")
    print("Complétez manuellement les colonnes manual_review, observed_problems et ocr_needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
