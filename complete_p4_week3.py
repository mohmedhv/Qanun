"""Qanun P4 Week 3: 30-question evaluation + independent human review sheet.

Run from the repository root. Does not alter the original datasets, model or
retrieval implementations. Human review stays PENDING until someone signs off.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter
from pathlib import Path

ROOT = Path.cwd()
EVAL_DIR = ROOT / 'eval' / 'p4'
OUT_DIR = EVAL_DIR / 'week3_completion'


def read_csv(path: Path):
    with path.open(encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def load_questions():
    original = read_csv(EVAL_DIR / 'questions.csv')
    graph = read_csv(EVAL_DIR / 'graph_questions_week3.csv')
    if len(original) != 20 or len(graph) != 10:
        raise ValueError(f'Expected 20 original + 10 graph questions, got {len(original)} + {len(graph)}')
    if Counter(q.get('split', '').strip().lower() for q in original) != {'dev': 10, 'test': 10}:
        raise ValueError('Original 20-question split must be dev=10, test=10; do not alter it.')
    ids = [q['question_id'] for q in original + graph]
    if len(set(ids)) != 30:
        raise ValueError('Duplicate question IDs detected.')
    return original, graph


def ref_id(q, graph=False):
    value = q['expected_text_id'] if graph else q['expected_cite_id']
    return ('text:' if graph else 'article:') + value.removeprefix('text:').removeprefix('article:')


def review_template(original, graph):
    prior = {r['question_id']: r for r in read_csv(EVAL_DIR / 'P4_P3_signoff_status.csv')}
    rows = []
    for q in original + graph:
        is_graph = 'expected_text_id' in q
        p = prior.get(q['question_id'], {})
        rows.append({
            'question_id': q['question_id'],
            'group': 'graph_generated' if is_graph else q['split'],
            'question': q['question'],
            'expected_answer_type': 'Text' if is_graph else 'Article',
            'expected_node_id': ref_id(q, graph=is_graph),
            'related_article_id': q.get('expected_article_id') or q.get('expected_cite_id') or '',
            'relationship': q.get('relation', ''),
            'source_url': q.get('source_url') or p.get('evidence_url', ''),
            'graph_relation_status': q.get('graph_relation_status', ''),
            'prior_documentary_status': p.get('independent_review_status', ''),
            'prior_reviewer_record': p.get('independent_reviewer', ''),
            'human_reviewer': '',
            'human_review_date': '',
            'human_decision': 'PENDING',
            'verified_expected_node_id': '',
            'verified_source_url': '',
            'verified_page_or_provision': '',
            'review_notes': '',
        })
    columns = list(rows[0].keys())
    outfile = OUT_DIR / 'independent_review_30.csv'
    if outfile.exists():
        # Never overwrite a partially completed human review.
        existing = read_csv(outfile)
        if [r['question_id'] for r in existing] != [r['question_id'] for r in rows]:
            raise ValueError('Review sheet exists with unexpected question IDs. Back it up and reconcile manually.')
        print('Review sheet already exists; keeping human entries:', outfile)
    else:
        write_csv(outfile, columns, rows)
        print('Created human review sheet:', outfile)
    return outfile


def actual_review_map():
    path = OUT_DIR / 'independent_review_30.csv'
    result = {}
    if not path.exists():
        return result
    for r in read_csv(path):
        decision = r.get('human_decision', '').strip().upper()
        named_reviewer = r.get('human_reviewer', '').strip()
        date = r.get('human_review_date', '').strip()
        url = r.get('verified_source_url', '').strip()
        verified = r.get('verified_expected_node_id', '').strip()
        if decision == 'CONFIRMED' and named_reviewer and date and url and verified == r['expected_node_id']:
            result[r['question_id']] = 'HUMAN_CONFIRMED_RECORDED'
        elif decision in {'REJECTED', 'CORRECTION_REQUIRED'}:
            result[r['question_id']] = 'HUMAN_REVIEW_REJECTED_OR_CORRECTION'
        else:
            result[r['question_id']] = 'PENDING_INDEPENDENT_REVIEW'
    return result


def unique_nodes(items):
    nodes, seen = [], set()
    for x in items:
        node = x.get('graph_node_id')
        if not node:
            aid = x.get('article_id')
            node = 'article:' + aid.removeprefix('article:') if aid else ''
        if node and node not in seen:
            nodes.append(node)
            seen.add(node)
    return nodes


def enrich_with_direct(question, graph_ranked, k):
    from src.search.graph_candidate_retrieval import graph_candidates
    direct = graph_candidates(question)  # prediction depends only on question + graph
    seen = set()
    out = []
    for item in direct + graph_ranked:
        node = item.get('graph_node_id') or ('article:' + item['article_id'] if item.get('article_id') else '')
        if node and node not in seen:
            out.append(item)
            seen.add(node)
        if len(out) >= k:
            break
    return out


def evaluate(original, graph):
    os.environ['JURIDEAZOR_SEARCH_METHOD'] = 'hybrid'
    from src.search.search_service import search
    from src.search.graph_ranker import hybrid_graph_rank

    expected_review = actual_review_map()
    rows = []
    all_questions = [(q, False) for q in original] + [(q, True) for q in graph]
    for i, (q, is_graph) in enumerate(all_questions, 1):
        expected = ref_id(q, graph=is_graph)
        # For both methods, use one fixed budget k=5. No reference labels passed.
        hybrid = search(q['question'], k=5)
        graph_ranked = hybrid_graph_rank(hybrid, k=5)
        combined = enrich_with_direct(q['question'], graph_ranked, 5)
        methods = {
            'hybrid': unique_nodes(hybrid)[:5],
            'hybrid_graph': unique_nodes(graph_ranked)[:5],
            'article_graph': unique_nodes(combined)[:5],
        }
        row = {
            'question_id': q['question_id'],
            'split': q.get('split', ''),
            'question_group': 'graph_generated_pending' if is_graph else 'original_article',
            'answer_type': 'Text' if is_graph else 'Article',
            'expected_node_id': expected,
            'related_article_node_id': 'article:' + q['expected_article_id'] if is_graph else '',
            'reference_review': expected_review.get(q['question_id'], 'PENDING_INDEPENDENT_REVIEW'),
            'source_relation_status': q.get('graph_relation_status', ''),
        }
        for name, ids in methods.items():
            row[f'{name}_top3'] = ';'.join(ids[:3])
            row[f'{name}_top5'] = ';'.join(ids[:5])
            row[f'{name}_hit3'] = int(expected in ids[:3])
            # One gold answer per question. Recall@5 = Hit@5.
            row[f'{name}_recall5'] = int(expected in ids[:5])
        a, b = 'hybrid_hit3', 'hybrid_graph_hit3'
        row['hybrid_vs_graph_hit3'] = ('improved' if row[b] > row[a]
                                     else 'worsened' if row[b] < row[a] else 'unchanged')
        a, b = 'hybrid_recall5', 'hybrid_graph_recall5'
        row['hybrid_vs_graph_recall5'] = ('improved' if row[b] > row[a]
                                        else 'worsened' if row[b] < row[a] else 'unchanged')
        rows.append(row)
        print(f"{i:02d}/30 {q['question_id']} [{row['answer_type']}] "
              f"H={row['hybrid_hit3']} HG={row['hybrid_graph_hit3']} ADG={row['article_graph_hit3']}")
    out = OUT_DIR / 'per_question_30.csv'
    write_csv(out, list(rows[0]), rows)
    summary = []
    groups = {
        'dev_original': [r for r in rows if r['split'] == 'dev'],
        'test_original': [r for r in rows if r['split'] == 'test'],
        'all_original': [r for r in rows if r['question_group'] == 'original_article'],
        'graph_generated_pending': [r for r in rows if r['answer_type'] == 'Text'],
        'all_30_mixed_descriptive_only': rows,
    }
    for label, subset in groups.items():
        if not subset:
            continue
        record = {'group': label, 'count': len(subset),
                  'human_review_pending_count': sum(r['reference_review'] != 'HUMAN_CONFIRMED_RECORDED' for r in subset)}
        for name in ('hybrid', 'hybrid_graph', 'article_graph'):
            for met in ('hit3', 'recall5'):
                record[f'{name}_{met}'] = round(sum(int(r[f'{name}_{met}']) for r in subset) / len(subset), 4)
        for metric in ('hit3', 'recall5'):
            col = f'hybrid_vs_graph_{metric}'
            for outcome in ('improved', 'worsened', 'unchanged'):
                record[f'{metric}_{outcome}_count'] = sum(r[col] == outcome for r in subset)
        summary.append(record)
    out_sum = OUT_DIR / 'summary_30.csv'
    write_csv(out_sum, list(summary[0]), summary)
    print('\nSummary (provisional; no independent human sign-off inferred):')
    for s in summary:
        print(s['group'], f"n={s['count']}",
              f"H@3={s['hybrid_hit3']:.2%}",
              f"HG@3={s['hybrid_graph_hit3']:.2%}",
              f"ADG@3={s['article_graph_hit3']:.2%}",
              f"pending_review={s['human_review_pending_count']}")
    print('Per question:', out)
    print('Summary:', out_sum)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-review', action='store_true', help='Only create/preserve independent-review template')
    parser.add_argument('--evaluate', action='store_true', help='Evaluate three methods on 30 questions')
    args = parser.parse_args()
    original, graph = load_questions()
    review_template(original, graph)
    if args.evaluate:
        evaluate(original, graph)
    elif not args.prepare_review:
        print('Run with --evaluate for 30-question evaluation (Hybrid model may take time).')


if __name__ == '__main__':
    main()
