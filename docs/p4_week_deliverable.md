# P4 week-2 checklist / submission status

- [x] P2 chunks exported in `data/processed/chunks.jsonl` (160 chunks, 158 article IDs).
- [x] 20 French questions, 10 development + 10 held-out test, IDs matched to P2 content.
- [ ] 20 official-reference checks signed by an **independent second person** (currently PENDING).
- [x] Deterministic French preprocessing and BM25 (positive IDF).
- [x] E5 embeddings and model-aware, corpus-fingerprint cache (rebuild locally).
- [x] Article-level RRF hybrid with full candidate coverage.
- [x] Recall@1, @3, @5, MRR@5 and per-question failure analysis exports.
- [x] `search(question, date=None, k=5)` interface with citations, score, source, and conservative version flags.
- [x] Inclusive valid_to boundary code and regression tests.
- [x] Automated checks: 16 passed in the packaging environment.
- [x] Student previously ran BM25/E5/Hybrid on Windows and supplied results, recorded with provenance in comparison report.
- [ ] Student must **rerun the revised ZIP** with E5 on Windows; hybrid candidates and cache validation changed in this revision.
- [ ] P3 must provide verified version metadata **and matching historical legal wording** before date-specific retrieval can be trusted.
- [x] P3/P5 handoff specification and test evidence included.

**Submit with the limitations visible** rather than mark legal verification or P3-version integration as complete.
