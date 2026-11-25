"""Reproducible article-level retrieval evaluation, fixed dev and test splits."""
import csv
import json
from pathlib import Path
from .search_service import load_documents
from .bm25_search import BM25Index
from .semantic_search import E5Index
from .hybrid_search import reciprocal_rank_fusion

QUESTIONS = Path('eval/questions.csv')
OUT = Path('data/processed/search_results.csv')
SUMMARY = Path('data/processed/search_metrics.json')
FAILURES = Path('data/processed/failure_analysis.csv')

def dedupe(ranked, k=None):
    seen = set()
    out = []
    for doc, score in ranked:
        if doc['cite_id'] not in seen:
            seen.add(doc['cite_id'])
            out.append((doc, score))
        if k is not None and len(out) >= k:
            break
    return out

def metrics(rows, split, method):
    subset = [r for r in rows if r['split'] == split]
    if not subset:
        return {'n':0,'recall@1':None,'recall@3':None,'recall@5':None,'mrr':None}
    hits = {1:0,3:0,5:0}
    rr = []
    for row in subset:
        rank = row['ranks'].get(method)
        for k in hits:
            hits[k] += int(rank is not None and rank <= k)
        # MRR@5, following the agreed top-five evaluation protocol.
        rr.append(1 / rank if rank is not None and rank <= 5 else 0)
    n = len(subset)
    return {'n':n, 'recall@1':hits[1]/n, 'recall@3':hits[3]/n,
            'recall@5':hits[5]/n, 'mrr':sum(rr)/n}

def main():
    docs = load_documents()
    bm = BM25Index(docs)
    with QUESTIONS.open(encoding='utf-8-sig', newline='') as f:
        questions = list(csv.DictReader(f))
    if not questions or any(q['split'] not in {'dev','test'} for q in questions):
        raise ValueError('Questions must have valid dev/test splits')
    if len({q['question_id'] for q in questions}) != len(questions):
        raise ValueError('Duplicate question IDs')
    for q in questions:
        if not any(d['cite_id'] == q['expected_cite_id'] for d in docs):
            raise ValueError('Missing expected cite_id for '+q['question_id'])
    try:
        e5 = E5Index(docs)
    except (ImportError, RuntimeError, OSError) as exc:
        e5 = None
        print('E5 unavailable:', exc)
    methods = ['bm25'] + (['e5','hybrid'] if e5 is not None else [])
    rows = []
    for q in questions:
        b = dedupe(bm.search(q['question'], k=len(docs)))
        ranked = {'bm25':b}
        if e5 is not None:
            s = dedupe(e5.search(q['question'], k=len(docs)))
            ranked['e5'] = s
            ranked['hybrid'] = dedupe(reciprocal_rank_fusion(b, s, k=len(docs)))
        ranks = {}
        for method, ranking in ranked.items():
            ranks[method] = next((i for i,(d,_) in enumerate(ranking, 1) if d['cite_id'] == q['expected_cite_id']), None)
        rows.append({**q, 'ranked':ranked, 'ranks':ranks})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['question_id','split','expected_cite_id','bm25_top5','e5_top5','hybrid_top5',
                    'bm25_rank','e5_rank','hybrid_rank'])
        for row in rows:
            w.writerow([row['question_id'],row['split'],row['expected_cite_id']] +
                       [';'.join(d['cite_id'] for d,_ in row['ranked'].get(m, [])[:5]) for m in ['bm25','e5','hybrid']] +
                       [row['ranks'].get(m,'') for m in ['bm25','e5','hybrid']])
    with FAILURES.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['question_id','split','question','expected_cite_id','method','target_rank','top5','failure_type'])
        for row in rows:
            for method in methods:
                rank = row['ranks'][method]
                if rank != 1:
                    w.writerow([row['question_id'],row['split'],row['question'],row['expected_cite_id'],method,
                                rank if rank is not None else '',
                                ';'.join(d['cite_id'] for d,_ in row['ranked'][method][:5]),
                                'missed_top5' if rank is None or rank > 5 else 'ranked_below_first'])
    summary = {split:{m:metrics(rows,split,m) for m in methods} for split in ['dev','test']}
    SUMMARY.write_text(json.dumps({
        'dataset':'eval/questions.csv',
        'article_level':True,
        'mrr_definition':'MRR@5 (reciprocal rank is 0 if the target is beyond top 5)',
        'reference_review':'PENDING independent second-person verification',
        'model':'intfloat/multilingual-e5-small' if e5 is not None else None,
        'metrics':summary}, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))
    print('Saved:', OUT, SUMMARY, FAILURES)

if __name__ == '__main__':
    main()
