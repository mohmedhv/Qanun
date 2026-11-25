"""Article-level reciprocal rank fusion; duplicate paragraph chunks count once."""
def reciprocal_rank_fusion(*ranked_lists, k=5, rrf_constant=60):
    if k <= 0:
        return []
    fused = {}
    for ranked in ranked_lists:
        seen = set()
        for doc, _score in ranked:
            key = doc['cite_id']
            if key in seen:
                continue
            seen.add(key)
            rank = len(seen)
            if key not in fused:
                fused[key] = [doc, 0.0]
            fused[key][1] += 1.0 / (rrf_constant + rank)
    ordered = sorted(fused.values(), key=lambda x: (-x[1], x[0]['cite_id']))
    return [(doc, float(score)) for doc, score in ordered[:k]]
