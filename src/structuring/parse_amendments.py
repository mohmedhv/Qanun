"""Week 2 - Parse the modifying texts ("Evolution" blocks) of law 90-11.

Each amending text says things like:
    "Art. 6.- L'article 42 de la loi n° 90-11 ... est modifié et rédigé comme suit :
     » Art. 42.- <new text> « ."
This script extracts, for every target article: the action (modify / complete /
insert / repeal / term_substitution), the modifying text (type, number, dates,
JO), and the NEW CONTENT. It hands the result to P3 (who builds version records).

Usage:  python src/structuring/parse_amendments.py
Reads:  data/interim/evolution_blocks.json   (made by splitter.py)
Writes: data/interim/amendments.json  and  data/interim/amendments.csv

HONESTY RULES
- We never invent a full article text. For "complete" actions the new content is only
  the added paragraph(s) (partial=True): P3 builds the full text of the version.
- date_signed / jo_date are what the text says. The ENTRY INTO FORCE date is NOT
  extracted here (it is not the same thing): P3 decides it from the official text.
- Every record is flagged needs_review when the regex was not sure.
"""
import csv
import json
import re
import unicodedata
from pathlib import Path

IN = Path("data/interim/evolution_blocks.json")
OUT_JSON = Path("data/interim/amendments.json")
OUT_CSV = Path("data/interim/amendments.csv")
MAX_ARTICLE = 158

MONTHS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
          "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12}

# ---- 1. headers of modifying texts ---------------------------------------------------------
HEADER = re.compile(
    r"(?P<type>Loi|Ordonnance|Décret\s+législatif|Décret\s+exécutif|Décret\s+présidentiel|Décret|Arrêté[^\n]{0,30}?)"
    r"\s+n°\s*(?P<num>\d{2,4}\s*-\s*\d+)\s+du\s+"
    r"(?P<body>(?:(?!\bArt\.|\bArticle\b).){0,420}?)\(page\s*\d+\)"
    r"(?P<tail>.{0,160}?)\(Publié\s+dans\s+JO\s+n°\s*(?P<jo>\d+)\s+du\s+(?P<jodate>\d{2}/\d{2}/\d{4})",
    re.DOTALL,
)
# Style 2 (finance laws quoted by the site): "Art 99 de la loi n° 17-11 du ... portant loi de finances pour 2018. JORA n° 76 du 28/12/2017"
HEADER2 = re.compile(
    r"Art\.?\s*(?P<art>\d+)\s+de\s+l[ae]\s+(?P<type>loi|ordonnance)\s+n°\s*(?P<num>\d{2,4}\s*-\s*\d+)\s+du\s+"
    r"(?P<body>.{0,300}?)JORA\s+n°\s*(?P<jo>\d+)\s+du\s+(?P<jodate>\d{2}/\d{2}/\d{4})",
    re.DOTALL | re.IGNORECASE,
)
DATE_FR = re.compile(r"(\d{1,2})(?:er)?\s+([A-Za-zéèêûôîàç]+)\s+(\d{4})")


def iso_date(text: str):
    """Gregorian date in the text: prefer the part after 'correspondant au'."""
    part = text.split("correspondant au", 1)[1] if "correspondant au" in text else text
    m = DATE_FR.search(part)
    if m and m[2].lower() in MONTHS:
        return f"{int(m[3]):04d}-{MONTHS[m[2].lower()]:02d}-{int(m[1]):02d}"
    return None


def find_headers(text: str):
    heads = []
    for m in HEADER.finditer(text):
        typ = re.sub(r"\s+", " ", m["type"]).strip()
        num = re.sub(r"\s+", "", m["num"])
        title = re.sub(r"\s+", " ", m["body"]).strip(" .")
        d = m["jodate"].split("/")
        heads.append({
            "pos": m.start(),
            "type": typ,
            "number": num,
            "modifying_text_id": re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", f"{typ}-{num}".lower()).encode("ascii", "ignore").decode()).strip("-"),
            "title": title[:300],
            "date_signed": iso_date(m["body"]),
            "jo_number": m["jo"],
            "jo_date": f"{d[2]}-{d[1]}-{d[0]}",
        })
    for m in HEADER2.finditer(text):
        typ = m["type"].capitalize()
        num = re.sub(r"\s+", "", m["num"])
        d = m["jodate"].split("/")
        heads.append({
            "pos": m.start(), "type": typ, "number": num,
            "modifying_text_id": f"{typ.lower()}-{num}".replace("é", "e"),
            "title": re.sub(r"\s+", " ", m["body"]).strip(" ."),
            "date_signed": iso_date(m["body"]), "jo_number": m["jo"], "jo_date": f"{d[2]}-{d[1]}-{d[0]}",
            "amending_article": f"Art. {m['art']}",
        })
    heads.sort(key=lambda h: h["pos"])
    return heads


# ---- 2. instructions and quoted contents ---------------------------------------------------
INSTR = re.compile(r"^\s*(?:Art\.?|Article\.?)\s*(\d+|1er)\s*[.\-–—]+\s*(.*)$")
INSTR2 = re.compile(r"^\s*(Les dispositions de)\s+(.*)$")          # style 2: "Les dispositions de 143 bis de la loi n° 90-11 ... sont modifiées ..."
OPEN_ITEM = re.compile(r"^\s*[»«\"]\s*Art\.?\s*(\d+)(?:\s*-\s*(\d+)|\s+(bis|ter|quater))?(?:\s*[.\-–—])*\s*(.*)$", re.I)
CLOSE = re.compile(r"\s*[«»]\s*\.?\s*$")
ART_NUM = r"(\d+(?:\s*-\s*\d+)?(?:\s+(?:bis|ter|quater))?)"


def norm_num(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\s*-\s*", "-", s.strip()))


def targets_from(sentence: str):
    """Article numbers targeted by an instruction sentence."""
    s = sentence.replace("’", "'")
    out = []
    m = re.search(r"articles?\s+(\d+)\s+à\s+(\d+)", s)                  # "articles 22 à 26"
    if m:
        return [str(i) for i in range(int(m[1]), int(m[2]) + 1)]
    m = re.search(r"aux articles\s+([\d, et]+?)\s+de la pr", s)         # list "115, 116, ... et 133"
    if m:
        return re.findall(r"\d+", m[1])
    for m in re.finditer(r"articles?\s+" + ART_NUM, s):
        out.append(norm_num(m[1]))
    m = re.search(r"des articles\s+(\d+)\s+et\s+(\d+)", s)             # "des articles 140 et 149"
    if m:
        out = [m[1], m[2]]
    # drop the numbers that only appear in "de la loi n° 90-11" or as insertion targets handled elsewhere
    seen, res = set(), []
    for x in out:
        if x not in seen:
            seen.add(x); res.append(x)
    return res


def classify(sentence: str):
    s = sentence.lower().replace("’", "'")
    if "après le terme" in s:
        return "term_substitution"
    if "abrog" in s:
        return "repeal"
    if "inséré" in s or re.search(r"complétées? par (un|les) articles?", s) or "ainsi conçu" in s and "article" in s:
        return "insert"
    if "modifi" in s:
        return "modify"
    if "complét" in s:
        return "complete"
    return "unknown"


def parse_block(block: dict):
    text = block["text"]
    heads = find_headers(text)
    lines = text.split("\n")
    # character offset of each line, to know which header precedes it
    offs, p = [], 0
    for l in lines:
        offs.append(p); p += len(l) + 1

    def header_at(pos):
        cur = None
        for h in heads:
            if h["pos"] <= pos:
                cur = h
        return cur

    records = []
    last_instr = None
    i = 0
    while i < len(lines):
        line = lines[i]
        pos = offs[i]
        # a quoted new content?
        mo = OPEN_ITEM.match(line)
        if mo and last_instr is not None:
            number = mo[1] + (f"-{mo[2]}" if mo[2] else "") + (f" {mo[3].lower()}" if mo[3] else "")
            first = mo[4]
            partial = bool(re.match(r"^[….\s]{3,}", first))
            first = re.sub(r"^[….\s]{3,}", "", first)
            body = [first] if first.strip() else []
            closed = bool(CLOSE.search(line)) and len(line.strip()) > 4
            j = i
            while not closed and j + 1 < len(lines):
                j += 1
                nxt = lines[j]
                if re.match(r"^\s*(?:Art\.?|Article\.?)\s*\d+\s*[.\-–—]", nxt) and not OPEN_ITEM.match(nxt):
                    j -= 1; break                                        # a new instruction: stop
                if re.match(r"^\s*[….]+\s*$", nxt):
                    partial = True; continue
                body.append(nxt)
                closed = bool(CLOSE.search(nxt))
            content = "\n".join(body)
            content = CLOSE.sub("", content).strip()
            if re.search(r"sans changement|[….]{4,}", content):
                partial = True
            h = header_at(pos)
            action = last_instr["action"]
            if h and h.get("amending_article") and last_instr["label"] in ("Art. ?", "Art. " + h["amending_article"].replace("Art. ", "")):
                pass
            if (mo[2] or mo[3]) and action != "modify":
                action = "insert"                                       # 73-1, 52 bis ... are new articles
            records.append({
                "target_article": norm_num(number),
                "action": action,
                "partial": partial,
                "new_content": re.sub(r"\s+", " ", content.replace("\n", " ")).strip(),
                "new_paragraphs": [re.sub(r"\s+", " ", x).strip() for x in content.split("\n") if x.strip()],
                "amending_article": last_instr["label"],
                "instruction": last_instr["sentence"],
                "header": h,
                "closed": closed,
            })
            i = j + 1
            continue
        mi = INSTR.match(line)
        if not mi:
            m2 = INSTR2.match(line)
            if m2 and "90-11" in (line + " " + (lines[i + 1] if i + 1 < len(lines) else "")).replace(" ", ""):
                hh = header_at(pos) or {}
                mi = re.match(r"(.*)", hh.get("amending_article", "Art. ?").replace("Art. ", ""))   # label from header
        if mi:
            sent = line
            k = i
            while not re.search(r"[:.]\s*$", sent) and k + 1 < len(lines) and k - i < 3:
                k += 1; sent += " " + lines[k]
            sent = re.sub(r"\s+", " ", sent).strip()
            if INSTR2.match(line) and not INSTR.match(line):
                sent = sent  # keep as is
            relevant = "90-11" in sent.replace(" ", "") or "de la présente loi" in sent or "article" in sent.lower()
            about_law = ("90-11" in sent.replace(" ", "")) or ("de la présente loi" in sent)
            action = classify(sent)
            if relevant and about_law and action != "unknown":
                last_instr = {"label": f"Art. {mi[1]}", "sentence": sent, "action": action}
                if action in ("repeal", "term_substitution") or "comme suit" not in sent and "suivants" not in sent and "ainsi conçu" not in sent:
                    for t in targets_from(sent):
                        records.append({
                            "target_article": t, "action": action, "partial": False, "new_content": None,
                            "new_paragraphs": [], "amending_article": last_instr["label"], "instruction": sent,
                            "header": header_at(pos), "closed": True,
                        })
                    last_instr = None if action in ("repeal", "term_substitution") else last_instr
            i = k + 1 if k > i else i + 1
            continue
        i += 1
    return records


def main():
    blocks = json.loads(IN.read_text(encoding="utf-8"))
    raw, seen, out = [], set(), []
    for b in blocks:
        raw += parse_block(b)
    for r in raw:
        h = r["header"] or {}
        norm = re.sub(r"^[—–\-\s]+", "", r["new_content"] or "").lower()
        key = (h.get("modifying_text_id"), r["amending_article"], r["target_article"], r["action"], norm)
        if key in seen:
            continue
        seen.add(key)
        reasons = []
        if not h:
            reasons.append("modifying text header not found")
        if r["action"] in ("modify", "complete", "insert") and not r["new_content"]:
            reasons.append("no new content extracted")
        if r["action"] in ("modify", "complete", "insert") and not r["closed"]:
            reasons.append("closing quote not found")
        title = (h.get("title") or "").lower()
        about_itself = re.search(r"présent(e)? (ordonnance|loi|décret)", r["instruction"].lower())
        if h and not about_itself and not re.search(r"modifi|complét|loi de finances|portant|abrog", title):
            reasons.append("modifying text UNCERTAIN: the nearest header looks like an application text, verify in the official JO")
        base = re.match(r"\d+", r["target_article"])
        if not base or int(base[0]) > MAX_ARTICLE:
            reasons.append("target outside 1-158")
        if r["partial"]:
            reasons.append("partial content: P3 must rebuild the full text from the previous version")
        out.append({
            "target_article": r["target_article"],
            "action": r["action"],
            "modifying_text_id": h.get("modifying_text_id"),
            "modifying_text_type": h.get("type"),
            "modifying_text_number": h.get("number"),
            "date_signed": h.get("date_signed"),
            "jo_number": h.get("jo_number"),
            "jo_date": h.get("jo_date"),
            "amending_article": r["amending_article"],
            "partial": r["partial"],
            "new_content": r["new_content"],
            "new_paragraphs": r["new_paragraphs"],
            "instruction": r["instruction"],
            "needs_review": bool(reasons),
            "review_reasons": "; ".join(reasons),
        })
    def sortkey(x):
        n = re.match(r"\d+", x["target_article"])
        return (int(n[0]) if n else 999, x["jo_date"] or "", x["target_article"])
    out.sort(key=sortkey)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    cols = [c for c in out[0] if c != "new_paragraphs"]
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:        # utf-8-sig: opens correctly in Excel
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(out)
    arts = sorted({x["target_article"] for x in out}, key=lambda a: (int(re.match(r"\d+", a)[0]), a))
    print(f"{len(out)} amendment records for {len(arts)} target articles; "
          f"{sum(x['needs_review'] for x in out)} flagged needs_review")
    by = {}
    for x in out:
        by[x["action"]] = by.get(x["action"], 0) + 1
    print("by action:", by)


if __name__ == "__main__":
    main()
