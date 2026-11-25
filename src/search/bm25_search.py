"""Deterministic BM25 with non-negative Robertson/Sparck Jones IDF.

Uses one chunk per document and P4's shared French tokenizer. No optional
library changes ranking depending on the local Python environment.
"""
from collections import Counter
import math
from .preprocessing import tokenize

class BM25Index:
    def __init__(self, documents, k1=1.5, b=0.75):
        self.documents = list(documents)
        self.tokens = [tokenize(d.get('text', '') + ' ' + d.get('context', '')) for d in self.documents]
        self.k1, self.b = k1, b
        self.doc_freq = Counter(t for doc in self.tokens for t in set(doc))
        self.doc_len = [len(t) for t in self.tokens]
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 0.0

    def scores(self, query):
        q = set(tokenize(query))
        n = len(self.tokens)
        if not n:
            return []
        out = []
        for terms, dl in zip(self.tokens, self.doc_len):
            tf = Counter(terms)
            score = 0.0
            for term in q:
                df = self.doc_freq.get(term, 0)
                freq = tf.get(term, 0)
                if not df or not freq:
                    continue
                idf = math.log1p((n - df + 0.5) / (df + 0.5))
                denom = freq + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1e-9))
                score += idf * freq * (self.k1 + 1) / denom
            out.append(score)
        return out

    def search(self, query, k=5):
        if k <= 0:
            return []
        scores = self.scores(query)
        order = sorted(range(len(scores)), key=lambda i: (-scores[i], self.documents[i]['cite_id'], self.documents[i].get('chunk_id','')))
        return [(self.documents[i], float(scores[i])) for i in order if scores[i] > 0][:k]
