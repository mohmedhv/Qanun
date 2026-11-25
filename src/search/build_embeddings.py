"""Build and persist multilingual-E5 passage vectors once."""
from .semantic_search import E5Index
from .search_service import load_documents

def main():
    docs=load_documents()
    E5Index(docs, force_rebuild=True)
    print(f"Saved E5 vectors for {len(docs)} chunks to data/processed/e5_embeddings.npz")

if __name__ == '__main__': main()
