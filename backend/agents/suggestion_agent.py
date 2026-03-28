import time
import os
import json
import re
import numpy as np
import faiss
from typing import List, Dict
from state import BRDState
from faiss_client import FAISSClient

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    # Vectors from FAISSClient are normalized, so inner product = cosine
    return float(np.dot(v1, v2))

def suggestion_agent(state: BRDState) -> BRDState:
    """
    RAG-based Predictive Requirement Suggestion Agent (Robust Semantic Version).
    
    Logic:
    1. Collect extracted requirements.
    2. Search FAISS for projects in the same domain.
    3. Use semantic embeddings to ensure suggestions are NOT already in the draft.
    4. Rank suggestion quality and filter out low-confidence noise.
    """
    start_time = time.time()
    
    domain = state.get("domain", "software")
    functional_reqs = state.get("functional_reqs", [])
    
    # 1. Collect all extracted requirement texts for context and duplicate checking
    extracted_texts = [r.get("text", "") for r in functional_reqs if r.get("text")]
    
    # Check domain_sections for non-software domains (Healthcare, Mechanical, etc.)
    domain_data = state.get("domain_data", {})
    sections = domain_data.get("sections", {})
    if isinstance(sections, dict):
        for section_name, items in sections.items():
            if isinstance(items, list):
                for item in items:
                    text = item.get("text") if isinstance(item, dict) else item
                    if text: extracted_texts.append(text)
    
    # Determine the search query
    if not extracted_texts:
        query_text = state.get("raw_input", "")[:1000]
    else:
        # Prioritize recent/core requirements as search context
        query_text = " ".join(extracted_texts[:20])
        
    try:
        faiss_client = FAISSClient()
        
        # Pre-compute embeddings for existing requirements for semantic deduplication
        existing_embeddings = []
        if extracted_texts:
            existing_embeddings = faiss_client.encode(extracted_texts)
            # Normalize for cosine similarity via inner product
            for e in existing_embeddings:
                faiss.normalize_L2(np.array([e]).astype('float32'))

        # Search the knowledge base
        matched_results = faiss_client.search(query_text, domain=domain, top_k=3)
        
        candidate_pool = []
        matched_brds = []
        
        # Process retrieval results
        for brd in matched_results:
            matched_brds.append({
                "project_name": brd.get("project_name"),
                "similarity_score": round(brd.get("similarity_score", 0), 3),
                "domain": brd.get("domain")
            })
            
            # Extract distinct requirements from the retrieved project
            project_reqs = brd.get("requirements", []).copy()
            domain_sections = brd.get("domain_sections", {})
            if isinstance(domain_sections, dict):
                for sec_name, items in domain_sections.items():
                    if isinstance(items, list):
                        for item in items:
                            text = item.get("text") if isinstance(item, dict) else item
                            if text: project_reqs.append(text)
            
            for text in project_reqs:
                candidate_pool.append({
                    "text": text,
                    "from": brd.get("project_name"),
                    "domain": brd.get("domain"),
                    "base_score": brd.get("similarity_score", 0),
                    "id": brd.get("id")
                })

        # Pattern-based expansion
        patterns_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "requirement_patterns.json")
        if os.path.exists(patterns_path):
            with open(patterns_path, "r") as f:
                patterns = json.load(f)
            
            combined_input = (state.get("raw_input", "") + " ".join(extracted_texts)).lower()
            for p in patterns:
                for keyword in p.get("trigger_keywords", []):
                    if keyword.lower() in combined_input:
                        candidate_pool.append({
                            "text": p["suggested_requirement"],
                            "from": "pattern_database",
                            "domain": domain,
                            "base_score": 0.65, # Standard pattern boost
                            "id": p.get("pattern_id")
                        })
                        break

        # Semantic Deduplication & Quality Filtering
        if not candidate_pool:
            state["suggestions"] = []
        else:
            # 1. Deduplicate the candidate pool itself (internal duplicates)
            unique_candidates = []
            cand_texts = [c["text"] for c in candidate_pool]
            cand_embeddings = faiss_client.encode(cand_texts)
            for i, emb in enumerate(cand_embeddings):
                faiss.normalize_L2(np.array([emb]).astype('float32'))
                
                is_duplicate = False
                # Check against existing requirements in the current document
                if len(existing_embeddings) > 0:
                    for ex_emb in existing_embeddings:
                        if cosine_similarity(emb, ex_emb) > 0.85: # High semantic overlap
                            is_duplicate = True
                            break
                
                if not is_duplicate:
                    # Check against already added unique candidates
                    for added_emb, _ in unique_candidates:
                        if cosine_similarity(emb, added_emb) > 0.85:
                            is_duplicate = True
                            break
                            
                if not is_duplicate:
                    unique_candidates.append((emb, candidate_pool[i]))

            # 2. Format final suggestions
            final_suggestions = []
            for _, cand in unique_candidates:
                final_suggestions.append({
                    "text": cand["text"],
                    "from_project": cand["from"],
                    "domain": cand["domain"],
                    "confidence": cand["base_score"],
                    "source_brd_id": cand["id"]
                })
            
            state["suggestions"] = sorted(final_suggestions, key=lambda x: x["confidence"], reverse=True)[:10]
            
        state["matched_brds"] = matched_brds
        state["suggestion_count"] = len(state.get("suggestions", []))
        
    except Exception as e:
        print(f"[SuggestionAgent] Robust Error: {e}")
        # Keep current suggestions if any, or empty
        if "suggestions" not in state: state["suggestions"] = []
        if "matched_brds" not in state: state["matched_brds"] = []
        state["suggestion_count"] = len(state["suggestions"])
        
    state["processing_times"]["suggestion_agent"] = round(time.time() - start_time, 3)
    return state
