"""
Score Agent
===========
Pure Python scoring agent. No LLM required.

Computes:
1. Completeness score: how many AMI benchmark requirement types are covered
2. MoSCoW priority scores for all requirements
3. Value vs Effort matrix scores for Priorities tab
4. AMI benchmark recall comparison

All scores are 0.0–1.0 floats.
"""

import os
import json
import time
import math
from state import BRDState
from dotenv import load_dotenv

load_dotenv()

AMI_BENCHMARK_PATH = os.getenv("AMI_BENCHMARK_PATH", "./data/ami_benchmark.json")

# ---------------------------------------------------------------------------
# AMI benchmark loader
# ---------------------------------------------------------------------------
_ami_benchmark = None


def _load_ami_benchmark() -> dict:
    """Load AMI benchmark data for scoring comparison."""
    global _ami_benchmark
    if _ami_benchmark is None:
        if os.path.exists(AMI_BENCHMARK_PATH):
            with open(AMI_BENCHMARK_PATH, "r") as f:
                _ami_benchmark = json.load(f)
            print(f"[ScoreAgent] AMI benchmark loaded successfully")
        else:
            _ami_benchmark = {}
            print(f"[ScoreAgent] INFO: Using default scoring (no benchmark file)")
    return _ami_benchmark


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------
def _compute_completeness_score(state: BRDState) -> float:
    """
    Compute completeness score based on BRD section coverage.

    Scoring rubric (max 1.0):
    - Has functional requirements   : 0.30
    - Has NFRs                      : 0.20
    - Has stakeholders              : 0.15
    - Has timeline                  : 0.10
    - Has decisions                 : 0.10
    - Has scope definition          : 0.10
    - Low gap count (<3)            : 0.05
    """
    score = 0.0

    frs = state.get("functional_reqs", [])
    nfrs = state.get("nfrs", [])
    stakeholders = state.get("stakeholders", [])
    timeline = state.get("timeline", [])
    decisions = state.get("decisions", [])
    scope = state.get("scope", {})
    gaps = state.get("gaps", [])

    if frs:
        score += 0.30
        # Bonus for quality: multiple FRs
        if len(frs) >= 3:
            score += 0.05
    if nfrs:
        score += 0.20
    if stakeholders:
        score += 0.15
    if timeline:
        score += 0.10
    if decisions:
        score += 0.10
    if scope.get("in_scope") or scope.get("out_of_scope"):
        score += 0.10

    # Gap penalty
    critical_gaps = sum(1 for g in gaps if g.get("severity") == "critical")
    high_gaps = sum(1 for g in gaps if g.get("severity") == "high")
    gap_penalty = min(0.15, critical_gaps * 0.05 + high_gaps * 0.02)
    score = max(0.0, score - gap_penalty)

    return round(min(1.0, score), 3)


def _compute_ami_recall(state: BRDState) -> dict:
    """
    Compare extracted requirements against AMI benchmark averages.
    Returns recall metrics for the Analytics vs AMI Benchmark card.
    """
    benchmark = _load_ami_benchmark()

    # Get benchmark targets (use defaults if no benchmark)
    fr_target = benchmark.get("functional_requirements", {}).get("count", 50) if benchmark else 50
    nfr_target = sum(benchmark.get("non_functional_requirements", {}).values()) if benchmark else 50
    stakeholder_target = benchmark.get("stakeholders", {}).get("count", 20) if benchmark else 20
    total_target = benchmark.get("total_requirements", 100) if benchmark else 100

    extracted_reqs = len(state.get("functional_reqs", []))
    extracted_nfrs = len(state.get("nfrs", []))
    extracted_stakeholders = len(state.get("stakeholders", []))
    extracted_timeline = len(state.get("timeline", []))

    # Recall = extracted / expected (scaled for typical single-document extraction)
    # A single email/document typically has 3-10 requirements, not 50
    # Scale expectations: single doc ~= 10% of full project
    scale_factor = 0.1
    
    fr_recall = min(1.0, extracted_reqs / max(1, fr_target * scale_factor))
    nfr_recall = min(1.0, extracted_nfrs / max(1, nfr_target * scale_factor))
    stakeholder_recall = min(1.0, extracted_stakeholders / max(1, stakeholder_target * scale_factor))
    timeline_recall = min(1.0, extracted_timeline / 3)  # 3 milestones is reasonable for single doc
    
    overall_recall = (fr_recall + nfr_recall + stakeholder_recall + timeline_recall) / 4

    return {
        "fr_recall": round(fr_recall, 3),
        "nfr_recall": round(nfr_recall, 3),
        "stakeholder_recall": round(stakeholder_recall, 3),
        "timeline_recall": round(timeline_recall, 3),
        "overall_recall": round(overall_recall, 3),
        "benchmark_total": total_target,
    }


def _compute_moscow_scores(state: BRDState) -> list[dict]:
    """
    Compute MoSCoW priority scores and value/effort matrix for each requirement.
    Priority scores are used by the Priorities tab.
    """
    priority_scores = []
    frs = state.get("functional_reqs", [])
    nfrs = state.get("nfrs", [])

    moscow_value = {"Must": 1.0, "Should": 0.7, "Could": 0.4, "Wont": 0.1}

    for req in frs:
        moscow = req.get("moscow", "Should")
        confidence = req.get("confidence", 0.7)
        priority = req.get("priority", 2)

        # Value score: based on MoSCoW + confidence
        value_score = round(moscow_value.get(moscow, 0.5) * confidence, 3)

        # Effort score: heuristic based on text complexity
        text = req.get("text", "")
        word_count = len(text.split())
        effort_score = round(min(1.0, 0.2 + (word_count / 40)), 3)

        priority_scores.append({
            "req_id": req.get("id", "FR-???"),
            "req_type": "FR",
            "moscow": moscow,
            "priority": priority,
            "value_score": value_score,
            "effort_score": effort_score,
            "confidence": confidence,
        })

    for req in nfrs:
        nfr_category = req.get("category", "")
        # NFRs are always high value
        value_score = round(0.9 * req.get("confidence", 0.8), 3)
        effort_score = round(min(1.0, 0.5), 3)

        priority_scores.append({
            "req_id": req.get("id", "NFR-???"),
            "req_type": "NFR",
            "moscow": "Must" if nfr_category in ["Performance", "Security"] else "Should",
            "priority": 1,
            "value_score": value_score,
            "effort_score": effort_score,
            "confidence": req.get("confidence", 0.8),
        })

    return priority_scores


def score_agent(state: BRDState) -> BRDState:
    """
    Computes completeness score, MoSCoW priority scores, and AMI recall metrics.
    Pure Python — no LLM calls.
    """
    start_time = time.time()

    try:
        # 1. Completeness score
        completeness = _compute_completeness_score(state)
        state["completeness_score"] = completeness

        # 2. MoSCoW + value/effort scores
        priority_scores = _compute_moscow_scores(state)
        state["priority_scores"] = priority_scores

        # 3. AMI recall metrics
        ami_recall = _compute_ami_recall(state)

        # 4. Update analytics
        state.setdefault("analytics", {})
        state["analytics"]["completeness_score"] = completeness
        state["analytics"]["ami_recall"] = ami_recall
        state["analytics"]["total_requirements"] = (
            len(state.get("functional_reqs", []))
            + len(state.get("nfrs", []))
        )

        # MoSCoW distribution
        moscow_dist = {"Must": 0, "Should": 0, "Could": 0, "Wont": 0}
        for ps in priority_scores:
            cat = ps.get("moscow", "Should")
            moscow_dist[cat] = moscow_dist.get(cat, 0) + 1
        state["analytics"]["moscow_distribution"] = moscow_dist

        state["processing_times"]["score"] = round(time.time() - start_time, 3)

    except Exception as e:
        state["error"] = f"Score agent error: {str(e)}"

    return state


if __name__ == "__main__":
    test_state = {
        "raw_input": "Sample text",
        "source_type": "email",
        "classified_sentences": [],
        "rag_examples": [],
        "functional_reqs": [
            {"id": "FR-001", "text": "System must allow login.", "priority": 1, "moscow": "Must", "confidence": 0.9, "source_span": ""},
            {"id": "FR-002", "text": "Users must be able to reset passwords.", "priority": 1, "moscow": "Must", "confidence": 0.88, "source_span": ""},
            {"id": "FR-003", "text": "Dashboard should show analytics.", "priority": 2, "moscow": "Should", "confidence": 0.75, "source_span": ""},
        ],
        "nfrs": [
            {"id": "NFR-001", "text": "API must respond under 200ms.", "category": "Performance", "priority": 1, "confidence": 0.91},
        ],
        "stakeholders": [{"name": "Sarah", "role": "Product Owner", "influence_score": 0.9, "mentioned_count": 3}],
        "decisions": [{"id": "DEC-001", "text": "Use Stripe for payments.", "rationale": "", "date_mentioned": ""}],
        "timeline": [{"milestone": "Q3 launch", "date": "Q3 2024", "type": "go-live", "dependencies": [], "urgency": "high"}],
        "scope": {"in_scope": ["Dashboard", "Auth"], "out_of_scope": ["Mobile app"], "assumptions": ["SSO available"]},
        "gaps": [{"gap": "No security NFR", "severity": "high", "suggestion": "Add security requirements"}],
        "completeness_score": 0.0,
        "priority_scores": [],
        "source_map": {},
        "processing_times": {},
        "analytics": {},
        "retry_count": 0,
        "error": None,
    }

    result = score_agent(test_state)
    print(f"Completeness score : {result['completeness_score']:.1%}")
    print(f"Priority scores    : {len(result['priority_scores'])} items")
    print(f"AMI recall         : {result['analytics']['ami_recall']['overall_recall']:.1%}")
    print(f"Processing time    : {result['processing_times'].get('score')}s")
