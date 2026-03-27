"""
RAG Agent
=========
Queries real ChromaDB (populated with Enron + AMI vectors) to retrieve
the top-3 most similar examples for each classified non-noise sentence.

Uses the same embedding model (all-MiniLM-L6-v2) as the ingestion script
to ensure consistent vector space.

Model and ChromaDB client are initialised at module level for efficiency.
"""

import time
from state import BRDState
from chroma_client import get_collection

from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Module-level embedding model — loads once at startup
# ---------------------------------------------------------------------------
_embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("[RAGAgent] Embedding model loaded (all-MiniLM-L6-v2)")


def rag_agent(state: BRDState) -> BRDState:
    """
    For each classified non-noise sentence, queries ChromaDB for top-3
    semantically similar examples from the Enron + AMI corpus.

    Filtering:
    - Queries are filtered by matching label (where clause)
    - If label-filtered query returns < 3 results, falls back to unfiltered query
    - Similarity = 1 - cosine_distance (ChromaDB returns cosine distance)

    Updates state with:
    - rag_examples: list of retrieved similar sentences
    - analytics.rag_source_breakdown: enron/ami/fallback counts
    """
    start_time = time.time()

    try:
        collection = get_collection()
    except RuntimeError as e:
        # ChromaDB not ready — return state unchanged with warning
        state.setdefault("rag_examples", [])
        state.setdefault("analytics", {})
        state["analytics"]["rag_source_breakdown"] = {"enron": 0, "ami": 0, "fallback": 0}
        state["processing_times"]["rag"] = round(time.time() - start_time, 3)
        print(f"[RAGAgent] WARNING: {e} — skipping RAG step")
        return state

    classified = state.get("classified_sentences", [])
    rag_examples = []
    source_counts = {"enron": 0, "ami": 0, "fallback": 0}

    # Only query for non-noise sentences
    query_sentences = [s for s in classified if s.get("label") != "noise"]

    if not query_sentences:
        state["rag_examples"] = []
        state.setdefault("analytics", {})
        state["analytics"]["rag_source_breakdown"] = source_counts
        state["processing_times"]["rag"] = round(time.time() - start_time, 3)
        return state

    for sentence in query_sentences:
        text = sentence["text"]
        label = sentence["label"]

        try:
            # Primary query: filter by same label
            results = collection.query(
                query_texts=[text],
                n_results=5,
                where={"label": label},
                include=["documents", "metadatas", "distances"],
            )

            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]

            if len(docs) < 3:
                # Fallback: no label filter
                results = collection.query(
                    query_texts=[text],
                    n_results=5,
                    include=["documents", "metadatas", "distances"],
                )
                docs = results["documents"][0]
                metas = results["metadatas"][0]
                dists = results["distances"][0]
                source = "fallback"
            else:
                source = None  # Will be read from metadata

            for doc, meta, dist in zip(docs[:3], metas[:3], dists[:3]):
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                similarity = round(max(0.0, 1.0 - dist), 4)
                actual_source = meta.get("source", "unknown") if source is None else source

                rag_examples.append({
                    "text": doc,
                    "label": meta.get("label", label),
                    "source": actual_source,
                    "similarity": similarity,
                    "query_sentence": text[:80],
                })

                if actual_source in source_counts:
                    source_counts[actual_source] += 1
                else:
                    source_counts["fallback"] += 1

        except Exception as e:
            # Gracefully skip individual failed queries
            print(f"[RAGAgent] Query error for '{text[:50]}': {e}")
            continue

    state["rag_examples"] = rag_examples
    state.setdefault("analytics", {})
    state["analytics"]["rag_source_breakdown"] = source_counts
    state["processing_times"]["rag"] = round(time.time() - start_time, 3)

    return state


if __name__ == "__main__":
    sample_state = {
        "raw_input": "The system must allow user authentication. API must respond under 200ms.",
        "source_type": "email",
        "classified_sentences": [
            {"text": "The system must allow user authentication.", "label": "functional_req", "confidence": 0.92},
            {"text": "API must respond under 200ms.", "label": "nfr", "confidence": 0.88},
        ],
        "rag_examples": [],
        "functional_reqs": [],
        "nfrs": [],
        "stakeholders": [],
        "decisions": [],
        "timeline": [],
        "scope": {"in_scope": [], "out_of_scope": [], "assumptions": []},
        "gaps": [],
        "completeness_score": 0.0,
        "priority_scores": [],
        "source_map": {},
        "processing_times": {},
        "analytics": {},
        "retry_count": 0,
        "error": None,
    }

    result = rag_agent(sample_state)
    print(f"RAG examples retrieved: {len(result['rag_examples'])}")
    for ex in result["rag_examples"][:3]:
        print(f"  [{ex['source']:8s}] ({ex['similarity']:.3f}) {ex['text'][:70]}")
    print(f"\nSource breakdown: {result['analytics']['rag_source_breakdown']}")
    print(f"Processing time : {result['processing_times']['rag']}s")
