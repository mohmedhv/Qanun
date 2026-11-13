"""Step 2 - Split the raw text of law 90-11 into articles.

Key rule: a line "Art. N.-" is accepted as a real article start ONLY if N is
exactly the expected next number (last accepted + 1). This rejects the
"Art. 2.-", "Art. 45.-" ... that belong to the amending laws quoted in the
"Evolution" blocks, and references such as "Art. 8. Toutes dispositions...".

Usage:  python src/structuring/splitter.py
Reads:  data/raw/loi_90_11.txt
Writes: data/interim/articles.json         (the clean articles)
        data/interim/evolution_blocks.json (amendment commentary, for P3)
"""
import json
import re
from pathlib import Path

RAW = Path("data/raw/loi_90_11.txt")
OUT_ARTICLES = Path("data/interim/articles.json")
OUT_EVOLUTION = Path("data/interim/evolution_blocks.json")

# "Art. 33.-", "Art. 45. –", "Article 1er.-"  (optional bis/ter/quater)
ARTICLE_START = re.compile(
    r"^\s*(?:Art\.|Article)\s+(\d+)\s*(?:er)?\s*(bis|ter|quater)?\s*[.\-–—]+\s*(.*)$",
    re.IGNORECASE,
)
TITLE = re.compile(r"^\s*TITRE\s+([IVXLC]+)\s*:?\s*(.*)$")
CHAPTER = re.compile(r"^\s*Chapitre\s+([IVXLC]+)\s*:?\s*(.*)$")
SECTION = re.compile(r"^\s*Section\s+(\d+)\s*:?\s*(.*)$")
PAGE_NUMBER = re.compile(r"^\s*\d{1,3}\s*$")          # a line holding only a page number
# Markers that close an article's text (the site's annotation buttons)
MARKER = re.compile(r"\b(Evolution|Textes d’application|Consulter aussi|Version consolidée|Rectificatif)\b")
FULL_LINE = 115   # a physical line shorter than this was not wrapped (PDF lines are ~125-140 chars)


def clean_line(line: str) -> str:
    line = line.replace("­", "").replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", line).strip()


def join_paragraphs(lines: list[str]) -> list[str]:
    """Physical lines (wrapped by the PDF) -> list of paragraphs (alineas).
    A new paragraph starts when the previous physical line ended a sentence
    (. : ;) AND was clearly shorter than a full line (so it was not wrapped),
    or when the line is a list item ("- ...", "1) ...")."""
    paragraphs: list[str] = []
    last_len = 0                       # length of the previous physical line
    for line in lines:
        starts_new = (
            not paragraphs
            or re.match(r"^[–\-•]\s", line)
            or re.match(r"^\d+[°)]\s", line)
            or (re.search(r"[.:;]$", paragraphs[-1]) and last_len < FULL_LINE and line[:1].isupper())
        )
        if starts_new:
            paragraphs.append(line)
        else:
            prev = paragraphs[-1]
            if re.search(r"[a-zà-ÿ]-$", prev) and line[:1].islower():
                paragraphs[-1] = prev[:-1] + line          # hyphenated word at line end
            else:
                paragraphs[-1] = prev + " " + line
        last_len = len(line)
    return paragraphs


def split(raw: str):
    articles, evolutions = [], []
    title = chapter = section = None
    expected = 1
    current = None            # article being built
    in_annotation = False

    def close_current():
        nonlocal current
        if current:
            current["paragraphs"] = join_paragraphs(current.pop("_lines"))
            current["content"] = "\n".join(current["paragraphs"])
            articles.append(current)
            current = None

    for original in raw.splitlines():
        line = clean_line(original)
        if not line or PAGE_NUMBER.match(line):
            continue

        # 1) headings (only in the main text, they reset lower levels)
        m = TITLE.match(line)
        if m and not (in_annotation and expected > 1 and False):
            close_current(); in_annotation = False
            title, chapter, section = f"TITRE {m[1]} : {m[2]}".strip(" :"), None, None
            continue
        m = CHAPTER.match(line)
        if m:
            close_current(); in_annotation = False
            chapter, section = f"Chapitre {m[1]} : {m[2]}".strip(" :"), None
            continue
        m = SECTION.match(line)
        if m:
            close_current(); in_annotation = False
            section = f"Section {m[1]} : {m[2]}".strip(" :")
            continue

        # 2) a real article start? (must be the expected number)
        m = ARTICLE_START.match(line)
        if m and int(m[1]) == expected and not m[2]:
            close_current(); in_annotation = False
            current = {
                "number": str(expected), "sort_key": expected, "suffix": None,
                "parent_title": title, "parent_chapter": chapter, "parent_section": section,
                "_lines": [],
            }
            expected += 1
            line = m[3].strip()
            if not line:
                continue

        if current is None:
            continue                                   # preamble ("Vu la Constitution...")

        # 3) annotation blocks
        if in_annotation:
            evolutions[-1]["text"].append(line)
            continue
        mk = MARKER.search(line)
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
    return articles, evolutions


def main():
    raw = RAW.read_text(encoding="utf-8")
    articles, evolutions = split(raw)
    OUT_ARTICLES.parent.mkdir(parents=True, exist_ok=True)
    OUT_ARTICLES.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_EVOLUTION.write_text(json.dumps(evolutions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(articles)} articles, {len(evolutions)} evolution blocks")


if __name__ == "__main__":
    main()
