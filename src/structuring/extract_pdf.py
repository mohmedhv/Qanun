"""Step 1 - Extract the raw text of the law from the PDF, page by page.
Usage (from the repo root):
    python src/structuring/extract_pdf.py path/to/loi_90-11_relations_de_travail.pdf
Output: data/raw/loi_90_11.txt   (never edit this file by hand)
"""
import sys
from pathlib import Path
import pymupdf  # PyMuPDF

def main(pdf_path: str) -> None:
    doc = pymupdf.open(pdf_path)
    pages = [page.get_text() for page in doc]
    chars = sum(len(p.strip()) for p in pages)
    print(f"{len(doc)} pages, {chars} characters extracted")
    if chars < 1000:
        print("WARNING: almost no text -> this PDF is a scan, it needs OCR.")
    out = Path("data/raw/loi_90_11.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(pages), encoding="utf-8")
    print(f"Saved to {out}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python src/structuring/extract_pdf.py <file.pdf>")
    main(sys.argv[1])
