"""Week 2 - OCR of a scanned PDF (two-column Arabic JO page, or French one-column page).

Why columns: the Arabic Journal officiel has 2 columns. OCR on the whole page mixes the lines of both
columns, so we cut each page in two halves and read the RIGHT column first (Arabic reads right-to-left).

Needs (outside pip): Tesseract with the language data  (ara = Arabic, fra = French)
    Windows: install Tesseract (UB Mannheim build), tick the Arabic + French languages, add it to PATH.
    Linux:   apt install tesseract-ocr tesseract-ocr-ara tesseract-ocr-fra
    pip install pymupdf pillow

Usage:
    python src/structuring/ocr_pdf.py <file.pdf> <out.txt> --lang ara --columns 2
    python src/structuring/ocr_pdf.py <file.pdf> <out.txt> --lang fra --columns 1
"""
import argparse
import io
import subprocess
import tempfile
from pathlib import Path

import pymupdf
from PIL import Image


def ocr_image(img: Image.Image, lang: str, psm: int) -> str:
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "page.png"
        img.save(src)
        res = subprocess.run(["tesseract", str(src), "stdout", "-l", lang, "--psm", str(psm)],
                             capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            raise RuntimeError(res.stderr)
        return res.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("out")
    ap.add_argument("--lang", default="ara")
    ap.add_argument("--columns", type=int, choices=(1, 2), default=2)
    ap.add_argument("--dpi", type=int, default=250)
    ap.add_argument("--first", type=int, default=1); ap.add_argument("--last", type=int, default=0)
    a = ap.parse_args()
    doc = pymupdf.open(a.pdf)
    last = a.last or len(doc)
    texts = []
    for i in range(a.first - 1, last):
        pix = doc[i].get_pixmap(dpi=a.dpi, colorspace=pymupdf.csGRAY)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        w, h = img.size
        if a.columns == 2:
            halves = [img.crop((w // 2 - 10, 0, w, h)), img.crop((0, 0, w // 2 + 10, h))]   # right column first
            if a.lang != "ara":
                halves.reverse()                                                          # left-to-right languages
            texts += [ocr_image(x, a.lang, 4) for x in halves]
        else:
            texts.append(ocr_image(img, a.lang, 6))
        print(f"page {i + 1}/{last} done")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(texts), encoding="utf-8")
    print(f"Saved {a.out}")


if __name__ == "__main__":
    main()
