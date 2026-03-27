"""
Critique Agent
==============
Uses Gemini Flash 2.5 (via LangChain ChatGoogleGenerativeAI) to review the extracted BRD
and identify gaps, vague requirements, and missing sections.

Falls back to rule-based gap detection if LLM unavailable.

Temperature=0 for consistent critique output.
"""

import re
import json
import time
from state import BRDState
from mcp_config import get_llm_safe


def _build_critique_prompt(state: BRDState) -> str:
    """Build the critique prompt with extracted BRD content."""
    frs = state.get("functional_reqs", [])
    nfrs = state.get("nfrs", [])
    stakeholders = state.get("stakeholders", [])
    decisions = state.get("decisions", [])
    timeline = state.get("timeline", [])
    scope = state.get("scope", {})

    fr_block = "\n".join(
        f"  {r['id']}: [{r['moscow']}] {r['text']}" for r in frs
    ) or "  (none)"

    nfr_block = "\n".join(
        f"  {r['id']}: [{r['category']}] {r['text']}" for r in nfrs
    ) or "  (none)"

    stakeholder_block = "\n".join(
        f"  {s['name']} — {s['role']}" for s in stakeholders
    ) or "  (none)"

    decision_block = "\n".join(
        f"  {d['id']}: {d['text']}" for d in decisions
    ) or "  (none)"

    prompt = f"""You are a Principal Business Auditor with 20 years of experience in project risk mitigation.
Review the following BRD extraction for high-impact gaps, ambiguities, and architectural risks.

=== EXTRACTED BRD ===

FUNCTIONAL REQUIREMENTS ({len(frs)} total):
{fr_block}

NON-FUNCTIONAL REQUIREMENTS ({len(nfrs)} total):
{nfr_block}

STAKEHOLDERS ({len(stakeholders)} total):
{stakeholder_block}

DECISIONS ({len(decisions)} total):
{decision_block}

TIMELINE ITEMS: {len(timeline)}

SCOPE:
  In scope  : {len(scope.get("in_scope", []))} items
  Out of scope: {len(scope.get("out_of_scope", []))} items
  Assumptions: {len(scope.get("assumptions", []))} items

=== YOUR AUDIT CRITERIA ===
Focus on these critical failure points:
1. **Ambiguous Actions**: Requirements using 'support', 'manage', or 'interface' without specifying HOW.
2. **Missing Metrics**: NFRs without measurable thresholds (e.g., "fast" vs "<200ms").
3. **Single Points of Failure**: Functional requirements without a technical lead or owner assigned.
4. **Conflicting Decisions**: Decisions that contradict functional requirements or constraints.
5. **Timeline Gaps**: Requirements that imply a sequence (e.g. 'after login') but lack dependency mapping.
6. **Scope Creep**: Vague 'in-scope' items that could balloon without 'out-of-scope' boundaries.

=== OUTPUT SPECIFICATION ===
Return ONLY a valid JSON object. No preamble. No markdown.
{{
  "gaps": [
    {{
      "gap": "Specific description of the risk",
      "severity": "critical|high|medium|low",
      "suggestion": "Actionable architect-level recommendation"
    }}
  ]
}}

Audit the BRD now:"""
    return prompt


def _rule_based_gaps(state: BRDState) -> list[dict]:
    """
    Rule-based gap detection fallback when LLM is unavailable.
    Checks common BRD quality issues without an LLM.
    """
    gaps = []
    frs = state.get("functional_reqs", [])
    nfrs = state.get("nfrs", [])
    stakeholders = state.get("stakeholders", [])
    decisions = state.get("decisions", [])
    timeline = state.get("timeline", [])
    scope = state.get("scope", {})

    # Check 1: No functional requirements
    if not frs:
        gaps.append({
            "gap": "No functional requirements extracted",
            "severity": "critical",
            "suggestion": "Review the input text for statements containing 'must', 'shall', 'should', or 'required to'",
        })

    # Check 2: No NFRs
    if not nfrs:
        gaps.append({
            "gap": "No non-functional requirements found",
            "severity": "high",
            "suggestion": "Add explicit performance targets (response time, uptime %), security requirements, and scalability goals",
        })

    # Check 3: Missing NFR categories
    if nfrs:
        nfr_categories = {r.get("category", "") for r in nfrs}
        for required_cat in ["Performance", "Security"]:
            if required_cat not in nfr_categories:
                gaps.append({
                    "gap": f"No {required_cat} NFR found",
                    "severity": "high",
                    "suggestion": f"Add explicit {required_cat.lower()} requirements with measurable targets",
                })

    # Check 4: Vague requirements (no numbers or metrics)
    for req in frs:
        text = req.get("text", "")
        if req.get("confidence", 1.0) < 0.7:
            gaps.append({
                "gap": f"{req['id']}: Low confidence requirement — may be vague or ambiguous",
                "severity": "medium",
                "suggestion": f"Clarify: '{text[:60]}' with specific acceptance criteria",
            })
            if len(gaps) >= 6:
                break

    # Check 5: No stakeholders
    if not stakeholders:
        gaps.append({
            "gap": "No stakeholders identified",
            "severity": "high",
            "suggestion": "Identify who owns each requirement, who approves, and who is impacted",
        })

    # Check 6: No timeline
    if not timeline:
        gaps.append({
            "gap": "No timeline or milestones found",
            "severity": "medium",
            "suggestion": "Add delivery milestones, sprint dates, and go-live target",
        })

    # Check 7: Empty scope
    if not scope.get("out_of_scope"):
        gaps.append({
            "gap": "No out-of-scope items defined",
            "severity": "medium",
            "suggestion": "Explicitly list what is NOT included to prevent scope creep",
        })

    return gaps[:8]


def critique_agent(state: BRDState) -> BRDState:
    """
    Reviews the extracted BRD and identifies gaps/issues.
    Uses Claude LLM if available, otherwise falls back to rule-based detection.
    """
    start_time = time.time()

    try:
        llm = get_llm_safe()

        if llm is not None:
            prompt = _build_critique_prompt(state)

            try:
                from langchain_core.messages import HumanMessage
                response = llm.invoke([HumanMessage(content=prompt)])
                response_text = response.content.strip()

                # Strip markdown fences
                response_text = re.sub(r"^```(?:json)?\n?", "", response_text)
                response_text = re.sub(r"\n?```$", "", response_text)

                parsed = json.loads(response_text)
                gaps = parsed.get("gaps", [])

            except (json.JSONDecodeError, Exception) as e:
                print(f"[CritiqueAgent] LLM error: {e} — using rule-based fallback")
                gaps = _rule_based_gaps(state)
        else:
            print("[CritiqueAgent] No API key — using rule-based gap detection")
            gaps = _rule_based_gaps(state)

        state["gaps"] = gaps
        state["processing_times"]["critique"] = round(time.time() - start_time, 3)

    except Exception as e:
        state["error"] = f"Critique agent error: {str(e)}"

    return state


if __name__ == "__main__":
    test_state = {
        "raw_input": "The system must allow login. The API should be fast.",
        "source_type": "email",
        "classified_sentences": [],
        "rag_examples": [],
        "functional_reqs": [
            {"id": "FR-001", "text": "The system must allow login.", "priority": 1, "moscow": "Must", "confidence": 0.9, "source_span": ""},
        ],
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

    result = critique_agent(test_state)
    print(f"Gaps found: {len(result['gaps'])}\n")
    for gap in result["gaps"]:
        print(f"  [{gap['severity']:8s}] {gap['gap']}")
        print(f"             → {gap['suggestion'][:80]}\n")
    print(f"Processing time: {result['processing_times'].get('critique')}s")
