import json
from pathlib import Path
from src.search.preprocessing import tokenize
from src.search.bm25_search import BM25Index
from src.search.search_service import load_documents, _versioned_documents

def test_french_preprocessing_removes_accents_and_stopwords():
    assert tokenize('Le licenciement du salarié') == ['licenciement', 'salarie']

def test_bm25_returns_relevant_article_for_exact_terms():
    docs=[{'cite_id':'a1','text':'La durée légale du travail est fixée à quarante quatre heures par semaine.'},
          {'cite_id':'a2','text':'Le congé annuel rémunéré est calculé par mois de travail.'}]
    assert BM25Index(docs).search('durée légale du travail',1)[0][0]['cite_id']=='a1'

def test_p2_chunks_load_and_have_unique_article_citations():
    docs=load_documents()
    assert len(docs)==160
    assert all(d['cite_id'].startswith('loi-90-11-art-') for d in docs)

def test_date_filter_uses_p3_version_rows():
    docs=load_documents()
    historical=_versioned_documents(docs, '1994-06-01')
    current=_versioned_documents(docs, '2026-11-20')
    hist_articles={d['number'] for d in historical}
    current_articles={d['number'] for d in current}
    assert {'72','73','87','87 bis'} <= hist_articles  # all four have a version on 1994-06-01
    assert {'73','87'} <= current_articles
    assert '72' not in current_articles and '87 bis' not in current_articles

def test_search_public_api_returns_cite_id_and_score(monkeypatch):
    import src.search.search_service as svc
    monkeypatch.setenv('JURIDEAZOR_SEARCH_METHOD','bm25')
    svc._DOCS = svc._BM25 = None
    results=svc.search('duree legale hebdomadaire travail',k=5)
    assert results and {'cite_id','score','number','text'} <= set(results[0])
    assert 'loi-90-11-art-22' in [r['cite_id'] for r in results]

def test_p3_version_valid_to_boundary_is_inclusive():
    from src.versions.versions import get_version
    # Article 73 v1 is valid through 1991-12-26; v2 starts the next day.
    assert get_version('loi-90-11', '73', '1991-12-26')['version_number'] == 1
    assert get_version('loi-90-11', '73', '1991-12-27')['version_number'] == 2

def test_rrf_combines_two_rankings():
    from src.search.hybrid_search import reciprocal_rank_fusion
    a={'cite_id':'a','text':'A'}; b={'cite_id':'b','text':'B'}; c={'cite_id':'c','text':'C'}
    fused=reciprocal_rank_fusion([(a,9),(b,8)],[(b,.9),(c,.8)],k=3)
    assert fused[0][0]['cite_id']=='b'
    assert len(fused)==3
