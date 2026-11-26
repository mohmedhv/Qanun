"""P4 experimental weighted fusion v2; leaves all original files unchanged.

Run: python -m src.search.evaluate_adaptive_v2
Uses a fixed original-ranking preference of 2 to 1; not trained on labels.
"""
import csv
import json
from pathlib import Path
from .search_service import load_documents
from .bm25_search import BM25Index
from .semantic_search import E5Index
from .hybrid_search import reciprocal_rank_fusion
from .legal_query_expansion import expand_queries, expanded_query_text

SOURCE = Path('eval/questions.csv')
OUT = Path('eval/results/adaptive_v2_comparison.csv')
METRICS = Path('eval/results/adaptive_v2_metrics.json')


def unique(ranking):
    seen = set()
    result = []
    for doc, score in ranking:
        if doc['cite_id'] not in seen:
            seen.add(doc['cite_id'])
            result.append((doc, score))
    return result


def weighted_rrf(lists_and_weights, k=160, constant=60):
    """Fuse article-level lists. Return full scored ranking with no target labels."""
    combined = {}
    for ranked, weight in lists_and_weights:
        for rank, (doc, _) in enumerate(unique(ranked), 1):
            key = doc['cite_id']
            if key not in combined:
                combined[key] = [doc, 0.0]
            combined[key][1] += weight / (constant + rank)
    return sorted(((d, s) for d, s in combined.values()),
                  key=lambda item: (-item[1], item[0]['cite_id']))[:k]


def rank_of(ranked, cite):
    return next((i for i, (d, _) in enumerate(ranked, 1)
                 if d['cite_id'] == cite), None)


def measure(rows, split, prefix):
    ranks = [row[prefix] for row in rows if row['split'] == split]
    n = len(ranks)
    return {
        'n': n,
        'recall@1': sum(x is not None and x <= 1 for x in ranks) / n if n else None,
        'recall@3': sum(x is not None and x <= 3 for x in ranks) / n if n else None,
        'recall@5': sum(x is not None and x <= 5 for x in ranks) / n if n else None,
        'mrr@5': sum(1/x if x is not None and x <= 5 else 0 for x in ranks) / n if n else None,
    }


def main():
    with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
        questions = list(csv.DictReader(stream))
    if not questions or not {'question_id', 'split', 'question', 'expected_cite_id'} <= set(questions[0]):
        raise ValueError('Missing required question CSV columns')
    if any(q['split'] not in ('dev', 'test') for q in questions):
        raise ValueError('Invalid split')
    docs = load_documents()
    bm, e5 = BM25Index(docs), E5Index(docs)
    e5.search(questions[0]['question'], k=1)
    rows = []
    for q in questions:
        question = q['question']
        original_b = unique(bm.search(question, k=len(docs)))
        original_e = unique(e5.search(question, k=len(docs)))
        original_h = reciprocal_rank_fusion(original_b, original_e, k=len(docs))

        variants = expand_queries(question)
        expanded_b = unique(bm.search(expanded_query_text(question), k=len(docs)))
        expanded_e = reciprocal_rank_fusion(*[
            unique(e5.search(v, k=len(docs))) for v in variants
        ], k=len(docs))
        expanded_h = reciprocal_rank_fusion(expanded_b, expanded_e, k=len(docs))

        # Three fixed, method-independent comparisons. Weight original twice.
        adapted_b = weighted_rrf([(original_b, 2), (expanded_b, 1)], k=len(docs))
        adapted_e = weighted_rrf([(original_e, 2), (expanded_e, 1)], k=len(docs))
        adapted_h = weighted_rrf([(original_h, 2), (expanded_h, 1)], k=len(docs))
        current = {'question_id': q['question_id'], 'split': q['split'],
                   'question': question, 'expected_cite_id': q['expected_cite_id'],
                   'generated_queries': ' || '.join(variants)}
        for condition, rankings in (
            ('baseline', (original_b, original_e, original_h)),
            ('expanded', (expanded_b, expanded_e, expanded_h)),
            ('adaptive', (adapted_b, adapted_e, adapted_h)),
        ):
            for method, ranking in zip(('bm25', 'e5', 'hybrid'), rankings):
                name = condition + '_' + method
                current[name + '_rank'] = rank_of(ranking, q['expected_cite_id'])
                current[name + '_top5'] = ';'.join(d['cite_id'] for d, _ in ranking[:5])
        rows.append(current)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        'model': 'intfloat/multilingual-e5-small',
        'protocol': 'P2 article-level; original query preferred 2:1 in weighted RRF',
        'caution': 'Dev and test already examined earlier; test is no longer strictly untouched. Do not tune to test.',
        'metrics': {split: {condition: {method: measure(rows, split, f'{condition}_{method}_rank')
                                          for method in ('bm25', 'e5', 'hybrid')}
                            for condition in ('baseline', 'expanded', 'adaptive')}
                    for split in ('dev', 'test')},
    }
    METRICS.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary['metrics'], indent=2, ensure_ascii=False))
    print('Wrote:', OUT, METRICS)


if __name__ == '__main__':
    main()
