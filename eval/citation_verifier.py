import re

# "Article 8", "Art. 12 bis", "article 73-4"  ->  "8", "12 bis", "73-4"
ARTICLE_RE = re.compile(r'(?:Article|Art\.?)\s*(\d+(?:\s*(?:bis|ter))?(?:\s*-\s*\d+)?)', re.IGNORECASE)
# French Code du travail references: "L1242-1", "R1234-5"
FRENCH_RE = re.compile(r'\b([LR]\d+[\-‑]\d+)', re.IGNORECASE)


def _norm(number: str) -> str:
    number = re.sub(r'\s*-\s*', '-', number.strip().lower())
    return re.sub(r'\s+', ' ', number)


def extract_citations(llm_answer: str) -> list[str]:
    """Article numbers cited in an answer (normalized, sorted, unique)."""
    cited = {_norm(m) for m in ARTICLE_RE.findall(llm_answer)}
    cited |= {m.upper() for m in FRENCH_RE.findall(llm_answer)}
    return sorted(cited)


def verify_citations(llm_answer: str, retrieved_articles: list) -> bool:
    """
    Checks if the LLM invented article numbers that were not in the retrieved list.
    """
    cited_clean = extract_citations(llm_answer)

    if not cited_clean:
        print("❌ Verification Failed: The LLM did not cite any articles.")
        return False

    # Numbers of the articles P4 actually provided.
    # P4 returns "number" (data contract); "article_number" kept for older data.
    valid_numbers = [_norm(str(art.get('number', art.get('article_number', ''))))
                     for art in retrieved_articles]

    hallucinated = [num for num in cited_clean if num not in valid_numbers]
    if hallucinated:
        print(f"🚨 HALLUCINATION DETECTED! The LLM cited articles that P4 did not provide: {hallucinated}")
        print(f"   Valid articles from P4: {valid_numbers}")
        return False

    print("✅ All citations are valid and exist in the retrieved context.")
    return True
