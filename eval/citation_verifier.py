"""P5 citation verifier.

For RAG answers (`check_citations` / `verify_citations`):
  - every cited article must be one of the retrieved articles;
  - every quoted passage (« … », “ … ”, "…", 20+ characters) must really appear in the
    text of the article it is attached to (the nearest article cited before it);
  - articles merely named inside a real quote (e.g. "l'article 12" quoted from 12 bis)
    are not counted as citations, and an article named in a retrieved article's text is
    reported as `named_in_context`, not as invented;
  - a correct refusal ("Je ne trouve pas de règle dans le corpus") with no citation is valid.

For graph answers (`verify_graph_citations`): every cited (text, article, relation,
provision) must be an edge of the knowledge graph.
"""
import re
import unicodedata

DASHES = "-‑‐–—"  # hyphen, non-breaking hyphen (U+2011), hyphen (U+2010), en dash, em dash
# "Article 8", "Art. 12 bis", "article 73-4", "Article 73‑4"  ->  "8", "12 bis", "73-4"
ARTICLE_RE = re.compile(
    rf"(?:Article|Art\.?)\s*(\d+(?:\s*(?:bis|ter))?(?:\s*[{DASHES}]\s*\d+)?)", re.IGNORECASE)
# French Code du travail references: "L1242-1", "R1234-5"
FRENCH_RE = re.compile(rf"\b([LR]\d+[{DASHES}]\d+)", re.IGNORECASE)
QUOTE_RE = re.compile(r"«(.+?)»|“(.+?)”|\"(.+?)\"", re.DOTALL)
REFUSAL = "je ne trouve pas de regle dans le corpus"
MIN_QUOTE = 20


def normalize(text: str) -> str:
    """Lowercase, unify quotes/dashes/apostrophes, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text)
    for src, dst in (("’", "'"), ("‘", "'"), ("«", '"'), ("»", '"'), ("“", '"'), ("”", '"')):
        text = text.replace(src, dst)
    for dash in DASHES:
        text = text.replace(dash, "-")
    return re.sub(r"\s+", " ", text).strip().lower()


def _letters(text: str) -> str:
    """Words only: dashes become spaces, punctuation is dropped (formatting-insensitive)."""
    text = normalize(text).replace("-", " ")
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def quote_in_text(quote: str, text: str, min_piece: int = 15) -> bool:
    """True if every piece of the quote (split on ... or …) appears in the text.

    Case, spacing, apostrophes, dashes and punctuation are ignored; the words must match.
    """
    pieces = [_letters(p) for p in re.split(r"\.\.\.|…", normalize(quote))]
    pieces = [p for p in pieces if len(p) >= min_piece]
    page = _letters(text)
    return bool(pieces) and all(p in page for p in pieces)


def _norm_number(number: str) -> str:
    number = re.sub(rf"\s*[{DASHES}]\s*", "-", number.strip().lower())
    return re.sub(r"\s+", " ", number)


def _article_number(art: dict) -> str:
    # P4 returns "number" (data contract); "article_number" kept for older data.
    return _norm_number(str(art.get("number", art.get("article_number", ""))))


def _quotes(answer: str) -> list[tuple[int, int, str]]:
    """(start, end, quoted text) for every quote long enough to be checked."""
    found = []
    for m in QUOTE_RE.finditer(answer):
        inner = next(g for g in m.groups() if g is not None).strip()
        if len(inner) >= MIN_QUOTE:
            found.append((m.start(), m.end(), inner))
    return found


def _mask(answer: str, spans: list[tuple[int, int, str]]) -> str:
    """Blank out quoted passages, keeping positions."""
    chars = list(answer)
    for start, end, _ in spans:
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def extract_citations(llm_answer: str) -> list[str]:
    """Article numbers cited outside quotes (normalized, sorted, unique)."""
    masked = _mask(llm_answer, _quotes(llm_answer))
    cited = {_norm_number(m) for m in ARTICLE_RE.findall(masked)}
    cited |= {m.upper().replace("‑", "-") for m in FRENCH_RE.findall(masked)}
    return sorted(cited)


def check_citations(llm_answer: str, retrieved_articles: list) -> dict:
    """Detailed check of a RAG answer against the articles it was given."""
    texts = {_article_number(a): str(a.get("text", "")) for a in retrieved_articles}
    quotes = _quotes(llm_answer)
    masked = _mask(llm_answer, quotes)
    cited = extract_citations(llm_answer)
    # An article not retrieved but named inside a retrieved article's text (12 named in 12 bis)
    # comes from the context: it is reported, not counted as invented.
    in_context = {_norm_number(n) for t in texts.values() for n in ARTICLE_RE.findall(t)}
    named_in_context = [num for num in cited if num not in texts and num in in_context]
    hallucinated = [num for num in cited if num not in texts and num not in in_context]
    refusal = REFUSAL in normalize(llm_answer).replace("è", "e")

    mentions = [(m.start(), _norm_number(m.group(1))) for m in ARTICLE_RE.finditer(masked)]
    quotes_missing = []
    for start, _, quote in quotes:
        before = [num for pos, num in mentions if pos < start]
        attached = before[-1] if before else None
        if attached in texts:
            ok = quote_in_text(quote, texts[attached])
        else:
            ok = any(quote_in_text(quote, t) for t in texts.values())
        if not ok:
            quotes_missing.append({"attached_to": attached, "quote": quote[:120]})

    if not cited:
        valid = refusal and not quotes_missing
    else:
        valid = not hallucinated and not quotes_missing
    return {"valid": valid, "cited": cited, "hallucinated": hallucinated,
            "named_in_context": named_in_context, "refusal": refusal,
            "quotes_checked": len(quotes), "quotes_missing": quotes_missing}


def verify_citations(llm_answer: str, retrieved_articles: list) -> bool:
    """True if the answer only cites retrieved articles and only quotes their real text."""
    result = check_citations(llm_answer, retrieved_articles)
    if not result["cited"] and result["refusal"]:
        print("✅ Correct refusal: no citation needed.")
    elif not result["cited"]:
        print("❌ Verification Failed: The LLM did not cite any articles.")
    if result["hallucinated"]:
        valid_numbers = sorted({_article_number(a) for a in retrieved_articles})
        print(f"🚨 HALLUCINATION DETECTED! The LLM cited articles that P4 did not provide: {result['hallucinated']}")
        print(f"   Valid articles from P4: {valid_numbers}")
    for miss in result["quotes_missing"]:
        print(f"🚨 QUOTE NOT FOUND in article {miss['attached_to']}: «{miss['quote']}»")
    if result["valid"] and result["cited"]:
        print("✅ All citations are valid and exist in the retrieved context.")
    return result["valid"]


def article_node(number: str, text_id: str = "loi-90-11") -> str:
    """Graph node id of an article: '87 bis' -> 'article:loi-90-11-art-87-bis'."""
    return f"article:{text_id}-art-{_norm_number(number).replace(' ', '-')}"


def verify_graph_citations(citations: list, edges: list) -> bool:
    """Every cited (text, article, relation, provision) must be an edge of the graph."""
    if not citations:
        return False
    known = {(e["source"], e["target"], e["relation"], e.get("provision", "")) for e in edges}
    return all((f"text:{c['text_id']}", article_node(c["article"]), c["relation"], c["provision"]) in known
               for c in citations)
