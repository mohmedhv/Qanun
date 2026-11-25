"""Local multilingual E5 with a validated, reusable NumPy embedding cache."""
from pathlib import Path
import hashlib
import json
import numpy as np

DEFAULT_MODEL = 'intfloat/multilingual-e5-small'
CACHE = Path('data/processed/e5_embeddings.npz')

def _fingerprint(documents):
    records = [(d['cite_id'], d.get('chunk_id',''), d.get('embedding_text', d['text'])) for d in documents]
    return hashlib.sha256(json.dumps(records, ensure_ascii=False).encode('utf-8')).hexdigest()

class E5Index:
    def __init__(self, documents, model_name=DEFAULT_MODEL, cache_path=CACHE, force_rebuild=False):
        self.documents = list(documents)
        self.model_name = model_name
        self.cache_path = Path(cache_path)
        self.model = None
        ids = np.array([d['cite_id'] + '#' + d.get('chunk_id','') for d in self.documents])
        fingerprint = _fingerprint(self.documents)
        if self.cache_path.exists() and not force_rebuild:
            with np.load(self.cache_path, allow_pickle=False) as saved:
                if ('fingerprint' in saved and str(saved['fingerprint'].item()) == fingerprint
                        and str(saved['model_name'].item()) == model_name
                        and np.array_equal(saved['ids'], ids)
                        and saved['vectors'].shape[0] == len(ids)):
                    self.vectors = saved['vectors'].astype('float32')
                    return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError('Install sentence-transformers with: python -m pip install -r requirements-search.txt') from exc
        self.model = SentenceTransformer(model_name)
        passages = ['passage: ' + d.get('embedding_text', d['text']) for d in self.documents]
        self.vectors = self.model.encode(passages, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True).astype('float32')
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(self.cache_path, ids=ids, vectors=self.vectors, model_name=np.array(model_name), fingerprint=np.array(fingerprint))

    def search(self, query, k=5, allowed_ids=None):
        if k <= 0 or not self.documents:
            return []
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError('sentence-transformers is needed to encode user queries even with a cached index') from exc
            self.model = SentenceTransformer(self.model_name)
        q = self.model.encode(['query: ' + query], normalize_embeddings=True, convert_to_numpy=True).astype('float32')[0]
        scores = self.vectors @ q
        indices = range(len(self.documents))
        if allowed_ids is not None:
            indices = (i for i in indices if self.documents[i]['chunk_id'] in allowed_ids)
        ranked = sorted(indices, key=lambda i: (-float(scores[i]), self.documents[i]['cite_id'], self.documents[i]['chunk_id']))
        return [(self.documents[i], float(scores[i])) for i in ranked[:k]]
