"""P4/P3/P5 smoke test. Run after installing search requirements and building E5."""
import os
import argparse
from .search_service import search

QUESTION = 'Quelle est la durée légale hebdomadaire du travail ?'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bm25-only', action='store_true', help='Run BM25 and P3 date checks without loading E5')
    args = parser.parse_args()
    methods = ['bm25'] if args.bm25_only else ['bm25', 'semantic', 'hybrid']
    for method in methods:
        os.environ['JURIDEAZOR_SEARCH_METHOD'] = method
        results = search(QUESTION, k=5)
        if not results:
            raise RuntimeError(f'{method} returned no results')
        print(f'[{method}] {len(results)} hits; top: {results[0]["cite_id"]} score={results[0]["score"]:.6f}')
        assert all({'cite_id','score','source_url','version_id','text','version_record_available','version_verified'} <= set(row) for row in results)

    os.environ['JURIDEAZOR_SEARCH_METHOD'] = 'bm25'
    old = search('licenciement faute grave', date='1991-01-01', k=20)
    new = search('licenciement faute grave', date='2020-01-01', k=20)
    old73 = next((r for r in old if r['number'] == '73'), None)
    new73 = next((r for r in new if r['number'] == '73'), None)
    assert old73 and new73 and old73['version_id'] != new73['version_id']
    assert old73['text'] != new73['text']
    post_repeal = search('salaire indemnité', date='2020-01-01', k=50)
    assert all(r['number'] not in {'72','87 bis'} for r in post_repeal)
    print('[P3 historical] version switch and repeal exclusion PASSED')
    print('P4/P3-to-P5 API smoke test PASSED')

if __name__ == '__main__':
    main()
