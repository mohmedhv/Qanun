"""OCR scanned Journal officiel PDFs (Tesseract, French).

For every selected page: if the PDF already has a text layer (>= MIN_CHARS characters) it is used as is,
otherwise the page is rendered to an image and read with Tesseract. Each page is saved in its own file, so
a second run skips pages already done (replayable, and you can stop and restart).

Examples (run from the repo root, inside the Python 3.11 environment):
  python -m src.collect.ocr data/raw_pdf/F1990017.pdf --pages 1-3        # quick quality test
  python -m src.collect.ocr data/raw_pdf/F1990017.pdf --pages 12-20      # the pages with Law 90-11
  python -m src.collect.ocr data/raw_pdf/F1990017.pdf                    # whole issue (slow)

Output: data/processed/ocr/<pdf name>/page_001.txt ... and data/processed/ocr/<pdf name>.txt (all pages,
with '=== page N (...) ===' markers) and <pdf name>_quality.csv (characters and Tesseract confidence per page).
"""
from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import pymupdf  # PyMuPDF (new name)
except ImportError:  # older PyMuPDF
    import fitz as pymupdf

# Tesseract is called as a program (no pytesseract, no pandas): some Windows security policies block pandas.

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "processed" / "ocr"
MIN_CHARS = 50
WINDOWS_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


TESSERACT = "tesseract"


def configure_tesseract(lang: str) -> None:
    """Find the tesseract program (TESSERACT_CMD, PATH, default Windows folder) and check the language."""
    global TESSERACT
    cmd = os.getenv("TESSERACT_CMD") or shutil.which("tesseract")
    if not cmd and Path(WINDOWS_TESSERACT).exists():
        cmd = WINDOWS_TESSERACT
    if not cmd:
        sys.exit("Tesseract not found. Install it (with the French language) or set TESSERACT_CMD to its path.")
    TESSERACT = cmd
    result = subprocess.run([TESSERACT, "--list-langs"], capture_output=True, text=True)
    lines = (result.stdout + "\n" + result.stderr).splitlines()
    available = [x.strip() for x in lines if x.strip() and not x.startswith("List of")]
    if lang not in available:
        sys.exit(f"Language '{lang}' is missing in Tesseract (found: {available}). "
                 "Re-run its installer and tick French, or copy fra.traineddata into its tessdata folder.")


def parse_pages(spec: str | None, total: int) -> list[int]:
    """'3', '1-5' or '1-3,8,10-12' (1-based) -> list of page numbers; None -> all pages."""
    if not spec:
        return list(range(1, total + 1))
    pages: list[int] = []
    for part in spec.split(","):
        a, _, b = part.strip().partition("-")
        pages.extend(range(int(a), int(b or a) + 1))
    bad = [p for p in pages if not 1 <= p <= total]
    if bad:
        sys.exit(f"Pages out of range (the PDF has {total} pages): {bad}")
    return pages


def run_tesseract(pix, lang: str, psm: int) -> tuple[str, list[float]]:
    """OCR one pixmap with the tesseract program; return (text, word confidences)."""
    with tempfile.TemporaryDirectory() as tmp:
        image = Path(tmp) / "page.png"
        pix.save(str(image))
        base = Path(tmp) / "out"
        # One run, two outputs: out.txt (text) and out.tsv (word confidences).
        run = subprocess.run([TESSERACT, str(image), str(base), "-l", lang, "--psm", str(psm), "txt", "tsv"],
                             capture_output=True, text=True)
        if run.returncode != 0 or not base.with_suffix(".txt").exists():
            raise RuntimeError(f"Tesseract failed: {run.stderr.strip()[:300]}")
        text = base.with_suffix(".txt").read_text(encoding="utf-8").strip()
        confidences = []
        with base.with_suffix(".tsv").open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE):
                try:
                    conf = float(row["conf"])
                except (KeyError, TypeError, ValueError):
                    continue
                if conf >= 0 and (row.get("text") or "").strip():
                    confidences.append(conf)
    return text, confidences


def ocr_page(page, dpi: int, lang: str, psm: int, columns: int) -> tuple[str, float | None, str]:
    """Return (text, mean confidence 0-100 or None, method).

    columns=1: the whole page is read at once (psm 3 lets Tesseract detect columns itself).
    columns=2: the page is cut into a left and a right half, each read on its own, left first.
    """
    layer = page.get_text().strip()
    if len(layer) >= MIN_CHARS:
        return layer, None, "text-layer"
    rect = page.rect
    if columns <= 1:
        pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
        text, confidences = run_tesseract(pix, lang, psm)
        method = f"ocr-psm{psm}"
    else:
        width = rect.width / columns
        parts, confidences = [], []
        for i in range(columns):
            clip = pymupdf.Rect(rect.x0 + i * width, rect.y0, rect.x0 + (i + 1) * width, rect.y1)
            pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, clip=clip)
            part, conf = run_tesseract(pix, lang, psm)
            parts.append(part)
            confidences += conf
        text = "\n\n".join(parts)
        method = f"ocr-{columns}col-psm{psm}"
    confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0.0
    return text, confidence, method


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--pages", help="for example 1-3 or 12-20,25 (default: all)")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--lang", default="fra")
    ap.add_argument("--psm", type=int, default=None,
                    help="Tesseract page segmentation. Default: 3 (automatic, detects columns) with --columns 1, "
                         "6 (one block) with --columns 2. 6 on a whole two-column page mixes the columns.")
    ap.add_argument("--columns", type=int, default=1, choices=[1, 2, 3],
                    help="number of text columns on the page. 2 = cut the page in two halves and read left, then right "
                         "(use it when the automatic mode still mixes the columns). Titles that span the whole page get cut.")
    ap.add_argument("--redo", action="store_true", help="ignore pages already done")
    args = ap.parse_args()

    configure_tesseract(args.lang)
    psm = args.psm if args.psm is not None else (3 if args.columns == 1 else 6)
    stem = args.pdf.stem
    page_dir = OUT_DIR / stem
    page_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(args.pdf)
    pages = parse_pages(args.pages, len(doc))
    print(f"{args.pdf.name}: {len(doc)} pages, processing {len(pages)}")

    for n in pages:
        target = page_dir / f"page_{n:03d}.txt"
        meta = page_dir / f"page_{n:03d}.meta"
        if target.exists() and meta.exists() and not args.redo:
            print(f"  page {n}: skipped (already done)")
            continue
        text, confidence, method = ocr_page(doc[n - 1], args.dpi, args.lang, psm, args.columns)
        target.write_text(text, encoding="utf-8")
        meta.write_text(f"{method},{'' if confidence is None else confidence}", encoding="utf-8")
        shown = "" if confidence is None else f", confidence {confidence}"
        print(f"  page {n}: {method}, {len(text)} characters{shown}")

    # Merge every page done so far (in order) into one file, and write the quality report.
    rows = []
    with (OUT_DIR / f"{stem}.txt").open("w", encoding="utf-8") as merged:
        for target in sorted(page_dir.glob("page_*.txt")):
            n = int(target.stem.split("_")[1])
            method, confidence = (page_dir / f"page_{n:03d}.meta").read_text(encoding="utf-8").split(",")
            text = target.read_text(encoding="utf-8")
            merged.write(f"=== page {n} ({method}) ===\n{text}\n\n")
            rows.append({"page": n, "method": method, "characters": len(text), "confidence": confidence})
    with (OUT_DIR / f"{stem}_quality.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["page", "method", "characters", "confidence"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT_DIR / (stem + '.txt')} and {stem}_quality.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())