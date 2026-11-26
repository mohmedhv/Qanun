from src.search.evaluate_adaptive_v2 import weighted_rrf


def test_weighted_rrf_prefers_consistent_original_rank():
    a = {'cite_id': 'a'}
    b = {'cite_id': 'b'}
    ranked = weighted_rrf([([(a, 1.0), (b, 0.1)], 2), ([(b, 1.0), (a, 0.1)], 1)])
    assert ranked[0][0]['cite_id'] == 'a'


def test_dedupe_does_not_double_count_article():
    a = {'cite_id': 'a'}
    b = {'cite_id': 'b'}
    ranked = weighted_rrf([([(a, 1.0), (a, 0.5), (b, 0.2)], 1)])
    assert len(ranked) == 2
