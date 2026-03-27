
import re

def apply_post_processing_rules(text, ml_prediction, ml_confidence):
    """Override ML predictions for edge cases using expert heuristics."""
    s = text.lower()
    
    # 1. Stakeholders (Named Owners)
    if re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+will\s+own\b', text):
        return 'stakeholder', 0.90, True
    if re.search(r'\bwill\s+own\s+(the\s+)?(product|requirements?|design|feature|sign-off)', s):
        return 'stakeholder', 0.85, True
    if ml_confidence < 0.50 and re.search(r'\b(owns?|ownership|responsible\s+for|sign[\-\s]?off|approval)\b', s):
        return 'stakeholder', 0.70, True
    
    # 2. Non-Functional Requirements (Quantitative Metrics)
    if re.search(r'\b\d{1,3}[,\d]*\s*(concurrent|simultaneous|active)\s*users?\b', s):
        return 'nfr', 0.90, True
    if re.search(r'\b(support|handle|scale to)\s+\d{1,3}[,\d]*\s*users?\b', s):
        return 'nfr', 0.85, True
    if re.search(r'\b(within|under|less than)\s+\d+\s*(ms|milliseconds?|seconds?|minutes?)\b', s):
        return 'nfr', 0.90, True
    if re.search(r'\b(uptime|availability|reliability)\s+(of\s+)?\d{2,3}(\.\d+)?%\b', s):
        return 'nfr', 0.95, True
    if re.search(r'\b(without|no)\s+(performance\s+)?(degradation|slowdown|latency)\b', s):
        return 'nfr', 0.85, True

    # 3. Decisions (Commitments)
    if re.search(r'\b(we\s+)?(decided|agreed|chosen|selected|opted)\s+(to|on|for)\b', s):
        return 'decision', 0.90, True
    if re.search(r'\b(instead of|rather than|migration from)\b', s):
        return 'decision', 0.75, True

    # 4. Timeline / Milestones (Time-based triggers)
    if re.search(r'\b(target|launch|deadline|kick[\-\s]?off|go[\-\s]?live|milestone|sprint)\s+(by|on|in|is)\b', s):
        return 'timeline', 0.85, True
    if re.search(r'\b(q[1-4]|january|february|march|april|may|june|july|august|september|october|november|december)\s+202[0-9]\b', s):
        return 'timeline', 0.80, True

    # 5. Core Functional Requirements (Explicit Permissions)
    if re.search(r'\b(must|shall|should)\s+(be able to|support|allow|enable|provide|have)\b', s):
        if ml_prediction != 'functional_req':
            return 'functional_req', 0.75, True
    
    return ml_prediction, ml_confidence, False
