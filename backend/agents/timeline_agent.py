"""
Timeline Agent
==============
Extracts milestones, deadlines, sprints, and dates from the raw text
using regex patterns and NLTK sentence tokenization. Pure Python — no LLM.

Extracts:
- Explicit dates (Q1/Q2/Q3/Q4, month+year, ISO dates)
- Sprint mentions
- Go-live / launch / deadline markers
- Dependencies between milestones
- Urgency scoring (critical / high / medium / low)
"""

import re
import time
import nltk
from state import BRDState

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
QUARTER_PATTERN = re.compile(
    r"\b(Q[1-4])\s*(?:of\s*)?(?:')?(\d{2,4}|\bthis year\b|\bnext year\b)?\b",
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r"\b(20[2-3]\d)\b")  # Years 2020-2039
MONTH_YEAR_PATTERN = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December"
    r"|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\s+(\d{4}|\d{2})\b",
    re.IGNORECASE,
)
ISO_DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
RELATIVE_DATE_PATTERN = re.compile(
    r"\b(next week|next month|end of month|end of quarter|by friday|this sprint"
    r"|within \d+ (?:days?|weeks?|months?))\b",
    re.IGNORECASE,
)
SPRINT_PATTERN = re.compile(r"\bSprint\s*(\d+)\b", re.IGNORECASE)

MILESTONE_KEYWORDS = {
    "go-live": "go-live",
    "go live": "go-live",
    "launch": "go-live",
    "release": "go-live",
    "deploy": "go-live",
    "kick-off": "kickoff",
    "kickoff": "kickoff",
    "kick off": "kickoff",
    "start": "kickoff",
    "begin": "kickoff",
    "deadline": "deadline",
    "due": "deadline",
    "must be done": "deadline",
    "sprint": "sprint",
    "demo": "sprint",
    "review": "sprint",
    "sign-off": "deadline",
    "sign off": "deadline",
    "approval": "deadline",
    "handover": "deadline",
    "UAT": "deadline",
    "testing": "sprint",
}

URGENCY_KEYWORDS = {
    "critical": "critical",
    "asap": "critical",
    "urgent": "critical",
    "immediately": "critical",
    "high priority": "high",
    "must": "high",
    "required by": "high",
    "target": "medium",
    "planned": "medium",
    "expected": "medium",
    "nice to have": "low",
    "tentative": "low",
}


def _extract_date_from_sentence(sentence: str) -> str:
    """Extract the most specific date mention from a sentence."""
    # ISO date is most specific
    m = ISO_DATE_PATTERN.search(sentence)
    if m:
        return m.group(1)

    # Month + year
    m = MONTH_YEAR_PATTERN.search(sentence)
    if m:
        return f"{m.group(1)} {m.group(2)}"

    # Quarter with year
    m = QUARTER_PATTERN.search(sentence)
    if m:
        year = m.group(2) or ""
        # Handle 2-digit years
        if year and len(year) == 2:
            year = f"20{year}"
        return f"{m.group(1)} {year}".strip()

    # Just a year
    m = YEAR_PATTERN.search(sentence)
    if m:
        return m.group(1)

    # Sprint number
    m = SPRINT_PATTERN.search(sentence)
    if m:
        return f"Sprint {m.group(1)}"

    # Relative date
    m = RELATIVE_DATE_PATTERN.search(sentence)
    if m:
        return m.group(1)

    return ""


def _detect_milestone_type(sentence: str) -> str:
    """Detect the type of milestone from keyword matching."""
    s = sentence.lower()
    for keyword, mtype in MILESTONE_KEYWORDS.items():
        if keyword in s:
            return mtype
    return "milestone"


def _detect_urgency(sentence: str) -> str:
    """Detect urgency level from keyword matching."""
    s = sentence.lower()
    for keyword, urgency in URGENCY_KEYWORDS.items():
        if keyword in s:
            return urgency
    return "medium"


def _extract_milestone_text(sentence: str) -> str:
    """Extract a clean milestone name from the sentence (max 80 chars)."""
    # Remove date patterns to get the action part
    clean = ISO_DATE_PATTERN.sub("", sentence)
    clean = QUARTER_PATTERN.sub("", clean)
    clean = MONTH_YEAR_PATTERN.sub("", clean)
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    return clean[:80] if clean else sentence[:80]


def _sentence_has_date_or_timeline(sentence: str) -> bool:
    """Quick check if a sentence contains any temporal marker."""
    s = sentence.lower()
    return bool(
        QUARTER_PATTERN.search(sentence)
        or MONTH_YEAR_PATTERN.search(sentence)
        or ISO_DATE_PATTERN.search(sentence)
        or SPRINT_PATTERN.search(sentence)
        or RELATIVE_DATE_PATTERN.search(sentence)
        or YEAR_PATTERN.search(sentence)
        or any(kw in s for kw in ["deadline", "launch", "go-live", "kickoff", "sprint", 
                                   "by end of", "target date", "due date", "timeline", 
                                   "milestone", "phase", "complete by", "deliver by"])
    )


def _infer_dependencies(milestones: list[dict]) -> list[dict]:
    """
    Add simple sequential dependencies: kickoffs → sprints → go-lives → deadlines.
    """
    type_order = {"kickoff": 0, "sprint": 1, "go-live": 2, "deadline": 3, "milestone": 1}
    sorted_ms = sorted(milestones, key=lambda m: type_order.get(m["type"], 1))

    for i, ms in enumerate(sorted_ms):
        if i > 0:
            prev = sorted_ms[i - 1]
            if type_order.get(prev["type"], 1) < type_order.get(ms["type"], 1):
                ms["dependencies"] = [prev["milestone"][:40]]
        else:
            ms["dependencies"] = []

    return sorted_ms


def timeline_agent(state: BRDState) -> BRDState:
    """
    Extracts timeline milestones from raw_input using regex + heuristics.
    Also uses pre-classified timeline sentences for higher recall.
    """
    start_time = time.time()

    try:
        raw = state.get("raw_input", "")
        classified = state.get("classified_sentences", [])

        # Collect candidate sentences: classified timeline + any sentence with date markers
        timeline_sentences = set()

        for item in classified:
            if item.get("label") == "timeline":
                timeline_sentences.add(item["text"])

        # Also scan all sentences for date markers
        for sent in nltk.sent_tokenize(raw):
            if _sentence_has_date_or_timeline(sent):
                timeline_sentences.add(sent.strip())

        milestones = []
        seen_texts: set[str] = set()

        for sentence in timeline_sentences:
            date_str = _extract_date_from_sentence(sentence)
            milestone_text = _extract_milestone_text(sentence)

            # Dedup by milestone text prefix
            key = milestone_text[:40].lower()
            if key in seen_texts:
                continue
            seen_texts.add(key)

            milestones.append({
                "milestone": milestone_text,
                "date": date_str,
                "type": _detect_milestone_type(sentence),
                "dependencies": [],
                "urgency": _detect_urgency(sentence),
                "raw_sentence": sentence,
            })

        # Infer dependencies between milestones
        if len(milestones) > 1:
            milestones = _infer_dependencies(milestones)

        # Sort: kickoff first, then sprint, then go-live, then deadline
        type_order = {"kickoff": 0, "sprint": 1, "milestone": 2, "go-live": 3, "deadline": 4}
        milestones.sort(key=lambda m: type_order.get(m["type"], 2))

        # Remove raw_sentence from final output (internal use only)
        for m in milestones:
            m.pop("raw_sentence", None)

        state["timeline"] = milestones
        state["processing_times"]["timeline"] = round(time.time() - start_time, 3)

    except Exception as e:
        state["error"] = f"Timeline agent error: {str(e)}"

    return state


if __name__ == "__main__":
    test_state = {
        "raw_input": (
            "The project kick-off is scheduled for March 2024. "
            "Sprint 1 will run through Q1 2024. "
            "The system must go live by June 2024. "
            "Final sign-off deadline is 2024-07-31. "
            "We need the dashboard demo by next month."
        ),
        "source_type": "email",
        "classified_sentences": [
            {"text": "The project kick-off is scheduled for March 2024.", "label": "timeline", "confidence": 0.91},
            {"text": "The system must go live by June 2024.", "label": "timeline", "confidence": 0.89},
        ],
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

    result = timeline_agent(test_state)
    print(f"Milestones extracted: {len(result['timeline'])}\n")
    for m in result["timeline"]:
        print(f"  [{m['type']:10s}] [{m['urgency']:8s}] {m['date']:15s} | {m['milestone']}")
    print(f"\nProcessing time: {result['processing_times'].get('timeline')}s")
