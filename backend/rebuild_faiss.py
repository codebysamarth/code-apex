
import os
import json
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Path configuration
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "rag_examples.json"
OUTPUT_DIR = BASE_DIR / "faiss_db"
OUTPUT_FILE = OUTPUT_DIR / "vector_store.pkl"

MODEL_NAME = "all-MiniLM-L6-v2"

def rebuild_index():
    print(f"--- Rebuilding FAISS Index with {DATA_PATH} ---")
    
    # 1. Load data
    if not DATA_PATH.exists():
        print(f"ERROR: rag_examples.json not found at {DATA_PATH}")
        return
        
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} examples.")
    
    # 2. Extract texts and metadata
    texts = [item['text'] for item in data]
    metadatas = []
    for item in data:
        metadatas.append({
            "label": item.get("label", "functional_req"),
            "source": item.get("source", "enron+ami"),
            "original_index": data.index(item)
        })
    
    # 3. Create embeddings
    print(f"Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    print(f"Creating embeddings for {len(texts)} sentences (this may take a minute)...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype(np.float32)
    
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)
    
    # 4. Create FAISS index
    dimension = embeddings.shape[1]
    # L2 distance on normalized vectors is proportional to cosine distance
    index = faiss.IndexFlatIP(dimension) 
    index.add(embeddings)
    
    print(f"Index built with {index.ntotal} vectors.")
    
    # 5. Save to pkl
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
        
    store_data = {
        "index": index,
        "texts": texts,
        "metadatas": metadatas,
        "dimension": dimension,
        "embedding_model": MODEL_NAME
    }
    
    with open(OUTPUT_FILE, 'wb') as f:
        pickle.dump(store_data, f)
        
    print(f"SUCCESS: Vector store saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    rebuild_index()
