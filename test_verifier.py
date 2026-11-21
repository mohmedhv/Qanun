from eval.citation_verifier import verify_citations

# Simulate what P4's search returned
retrieved_articles = [
    {'article_number': '8', 'text': 'La relation de travail prend naissance par le contrat écrit ou non écrit.'},
    {'article_number': '10', 'text': 'La preuve du contrat peut être faite par tout moyen.'},
    {'article_number': '11', 'text': 'Le contrat oral est présumé à durée indéterminée.'},
    {'article_number': '13', 'text': 'Conditions du temps partiel.'},
    {'article_number': '63', 'text': 'Modification du contrat.'},
]

# Simulate a fake LLM answer that hallucinates French law
fake_llm_answer = """
Oui, un contrat peut être oral (Article 8).
Cependant, pour les CDD, la loi impose l'écrit (article L1242-1).
Et aussi Article 99 qui n'existe pas.
"""

print("--- Test: Hallucinated citations (should FAIL) ---")
result = verify_citations(fake_llm_answer, retrieved_articles)
print(f"Result: {result}")
assert result == False, "Verifier should have caught the hallucinations"

print("\n--- Test: Valid citations (should PASS) ---")
valid_answer = "Selon Article 8 et Article 10, un contrat oral est valable."
result = verify_citations(valid_answer, retrieved_articles)
print(f"Result: {result}")
assert result == True, "Verifier should have passed"

print("\n✅ Citation verifier is working correctly!")
