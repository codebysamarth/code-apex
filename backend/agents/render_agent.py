"""
Render Agent
============
Final agent in the pipeline. Cleans up the state, fills in any missing
fields with defaults, computes final analytics aggregation, and
returns the complete BRDState ready to serialize as JSON for the frontend.

Pure Python — no LLM calls.
"""

import time
from state import BRDState


def _ensure_defaults(state: BRDState) -> BRDState:
    """Ensure all state fields have sensible defaults."""
    state.setdefault("functional_reqs", [])
    state.setdefault("nfrs", [])
    state.setdefault("stakeholders", [])
    state.setdefault("decisions", [])
    state.setdefault("timeline", [])
    state.setdefault("scope", {"in_scope": [], "out_of_scope": [], "assumptions": []})
    state.setdefault("gaps", [])
    state.setdefault("completeness_score", 0.0)
    state.setdefault("priority_scores", [])
    state.setdefault("source_map", {})
    state.setdefault("rag_examples", [])
    state.setdefault("classified_sentences", [])
    state.setdefault("domain", "software")
    state.setdefault("domain_data", {})
    state.setdefault("project_name", "Untitled Project")
    
    # Innovation: Static labels for dashboard cards
    from domain_configs import DOMAIN_CONFIGS
    config = DOMAIN_CONFIGS.get(state["domain"], DOMAIN_CONFIGS["software"])
    state["summary_labels"] = config.get("summary_labels", DOMAIN_CONFIGS["software"]["summary_labels"])

    scope = state.get("scope", {})
    if not isinstance(scope, dict):
        state["scope"] = {"in_scope": [], "out_of_scope": [], "assumptions": []}
    else:
        scope.setdefault("in_scope", [])
        scope.setdefault("out_of_scope", [])
        scope.setdefault("assumptions", [])

    return state


def _aggregate_analytics(state: BRDState) -> dict:
    """Build the final analytics dict for the Analytics tab."""
    analytics = state.get("analytics", {})

    # Processing times summary
    processing_times = state.get("processing_times", {})
    total_time = round(sum(processing_times.values()), 2)
    analytics["processing_times"] = processing_times
    analytics["total_processing_time"] = total_time

    # Requirement type breakdown for pie chart
    if state.get("domain") == "software":
        analytics["req_type_breakdown"] = {
            "Functional": len(state.get("functional_reqs", [])),
            "Non-Functional": len(state.get("nfrs", [])),
            "Decisions": len(state.get("decisions", [])),
            "Stakeholders": len(state.get("stakeholders", [])),
        }
    else:
        # For dynamic domains, count sections in domain_data
        domain_data = state.get("domain_data", {})
        sections = domain_data.get("sections", {})
        
        # Merge standard breakdown with custom sections
        breakdown = {
            "Functional": len(state.get("functional_reqs", [])),
            "Non-Functional": len(state.get("nfrs", [])),
            "Decisions": len(state.get("decisions", [])),
            "Stakeholders": len(state.get("stakeholders", [])),
        }
        
        # Add dynamic sections if not already covered
        for name, items in sections.items():
            if isinstance(items, list) and name not in breakdown:
                breakdown[name] = len(items)
                
        analytics["req_type_breakdown"] = breakdown

    # Confidence distribution (from classifier agent)
    if "confidence_distribution" not in analytics:
        classified = state.get("classified_sentences", [])
        dist = {"high": 0, "medium": 0, "low": 0, "very_low": 0}
        for item in classified:
            c = item.get("confidence", 0)
            if c >= 0.90:
                dist["high"] += 1
            elif c >= 0.70:
                dist["medium"] += 1
            elif c >= 0.50:
                dist["low"] += 1
            else:
                dist["very_low"] += 1
        analytics["confidence_distribution"] = dist

    # Gap severity summary
    gaps = state.get("gaps", [])
    analytics["gap_severity_summary"] = {
        "critical": sum(1 for g in gaps if g.get("severity") == "critical"),
        "high": sum(1 for g in gaps if g.get("severity") == "high"),
        "medium": sum(1 for g in gaps if g.get("severity") == "medium"),
        "low": sum(1 for g in gaps if g.get("severity") == "low"),
    }

    # RAG source breakdown
    if "rag_source_breakdown" not in analytics:
        analytics["rag_source_breakdown"] = {"enron": 0, "ami": 0, "fallback": 0}

    # Completeness score
    analytics["completeness_score"] = state.get("completeness_score", 0.0)

    # Total sentences processed
    analytics["total_sentences_classified"] = analytics.get(
        "total_sentences_classified",
        len(state.get("classified_sentences", []))
    )

    # Source type
    analytics["source_type"] = state.get("source_type", "document")

    return analytics


def _clean_requirement_ids(state: BRDState) -> BRDState:
    """
    Ensure all requirement IDs are unique and properly formatted.
    Re-numbers if duplicates exist.
    """
    seen_ids: set[str] = set()

    for i, req in enumerate(state.get("functional_reqs", []), 1):
        req_id = req.get("id", f"FR-{i:03d}")
        if req_id in seen_ids:
            req_id = f"FR-{i:03d}"
        req["id"] = req_id
        seen_ids.add(req_id)

    for i, req in enumerate(state.get("nfrs", []), 1):
        req_id = req.get("id", f"NFR-{i:03d}")
        if req_id in seen_ids:
            req_id = f"NFR-{i:03d}"
        req["id"] = req_id
        seen_ids.add(req_id)

    for i, dec in enumerate(state.get("decisions", []), 1):
        dec_id = dec.get("id", f"DEC-{i:03d}")
        if dec_id in seen_ids:
            dec_id = f"DEC-{i:03d}"
        dec["id"] = dec_id
        seen_ids.add(dec_id)

    return state


def render_agent(state: BRDState) -> BRDState:
    """
    Final pipeline stage. Normalises state, fills defaults,
    and builds the complete analytics block for the frontend.
    """
    start_time = time.time()

    try:
        state = _ensure_defaults(state)
        state = _clean_requirement_ids(state)
        state["analytics"] = _aggregate_analytics(state)
        # --- NEW: Predictive Suggestions Section (FAISS RAG Feature 2) ---
        if state.get("suggestions"):
            if "domain_data" not in state or not state["domain_data"]:
                state["domain_data"] = {"sections": {}}
            if "sections" not in state["domain_data"]:
                state["domain_data"]["sections"] = {}
                
            suggestion_items = []
            for s in state["suggestions"]:
                # Map fields to match domain section item expectations
                suggestion_items.append({
                    "title": f"Suggestion ({s['from_project']})",
                    "description": s["text"],
                    "priority": "Recommended" if s["confidence"] > 0.7 else "Potential",
                    "id": s["source_brd_id"]
                })
                
            state["domain_data"]["sections"]["Predictive Suggestions (FAISS RAG)"] = suggestion_items

        state["processing_times"]["render"] = round(time.time() - start_time, 3)

    except Exception as e:
        state["error"] = f"Render agent error: {str(e)}"

    return state


if __name__ == "__main__":
    test_state = {
        "raw_input": "Test input",
        "source_type": "email",
        "classified_sentences": [
            {"text": "Must allow login.", "label": "functional_req", "confidence": 0.92},
        ],
        "rag_examples": [],
        "functional_reqs": [{"id": "FR-001", "text": "Must allow login.", "priority": 1, "moscow": "Must", "confidence": 0.92, "source_span": ""}],
        "nfrs": [],
        "stakeholders": [],
        "decisions": [],
        "timeline": [],
        "scope": {},
        "gaps": [],
        "completeness_score": 0.45,
        "priority_scores": [],
        "source_map": {},
        "processing_times": {"ingest": 0.01, "classifier": 0.12, "rag": 0.5, "extractor": 3.2},
        "analytics": {},
        "retry_count": 0,
        "error": None,
    }

    result = render_agent(test_state)
    print("Render agent output:")
    print(f"  Total time  : {result['analytics']['total_processing_time']}s")
    print(f"  Completeness: {result['analytics']['completeness_score']:.1%}")
    print(f"  Req types   : {result['analytics']['req_type_breakdown']}")
    print(f"  Scope set   : {bool(result['scope'])}")
