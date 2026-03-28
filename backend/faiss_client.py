import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional

class FAISSClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FAISSClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.store_dir = os.path.join(os.path.dirname(__file__), "faiss_store")
        self.index_path = os.path.join(self.store_dir, "brd_index.faiss")
        self.metadata_path = os.path.join(self.store_dir, "brd_metadata.json")
        
        if not os.path.exists(self.store_dir):
            os.makedirs(self.store_dir)
            
        # Model: all-MiniLM-L6-v2 (384-dim)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dimension = 384
        
        self.metadata = []
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, "r") as f:
                    self.metadata = json.load(f)
                print(f"[FAISSClient] Loaded existing index with {len(self.metadata)} records")
            except Exception as e:
                print(f"[FAISSClient] Error loading existing index: {e}. Creating fresh.")
                self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            print("[FAISSClient] Created fresh index")
            
        self._initialized = True

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode a list of strings into embeddings."""
        return self.model.encode(texts)

    def _get_combined_text(self, brd: Dict) -> str:
        """Combine fields for embedding: project_name + domain + all requirements + domain_sections values flattened."""
        parts = [
            brd.get("project_name", ""),
            brd.get("domain", ""),
            " ".join(brd.get("requirements", [])),
            " ".join(brd.get("nfrs", []))
        ]
        
        # Flatten domain_sections
        domain_sections = brd.get("domain_sections", {})
        if isinstance(domain_sections, dict):
            for section_name, items in domain_sections.items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and "text" in item:
                            parts.append(item["text"])
                        elif isinstance(item, str):
                            parts.append(item)
        
        return " ".join([p for p in parts if p]).strip()

    def add_brd(self, brd: Dict) -> int:
        """Embed BRD and add to index; save after every add."""
        text = self._get_combined_text(brd)
        if not text:
            return -1
            
        # Generate embedding
        embedding = self.model.encode([text])[0]
        # Normalize for cosine similarity via inner product
        faiss.normalize_L2(np.array([embedding]))
        
        # Add to FAISS
        self.index.add(np.array([embedding]).astype('float32'))
        
        # Update metadata
        meta = {
            "id": brd.get("id"),
            "project_name": brd.get("project_name"),
            "domain": brd.get("domain"),
            "industry": brd.get("industry", ""),
            "requirements": brd.get("requirements", []),
            "nfrs": brd.get("nfrs", []),
            "domain_sections": brd.get("domain_sections", {}),
            "compliance": brd.get("compliance", []),
            "tags": brd.get("tags", [])
        }
        self.metadata.append(meta)
        
        self._save()
        return len(self.metadata) - 1

    def search(self, query_text: str, domain: Optional[str] = None, top_k: int = 3) -> List[Dict]:
        """Embed query, search index, optionally filter by domain, return list of metadata dicts."""
        if self.index.ntotal == 0:
            return []
            
        # Embed and normalize query
        query_embedding = self.model.encode([query_text])[0]
        faiss.normalize_L2(np.array([query_embedding]))
        
        # Search index (request more if filtering)
        search_k = top_k * 4 if domain else top_k
        distances, indices = self.index.search(np.array([query_embedding]).astype('float32'), search_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(self.metadata):
                continue
                
            meta = self.metadata[idx].copy()
            # Filter by domain if specified
            if domain and meta.get("domain") != domain:
                continue
                
            # dist is inner product on normalized vectors = cosine similarity
            meta["similarity_score"] = float(dist)
            results.append(meta)
            
            if len(results) >= top_k:
                break
                
        return results

    def get_stats(self) -> Dict:
        """Return total count and per-domain count."""
        total = self.index.ntotal
        domain_counts = {}
        for m in self.metadata:
            d = m.get("domain", "unknown")
            domain_counts[d] = domain_counts.get(d, 0) + 1
            
        return {
            "total_brds": total,
            "per_domain": domain_counts
        }

    def _save(self):
        """Write index and metadata to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def rebuild(self):
        """Clear the index and metadata."""
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.metadata_path):
            os.remove(self.metadata_path)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        print("[FAISSClient] Index cleared for rebuild")
