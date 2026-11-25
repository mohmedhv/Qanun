"""P4 search API with P3 legal-version integration.

Undated search: uses the provisional P2 corpus for articles without a P3
version record, and substitutes the latest P3 version for tracked articles.
Dated search: only returns articles for which P3 has an explicit version valid
on the requested date. Untracked articles are excluded rather than being
incorrectly treated as historically valid.

`version_verified` is deliberately False until the team's independent legal
source review is complete. `version_record_available` means a P3 version row
was found; it is not a claim that the wording has been independently audited.
"""
import hashlib
import json
import os
import sqlite3
from datetime import date as date_type
from pathlib import Path

from .bm25_search import BM25Index
from .semantic_search import E5Index
from .hybrid_search import reciprocal_rank_fusion

CHUNKS_JSONL = Path('data/processed/chunks.jsonl')
CHUNKS_JSON = Path('data/interim/chunks.json')
DB = Path('data/db/qanun.db')
_DOCS = _BM25 = None
_E5_INDEXES = {}
_BM25_INDEXES = {}


def _numbers_by_article_id():
    if not DB.exists():
        return {}
    with sqlite3.connect(DB) as connection:
        return dict(connection.execute("SELECT article_id, number FROM articles"))


def _number_from_id(article_id):
    value = str(article_id).rsplit('-art-', 1)[-1]
    for suffix in ('bis', 'ter', 'quater'):
        if value.endswith(f'-{suffix}'):
            return f"{value[:-(len(suffix) + 1)]} {suffix}"
    return value


def load_documents():
    if CHUNKS_JSONL.exists():
        chunks = [json.loads(line) for line in CHUNKS_JSONL.read_text(encoding='utf-8').splitlines() if line.strip()]
    elif CHUNKS_JSON.exists():
        chunks = json.loads(CHUNKS_JSON.read_text(encoding='utf-8'))
    else:
        raise FileNotFoundError('P2 chunks not found; expected data/processed/chunks.jsonl')
    docs = []
    numbers_by_article_id = _numbers_by_article_id()
    for c in chunks:
        cite = c.get('cite_id') or c.get('article_id')
        if not cite:
            raise ValueError('Chunk missing cite_id/article_id')
        article_id = c.get('article_id') or cite
        docs.append({
            'cite_id': cite,
            'article_id': article_id,
            'number': str(c.get('number') or numbers_by_article_id.get(article_id) or _number_from_id(article_id)),
            'text_id': c.get('text_id') or 'loi-90-11',
            'chunk_id': c.get('chunk_id') or cite,
            'text': c.get('content') or c.get('text') or '',
            'embedding_text': c.get('text_for_embedding') or c.get('content') or c.get('text') or '',
            'context': ' '.join(x for x in (c.get('parent_title'), c.get('parent_chapter')) if x),
            'source_url': c.get('source_url'),
            'version_id': None, 'valid_from': None, 'valid_to': None,
            'version_status': 'provisional_p2', 'version_record_available': False,
            'version_verified': False,
        })
    return docs


def _iso_date(value):
    if value is None or value == '':
        return None
    if isinstance(value, date_type):
        return value.isoformat()
    value = str(value).strip()
    return date_type.fromisoformat(value).isoformat()


def _version_module():
    try:
        from src.versions.versions import get_version, list_versions
    except ImportError as exc:
        raise RuntimeError('P3 version module is missing; expected src/versions/versions.py') from exc
    if not DB.exists():
        raise FileNotFoundError('P3 version database is missing: data/db/qanun.db')
    return get_version, list_versions


def _tracked_numbers(text_id='loi-90-11'):
    if not DB.exists():
        return set()
    with sqlite3.connect(DB) as conn:
        rows = conn.execute(
            'SELECT DISTINCT articles.number FROM versions '
            'JOIN articles ON articles.article_id=versions.article_id '
            'WHERE articles.text_id=?',
            (text_id,),
        ).fetchall()
    return {str(r[0]) for r in rows}


def _paragraphs(content, raw_paragraphs):
    if isinstance(raw_paragraphs, str):
        try:
            raw_paragraphs = json.loads(raw_paragraphs)
        except Exception:
            raw_paragraphs = None
    if isinstance(raw_paragraphs, list):
        parts = [str(p).strip() for p in raw_paragraphs if str(p).strip()]
        if len(content) > 2400 and len(parts) > 1:
            return parts
    return [content]


def _versioned_documents(base_docs, date=None):
    get_version, _ = _version_module()
    requested_date = _iso_date(date)
    tracked = _tracked_numbers()
    base_by_article = {}
    for doc in base_docs:
        base_by_article.setdefault(doc['number'], []).append(doc)

    output = []
    # Preserve the P2 provisional corpus for undated queries, except that
    # articles tracked by P3 are replaced by their latest/current P3 wording.
    if requested_date is None:
        output.extend(d for d in base_docs if d['number'] not in tracked)

    for number in sorted(tracked, key=lambda x: (int(''.join(ch for ch in x if ch.isdigit()) or 0), x)):
        version = get_version('loi-90-11', number, requested_date)
        if version is None:
            continue
        base = base_by_article.get(number, [{}])[0]
        content = str(version.get('content') or '').strip()
        if not content:
            # Never index empty/fictitious version text.
            continue
        parts = _paragraphs(content, version.get('paragraphs'))
        article_id = version.get('article_id') or base.get('article_id') or f'loi-90-11-art-{number.replace(" ", "-")}'
        cite_id = base.get('cite_id') or article_id
        for i, part in enumerate(parts, 1):
            chunk_id = f"p3-version-{version['version_id']}" + (f"-p{i}" if len(parts) > 1 else '')
            output.append({
                'cite_id': cite_id, 'article_id': article_id,
                'number': number, 'text_id': version.get('text_id') or 'loi-90-11',
                'chunk_id': chunk_id, 'text': part,
                'embedding_text': f"Loi n° 90-11, article {number}. {part}",
                'context': base.get('context', ''), 'source_url': version.get('source_url') or base.get('source_url'),
                'version_id': version.get('version_id'), 'valid_from': version.get('valid_from'),
                'valid_to': version.get('valid_to'), 'version_status': version.get('status'),
                'version_record_available': True,
                # P3's validator is not a substitute for the independent source
                # review requested by the professor.
                'version_verified': False,
                'modifying_text_id': version.get('modifying_text_id'),
                'repealing_text_id': version.get('repealing_text_id'),
            })
    return output


def _corpus_key(docs):
    raw = '\n'.join(f"{d['cite_id']}|{d['chunk_id']}|{d['embedding_text']}" for d in docs)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _indexes(docs=None):
    global _DOCS, _BM25
    if docs is None:
        if _DOCS is None:
            _DOCS = load_documents()
            _BM25 = BM25Index(_DOCS)
        return _DOCS, _BM25
    key = _corpus_key(docs)
    if key not in _BM25_INDEXES:
        _BM25_INDEXES[key] = BM25Index(docs)
    return docs, _BM25_INDEXES[key]


def _e5_index(docs):
    key = _corpus_key(docs)
    if key not in _E5_INDEXES:
        # Separate cache per exact temporal corpus: never reuse vectors for
        # original wording when a historical version has different wording.
        cache = Path('data/processed') / f'e5_temporal_{key[:16]}.npz'
        _E5_INDEXES[key] = E5Index(docs, cache_path=cache)
    return _E5_INDEXES[key]


def _dedupe(ranked, k):
    seen, result = set(), []
    for doc, score in ranked:
        if doc['cite_id'] not in seen:
            seen.add(doc['cite_id'])
            result.append((doc, score))
        if len(result) >= k:
            break
    return result


def search(question: str, date=None, k: int = 5):
    """Search Law 90-11 and return article citations with P3 version metadata.

    For a dated query, only articles with an explicit P3 version valid on that
    date are eligible. For undated queries, untracked P2 articles remain
    provisional and P3-tracked articles use their current version (or are
    omitted if repealed).
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError('question must be a non-empty string')
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError('k must be a positive integer')
    requested_date = _iso_date(date)
    base_docs = load_documents()
    docs = _versioned_documents(base_docs, requested_date)
    if not docs:
        return []
    docs, bm25 = _indexes(docs)
    method = os.getenv('JURIDEAZOR_SEARCH_METHOD', 'hybrid' if Path('data/processed/e5_embeddings.npz').exists() else 'bm25').lower()
    if method not in {'bm25', 'semantic', 'hybrid'}:
        raise ValueError('JURIDEAZOR_SEARCH_METHOD must be bm25, semantic, or hybrid')
    rank_b = bm25.search(question, k=len(docs)) if method in {'bm25', 'hybrid'} else None
    rank_e = _e5_index(docs).search(question, k=len(docs)) if method in {'semantic', 'hybrid'} else None
    if method == 'bm25':
        ranked = rank_b
    elif method == 'semantic':
        ranked = rank_e
    else:
        ranked = reciprocal_rank_fusion(rank_b, rank_e, k=len(docs))

    results = []
    for doc, score in _dedupe(ranked, k):
        results.append({
            'cite_id': doc['cite_id'], 'article_id': doc['article_id'],
            'number': doc['number'], 'text_id': doc['text_id'],
            'chunk_id': doc['chunk_id'], 'score': float(score), 'text': doc['text'],
            'source_url': doc.get('source_url'), 'version_id': doc.get('version_id'),
            'valid_from': doc.get('valid_from'), 'valid_to': doc.get('valid_to'),
            'version_status': doc.get('version_status', 'provisional_p2'),
            'version_record_available': bool(doc.get('version_record_available')),
            'version_verified': False,
            'modifying_text_id': doc.get('modifying_text_id'),
            'repealing_text_id': doc.get('repealing_text_id'), 'method': method,
        })
    return results
