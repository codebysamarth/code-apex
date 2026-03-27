"""
BRD Agent State Schema
======================
Central TypedDict that flows through the entire 7-agent LangGraph pipeline.
Every agent reads from and writes to this state object.
"""

from typing import TypedDict, Optional


class BRDState(TypedDict):
    # Raw text pasted by the user (email, meeting transcript, chat, or document)
    raw_input: str

    # Detected input type: "email" | "meeting" | "chat" | "document"
    source_type: str

    # Output of ML Classifier Agent: each sentence with its label and confidence score
    # Each item: {text: str, label: str, confidence: float, normalized_text: str}
    classified_sentences: list[dict]

    # Output of RAG Agent: top-3 similar examples retrieved from ChromaDB
    # Each item: {text: str, label: str, source: str, similarity: float}
    rag_examples: list[dict]

    # Functional requirements extracted by the Extractor Agent
    # Each item: {id: str, text: str, priority: int, moscow: str, confidence: float, source_span: str}
    functional_reqs: list[dict]

    # Non-functional requirements extracted by the Extractor Agent
    # Each item: {id: str, text: str, category: str, priority: int, confidence: float}
    nfrs: list[dict]

    # Stakeholders identified from the input text
    # Each item: {name: str, role: str, influence_score: float, mentioned_count: int}
    stakeholders: list[dict]

    # Decisions captured from the input text
    # Each item: {id: str, text: str, rationale: str, date_mentioned: str}
    decisions: list[dict]

    # Timeline milestones extracted by the Timeline Agent
    # Each item: {milestone: str, date: str, type: str, dependencies: list, urgency: str}
    timeline: list[dict]

    # Scope definition extracted from the input
    # Structure: {in_scope: list[str], out_of_scope: list[str], assumptions: list[str]}
    scope: dict

    # Gaps and critique from the Critique Agent
    # Each item: {gap: str, severity: str, suggestion: str}
    gaps: list[dict]

    # Overall completeness score (0.0 to 1.0) compared against AMI benchmark
    completeness_score: float

    # Priority scores for each requirement (MoSCoW analysis)
    # Each item: {req_id: str, moscow: str, value_score: float, effort_score: float}
    priority_scores: list[dict]

    # Maps requirement IDs to their source character positions in raw_input
    # Structure: {req_id: {start: int, end: int, text: str}}
    source_map: dict

    # Time taken by each agent in seconds
    # Structure: {agent_name: float}
    processing_times: dict

    # Aggregated analytics for the Analytics tab
    # Includes: confidence_distribution, rag_source_breakdown, label_counts, etc.
    analytics: dict

    # Number of pipeline retries attempted (used by should_retry logic)
    retry_count: int

    # Error message if any agent fails; None on success
    error: Optional[str]
