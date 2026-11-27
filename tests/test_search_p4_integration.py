"""Additional lightweight P4 integration/regression tests (no model download)."""
import csv
import json
import sqlite3
from pathlib import Path
import pytest
from src.search.bm25_search import BM25Index
from src.search.hybrid_search import reciprocal_rank_fusion
from src.search.evaluate import dedupe, metrics
from src.search.search_service import load_documents
import src.search.search_service as svc


def test_bm25_empty_and_zero_query():
    assert BM25Index([]).search('any', 5) == []
    assert BM25Index([{'cite_id':'a','text':'bonjour'}]).search(' ', 5) == []


def test_bm25_identical_in_all_environments():
    docs=[{'cite_id':'a1','text':'La durée légale du travail est fixée à quarante quatre heures par semaine.'},
          {'cite_id':'a2','text':'Le congé annuel rémunéré est calculé par mois de travail.'}]
    assert BM25Index(docs).search('durée légale du travail')[0][0]['cite_id'] == 'a1'


def test_full_corpus_has_20_distinct_verified_ids_pending():
    docs=load_documents()
    assert len(docs) == 160
    with open('eval/p4/questions.csv', encoding='utf-8-sig') as f:
        questions=list(csv.DictReader(f))
    assert len(questions) >= 20
    assert len([q for q in questions if q['split']=='test']) >= 10
    assert all(q['expected_cite_id'] in {d['cite_id'] for d in docs} for q in questions)
    with open('eval/p4/P4_P3_signoff_status.csv', encoding='utf-8-sig') as f:
        reviews = {row['question_id']: row for row in csv.DictReader(f)}
    assert set(reviews) == {q['question_id'] for q in questions}
    for q in questions:
        review = reviews[q['question_id']]
        status = q['independent_second_check']
        assert review['independent_review_status'] == status
        assert review['expected_cite_id'] == q['expected_cite_id']
        assert status in {'PENDING', 'CONFIRMED', 'CORRECTION_REQUIRED'}
        if status != 'PENDING':
            assert review['independent_reviewer'] and review['independent_review_date']


def test_rrf_duplicate_chunks_only_one_vote():
    a={'cite_id':'a','chunk_id':'a#1'}
    a2={'cite_id':'a','chunk_id':'a#2'}
    b={'cite_id':'b','chunk_id':'b#1'}
    result=reciprocal_rank_fusion([(a,10),(a2,9),(b,8)],[(b,.8)],k=2)
    assert result[0][0]['cite_id']=='b'
    assert len(result)==2


def test_mrr_at_5_excludes_rank_6():
    rows=[{'split':'dev','ranks':{'bm25':1}},{'split':'dev','ranks':{'bm25':6}}]
    result=metrics(rows,'dev','bm25')
    assert result['recall@1']==.5 and result['recall@5']==.5 and result['mrr']==.5


def test_date_inclusive_and_repeal():
    from src.versions.versions import get_version
    assert get_version('loi-90-11', '73', '1991-12-26')['version_number'] == 1
    assert get_version('loi-90-11', '73', '1991-12-27')['version_number'] == 2
    assert get_version('loi-90-11', '72', '1994-06-02') is not None
    assert get_version('loi-90-11', '72', '1994-06-03') is None
    assert get_version('loi-90-11', '87 bis', '2015-01-01') is not None
    assert get_version('loi-90-11', '87 bis', '2015-01-02') is None


def test_search_uses_historical_version_text(monkeypatch):
    monkeypatch.setenv('JURIDEAZOR_SEARCH_METHOD', 'bm25')
    old = svc.search('licenciement faute grave', date='1991-01-01', k=20)
    new = svc.search('licenciement faute grave', date='2020-01-01', k=20)
    old73 = next(r for r in old if r['number'] == '73')
    new73 = next(r for r in new if r['number'] == '73')
    assert old73['version_id'] != new73['version_id']
    assert old73['text'] != new73['text']
    assert old73['version_record_available'] is True
    assert old73['version_verified'] is False


def test_search_never_returns_repealed_articles_after_repeal(monkeypatch):
    monkeypatch.setenv('JURIDEAZOR_SEARCH_METHOD', 'bm25')
    results = svc.search('salaire indemnité', date='2020-01-01', k=50)
    numbers = {r['number'] for r in results}
    assert '72' not in numbers
    assert '87 bis' not in numbers


def test_search_rejects_bad_inputs(monkeypatch):
    monkeypatch.setenv('JURIDEAZOR_SEARCH_METHOD','bm25')
    with pytest.raises(ValueError):
        svc.search('')
    with pytest.raises(ValueError):
        svc.search('hello', k=0)
    with pytest.raises(ValueError):
        svc.search('hello', date='2024-44-99')


def test_search_handoff_contract(monkeypatch):
    monkeypatch.setenv('JURIDEAZOR_SEARCH_METHOD','bm25')
    result=svc.search('Quelle est la durée légale hebdomadaire du travail ?', k=5)
    assert result
    assert {'cite_id','score','number','text','source_url','version_id','valid_from','valid_to','version_verified','method'} <= result[0].keys()
    assert result[0]['version_id'] is None
    assert result[0]['version_verified'] is False


def test_semantic_cache_detects_text_change_without_download(tmp_path):
    import numpy as np
    from src.search.semantic_search import E5Index, _fingerprint
    docs=[{'cite_id':'a','chunk_id':'a','text':'hello','embedding_text':'hello'}]
    cache=tmp_path/'v.npz'
    np.savez_compressed(cache, ids=np.array(['a#a']), vectors=np.ones((1,2),dtype='float32'),
                        model_name=np.array('mock'),fingerprint=np.array(_fingerprint(docs)))
    idx=E5Index(docs,model_name='mock',cache_path=cache)
    assert idx.model is None and idx.vectors.shape==(1,2)
    assert _fingerprint([{**docs[0],'embedding_text':'changed'}]) != _fingerprint(docs)


def test_hybrid_search_uses_temporal_version_corpus(monkeypatch):
    monkeypatch.setenv('JURIDEAZOR_SEARCH_METHOD', 'hybrid')
    class FakeE5:
        def __init__(self, documents, cache_path=None):
            self.documents = documents
        def search(self, query, k=5):
            return [(doc, 0.9 - i * 0.001) for i, doc in enumerate(self.documents[:k])]
    monkeypatch.setattr(svc, 'E5Index', FakeE5)
    svc._E5_INDEXES.clear()
    results = svc.search('licenciement faute grave', date='1991-01-01', k=20)
    article73 = next(r for r in results if r['number'] == '73')
    assert article73['version_id'] == 1
    assert article73['valid_from'] == '1990-04-27'
    assert article73['valid_to'] == '1991-12-26'
    assert article73['method'] == 'hybrid'
