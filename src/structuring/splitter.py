"""Split the raw text of law 90-11 into articles (French clean text, French/Arabic OCR text).

KEY RULE: a line "Art. N.-" is accepted as a real article start ONLY if N is the expected next
number. This rejects the "Art. 2.-", "Art. 45.-" ... that belong to the amending laws quoted in the
"Evolution" blocks, and references such as "Art. 8. Toutes dispositions...".

WEEK 2: the same code also works on NOISY text (OCR of a scanned PDF) and on Arabic:
  --max-gap N   noisy mode: accept a number up to N ahead of the expected one, so that an OCR miss
                no longer blocks everything after it. The skipped numbers are reported as MISSING.
                Default 0 = strict mode (clean text) = exactly the Week 1 behaviour.
  --lang fr|ar  French (default) or Arabic patterns.

Usage (French, clean):  python src/structuring/splitter.py
Usage (Arabic, OCR):    python src/structuring/splitter.py --lang ar --max-gap 3 \
                            --input data/raw/loi_90_11_ar_ocr.txt --out data/interim/articles_ar.json
Default reads data/raw/loi_90_11.txt and writes:
    data/interim/articles.json          (the clean articles)
    data/interim/evolution_blocks.json  (amendment commentary, for P3; French only)
"""
import argparse
import json
import re
from pathlib import Path

FULL_LINE = 115   # a physical line shorter than this was not wrapped (PDF lines are ~125-140 chars)
PAGE_NUMBER = re.compile(r"^\s*\d{1,3}\s*$")          # a line holding only a page number

PROFILES = {
    "fr": {
        # "Art. 33.-", "Art. 45. –", "Article 1er.-"  (optional bis/ter/quater)
        "article": re.compile(r"^\s*(?:Art\.|Article)\s+(?P<num>\d+)\s*(?:er)?\s*(?P<suffix>bis|ter|quater)?\s*[.\-–—]+\s*(?P<rest>.*)$", re.I),
        "title": re.compile(r"^\s*TITRE\s+(?P<n>[IVXLC]+)\s*:?\s*(?P<t>.*)$"),
        "chapter": re.compile(r"^\s*Chapitre\s+(?P<n>[IVXLC]+)\s*:?\s*(?P<t>.*)$"),
        "section": re.compile(r"^\s*Section\s+(?P<n>\d+)\s*:?\s*(?P<t>.*)$"),
        "labels": ("TITRE", "Chapitre", "Section"),
        # buttons of the annotated site that close an article's text
        "marker": re.compile(r"\b(Evolution|Textes d’application|Consulter aussi|Version consolidée|Rectificatif)\b"),
        "noise": None,
        "has_case": True,
    },
    "ar": {
        # OCR often turns "المادة" into "الملدة" or "الماية": tolerate it. Article 1 is written "الأولى".
        "article": re.compile(r"^\W{0,3}ال[مل][ا-ي]{1,3}\s*(?P<num>\d{1,3}|الأولى|الاولى)\s*(?P<suffix>)[:：.\-–—]+\s*(?P<rest>.*)$"),
        "title": re.compile(r"^\W{0,3}(?P<n>الباب)\s+(?P<t>.*)$"),
        "chapter": re.compile(r"^\W{0,3}(?P<n>الفصل)\s+(?P<t>.*)$"),
        "section": re.compile(r"^\W{0,3}(?P<n>الفرع)\s+(?P<t>.*)$"),
        "labels": ("الباب", "الفصل", "الفرع"),
        "marker": None,
        "noise": re.compile(r"الجريدة الرسمية|العدد\s*\d+|^\W*\d+\s*(?:ه|هـ)?\W*$"),   # running page header
        "has_case": False,
    },
}


def clean_line(line: str) -> str:
    line = line.replace("­", "").replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", line).strip()


def join_paragraphs(lines: list[str], has_case: bool = True) -> list[str]:
    """Physical lines (wrapped by the PDF) -> list of paragraphs (alineas).
    A new paragraph starts when the previous physical line ended a sentence (. : ;) AND was clearly
    shorter than a full line (so it was not wrapped), or when the line is a list item."""
    paragraphs: list[str] = []
    last_len = 0
    for line in lines:
        starts_new = (
            not paragraphs
            or re.match(r"^[–\-•]\s", line)
            or re.match(r"^\d+[°)]\s", line)
            or (has_case and re.search(r"[.:;]$", paragraphs[-1]) and last_len < FULL_LINE and line[:1].isupper())
        )
        if starts_new:
            paragraphs.append(line)
        else:
            prev = paragraphs[-1]
            if has_case and re.search(r"[a-zà-ÿ]-$", prev) and line[:1].islower():
                paragraphs[-1] = prev[:-1] + line          # hyphenated word at line end
            else:
                paragraphs[-1] = prev + " " + line
        last_len = len(line)
    return paragraphs


def split(raw: str, lang: str = "fr", max_gap: int = 0):
    """Returns (articles, evolution_blocks, missing_numbers)."""
    P = PROFILES[lang]
    articles, evolutions, missing = [], [], []
    title = chapter = section = None
    expected = 1
    current = None
    in_annotation = False

    def close_current():
        nonlocal current
        if current:
            current["paragraphs"] = join_paragraphs(current.pop("_lines"), P["has_case"])
            current["content"] = "\n".join(current["paragraphs"])
            articles.append(current)
            current = None

    def heading(kind, m):
        n, t = m.group("n"), m.group("t")
        label = P["labels"][("title", "chapter", "section").index(kind)]
        return f"{label} {n} : {t}".strip(" :") if lang == "fr" else f"{n} {t}".strip()

    for original in raw.splitlines():
        line = clean_line(original)
        if not line or PAGE_NUMBER.match(line) or (P["noise"] and P["noise"].search(line)):
            continue

        # 1) headings (they reset the lower levels)
        m = P["title"].match(line)
        if m:
            close_current(); in_annotation = False
            title, chapter, section = heading("title", m), None, None
            continue
        m = P["chapter"].match(line)
        if m:
            close_current(); in_annotation = False
            chapter, section = heading("chapter", m), None
            continue
        m = P["section"].match(line)
        if m:
            close_current(); in_annotation = False
            section = heading("section", m)
            continue

        # 2) a real article start? (the expected number; in noisy mode up to max_gap ahead)
        m = P["article"].match(line)
        if m and not m.group("suffix"):
            raw_num = m.group("num")
            n = int(raw_num) if raw_num.isdigit() else 1
            if expected <= n <= expected + max_gap:
                close_current(); in_annotation = False
                missing += list(range(expected, n))
                current = {
                    "number": str(n), "sort_key": n, "suffix": None,
                    "parent_title": title, "parent_chapter": chapter, "parent_section": section,
                    "_lines": [],
                }
                expected = n + 1
                line = m.group("rest").strip()
                if not line:
                    continue

        if current is None:
            continue                                   # preamble ("Vu la Constitution...")

        # 3) annotation blocks (annotated French copy only)
        if in_annotation:
            evolutions[-1]["text"].append(line)
            continue
        mk = P["marker"].search(line) if P["marker"] else None
        if mk:
            before = line[:mk.start()].strip()
            if before:
                current["_lines"].append(before)
            in_annotation = True
            evolutions.append({"article": str(current["sort_key"]), "text": [line[mk.start():]]})
            continue

        current["_lines"].append(line)

    close_current()
    for e in evolutions:
        e["text"] = "\n".join(e["text"])
    return articles, evolutions, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/raw/loi_90_11.txt")
    ap.add_argument("--out", default="data/interim/articles.json")
    ap.add_argument("--evolution-out", default="data/interim/evolution_blocks.json")
    ap.add_argument("--lang", choices=PROFILES, default="fr")
    ap.add_argument("--max-gap", type=int, default=0)
    a = ap.parse_args()
    raw = Path(a.input).read_text(encoding="utf-8")
    articles, evolutions, missing = split(raw, a.lang, a.max_gap)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.lang == "fr":
        Path(a.evolution_out).write_text(json.dumps(evolutions, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{len(articles)} articles, {len(evolutions)} evolution blocks")
    else:
        print(f"{len(articles)} articles found")
    if missing:
        print(f"MISSING (skipped by the gap rule): {missing}")


if __name__ == "__main__":
    main()
