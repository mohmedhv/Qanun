import time
from llm_client import ask, get_api_call_count

question = "Quel est le jour de repos hebdomadaire légal en Algérie ?"

print("--- First call (will hit API) ---")
t0 = time.time()
r1 = ask(question)
print(f"Time: {time.time()-t0:.2f}s")
print(f"API calls so far: {get_api_call_count()}")
print(f"Answer: {r1[:200]}...")

print("\n--- Second call (should hit cache) ---")
t0 = time.time()
r2 = ask(question)
print(f"Time: {time.time()-t0:.3f}s")
print(f"API calls so far: {get_api_call_count()}")
print(f"Same answer? {r1 == r2}")
