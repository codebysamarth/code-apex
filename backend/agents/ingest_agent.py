"""
Ingest Agent
============
First agent in the pipeline. Detects the input type (email/meeting/chat/document),
cleans the raw text, and initialises the pipeline state.
"""

import re
import time
from state import BRDState


def _detect_source_type(text: str, hint: str | None = None) -> str:
    """
    Detect whether the text is an email, meeting transcript, chat, or document.
    Uses the hint if provided, otherwise falls back to heuristics.
    """
    if hint and hint in {"email", "meeting", "chat", "document"}:
        return hint

    text_lower = text.lower()

    # Email signals
    if any(kw in text_lower for kw in ["from:", "to:", "subject:", "cc:", "dear ", "regards,"]):
        return "email"

    # Meeting transcript signals
    if any(kw in text_lower for kw in ["[00:", "speaker", "facilitator", "attendees:", "minutes of"]):
        return "meeting"

    # Chat signals
    if re.search(r"^\[?\d{1,2}:\d{2}", text, re.MULTILINE):
        return "chat"

    return "document"


def _clean_text(text: str) -> str:
    """
    Normalize whitespace, remove zero-width characters, and trim.
    Does NOT strip content — the classifier and extractor need full context.
    """
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)   # zero-width chars
    text = re.sub(r"\r\n", "\n", text)                        # normalize line endings
    text = re.sub(r"\t", " ", text)                           # tabs → spaces
    text = re.sub(r" {3,}", "  ", text)                       # collapse excessive spaces
    text = re.sub(r"\n{4,}", "\n\n\n", text)                  # collapse excessive blank lines
    return text.strip()


def ingest_agent(state: BRDState) -> BRDState:
    """
    Cleans raw input, detects source type, and initialises pipeline state fields.

    Args:
        state: BRDState with raw_input and source_type (may be empty string)

    Returns:
        Updated BRDState with cleaned raw_input and detected source_type
    """
    start_time = time.time()

    try:
        raw = state.get("raw_input", "")
        if not raw or not raw.strip():
            state["error"] = "Input text is empty. Please paste some corporate communication."
            return state

        cleaned = _clean_text(raw)
        source_type = _detect_source_type(cleaned, state.get("source_type"))

        state["raw_input"] = cleaned
        state["source_type"] = source_type

        # Initialise all list/dict fields to avoid KeyError downstream
        state.setdefault("classified_sentences", [])
        state.setdefault("rag_examples", [])
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
        state.setdefault("processing_times", {})
        state.setdefault("analytics", {})
        state.setdefault("retry_count", 0)
        state.setdefault("error", None)

        state["processing_times"]["ingest"] = round(time.time() - start_time, 3)

    except Exception as e:
        state["error"] = f"Ingest agent error: {str(e)}"

    return state


if __name__ == "__main__":
    sample = {
        "raw_input": """
From: sarah@acme.com
To: team@acme.com
Subject: Q3 Dashboard Project

Hi Team,

The system must allow users to log in with SSO.
The API response time must be under 200ms.
We decided to use Stripe for payments in Q3 2024.
Sarah will own the sign-off process.
        """,
        "source_type": "",
        "classified_sentences": [],
        "rag_examples": [],
        "functional_reqs": [],
        "nfrs": [],
        "stakeholders": [],
        "decisions": [],
        "timeline": [],
        "scope": {},
        "gaps": [],
        "completeness_score": 0.0,
        "priority_scores": [],
        "source_map": {},
        "processing_times": {},
        "analytics": {},
        "retry_count": 0,
        "error": None,
    }

    result = ingest_agent(sample)
    print(f"Source type detected : {result['source_type']}")
    print(f"Cleaned text length  : {len(result['raw_input'])} chars")
    print(f"Processing time      : {result['processing_times'].get('ingest')}s")
