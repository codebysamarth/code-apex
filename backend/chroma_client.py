"""
FAISS Client
============
Singleton FAISS vector store client used by the RAG agent at runtime.
FAISS is a vector similarity search library that works without C++ compilation on Windows.

This module provides a ChromaDB-compatible interface for FAISS.
"""

import os
import pickle
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_vector_store = None
_collection_wrapper = None
VECTOR_STORE_PATH = None


class FAISSCollectionWrapper:
    """
    Wrapper around FAISS vector store to provide ChromaDB-compatible interface.
    """
    
    def __init__(self, store_data):
        self.index = store_data['index']
        self.texts = store_data['texts']
        self.metadatas = store_data['metadatas']
        self.dimension = store_data['dimension']
        self.embedding_model = store_data['embedding_model']
        self._embedder = None  # Lazy load on first query
    
    def _get_embedder(self):
        """Lazy load the embedding model only when needed."""
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self.embedding_model)
        return self._embedder
    
    def query(self, query_texts, n_results=5, where=None, include=None):
        """
        Query FAISS index with ChromaDB-compatible interface.
        
        Args:
            query_texts: List of query strings
            n_results: Number of results to return
            where: Filter dictionary (e.g., {"label": "functional_req"})
            include: List of fields to include (e.g., ["documents", "metadatas", "distances"])
        
        Returns:
            Dictionary with ChromaDB-style results
        """
        if include is None:
            include = ["documents", "metadatas", "distances"]
        
        # Create embeddings for queries (lazy load embedder)
        embedder = self._get_embedder()
        query_embeddings = embedder.encode(query_texts, convert_to_numpy=True)
        query_embeddings = query_embeddings.astype(np.float32)
        
        # Normalize for cosine similarity
        import faiss
        faiss.normalize_L2(query_embeddings)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embeddings, n_results * 10)  # Get extra for filtering
        
        # Build results
        results = {
            "documents": [],
            "metadatas": [],
            "distances": []
        }
        
        for query_idx in range(len(query_texts)):
            query_docs = []
            query_metas = []
            query_dists = []
            
            for i, idx in enumerate(indices[query_idx]):
                if idx == -1:  # FAISS uses -1 for no result
                    continue
                
                # Apply filter if specified
                if where:
                    metadata = self.metadatas[idx]
                    match = all(metadata.get(k) == v for k, v in where.items())
                    if not match:
                        continue
                
                query_docs.append(self.texts[idx])
                query_metas.append(self.metadatas[idx])
                query_dists.append(float(distances[query_idx][i]))
                
                if len(query_docs) >= n_results:
                    break
            
            results["documents"].append(query_docs)
            results["metadatas"].append(query_metas)
            results["distances"].append(query_dists)
        
        return results
    
    def count(self):
        """Return number of vectors in the index."""
        return self.index.ntotal


def get_vector_store():
    """
    Returns the FAISS vector store.
    
    Raises:
        RuntimeError: If the vector store file doesn't exist.
    """
    global _vector_store, VECTOR_STORE_PATH
    
    if _vector_store is None:
        faiss_path = os.getenv("FAISS_DB_PATH", "./faiss_db")
        VECTOR_STORE_PATH = Path(faiss_path) / "vector_store.pkl"
        
        if not VECTOR_STORE_PATH.exists():
            raise RuntimeError(
                f"FAISS vector store not found at {VECTOR_STORE_PATH}. "
                "Please run: python backend/offline/build_faiss_db.py"
            )
        
        try:
            with open(VECTOR_STORE_PATH, 'rb') as f:
                _vector_store = pickle.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load FAISS vector store: {e}")
    
    return _vector_store


def get_collection():
    """
    Returns a ChromaDB-compatible collection wrapper for FAISS.
    """
    global _collection_wrapper
    
    if _collection_wrapper is None:
        store = get_vector_store()
        _collection_wrapper = FAISSCollectionWrapper(store)
    
    return _collection_wrapper


def get_vector_count() -> int:
    """Returns the number of vectors in the store, or 0 if not built yet."""
    try:
        store = get_vector_store()
        # Store is a dictionary with 'index' key
        if isinstance(store, dict) and 'index' in store:
            index = store['index']
            if hasattr(index, 'ntotal'):
                return index.ntotal
        # Fallback for object-style access
        elif hasattr(store, 'index') and hasattr(store.index, 'ntotal'):
            return store.index.ntotal
        return 0
    except RuntimeError:
        return 0


if __name__ == "__main__":
    try:
        store = get_vector_store()
        count = get_vector_count()
        print(f"FAISS OK — {count} vectors loaded")
    except RuntimeError as e:
        print(f"FAISS not ready: {e}")

