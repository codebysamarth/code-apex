"""
Extractor Agent
===============
Uses Gemini Flash 2.5 (via LangChain ChatGoogleGenerativeAI) to read classified sentences
and RAG examples, then outputs a structured BRD JSON with:
- Functional requirements (FRs)
- Non-functional requirements (NFRs)
- Stakeholders
- Decisions
- Scope (in/out/assumptions)
- Source map (character positions in raw text)
- Confidence explanations (reasoning for each extraction)

Features:
- Chain-of-thought reasoning for better accuracy
- Few-shot examples for consistent output format
- Confidence explanations showing WHY each item was extracted

Temperature=0 for deterministic extraction.
Falls back to regex-based extraction if LLM unavailable.
"""

import re
import json
import time
from state import BRDState
from mcp_config import get_llm_safe

# ---------------------------------------------------------------------------
# Few-Shot Examples for Consistent Extraction
# ---------------------------------------------------------------------------
FEW_SHOT_EXAMPLES = """
=== EXAMPLE 1: Email about Authentication System ===
INPUT: "Hi team, after our discussion, we need the login page to support SSO with Google and Microsoft. 
John (our security lead) mentioned we must have 2FA for all admin accounts. 
The login should complete within 2 seconds. Target launch is March 2025."

REASONING (Chain of Thought):
1. "login page to support SSO with Google and Microsoft" → This is a FUNCTIONAL requirement because it describes a specific feature the system must do. MoSCoW = Must (critical functionality)
2. "must have 2FA for all admin accounts" → FUNCTIONAL requirement for security feature. The word "must" indicates Must priority.
3. "login should complete within 2 seconds" → NON-FUNCTIONAL (Performance) because it's about how fast, not what it does.
4. "John (our security lead)" → STAKEHOLDER - named person with a role.
5. "Target launch is March 2025" → TIMELINE milestone.

OUTPUT:
{
  "functional_reqs": [
    {"id": "FR-001", "text": "Login page must support SSO with Google and Microsoft", "priority": 1, "moscow": "Must", "confidence": 0.95, "source_span": "login page to support SSO with Google and Microsoft", "reasoning": "Explicit feature request for SSO integration with specific providers"},
    {"id": "FR-002", "text": "All admin accounts must have 2FA enabled", "priority": 1, "moscow": "Must", "confidence": 0.92, "source_span": "must have 2FA for all admin accounts", "reasoning": "Security requirement with 'must' keyword indicating mandatory"}
  ],
  "nfrs": [
    {"id": "NFR-001", "text": "Login should complete within 2 seconds", "category": "Performance", "priority": 1, "confidence": 0.88, "reasoning": "Performance metric with specific time constraint"}
  ],
  "stakeholders": [
    {"name": "John", "role": "Security Lead", "influence_score": 0.85, "mentioned_count": 1, "reasoning": "Explicitly named with role 'security lead', involved in security decisions"}
  ]
}

=== EXAMPLE 2: Meeting Notes about E-commerce Platform ===
INPUT: "Meeting notes: Sarah (PM) wants the checkout to accept Visa, Mastercard, and PayPal.
Mike from DevOps said the API needs to handle 1000 requests per second.
We decided to use Stripe over Square because of better international support.
Mobile app is out of scope for v1."

REASONING (Chain of Thought):
1. "checkout to accept Visa, Mastercard, and PayPal" → FUNCTIONAL requirement - specific payment methods to support
2. "API needs to handle 1000 requests per second" → NON-FUNCTIONAL (Scalability/Performance) - capacity requirement
3. "decided to use Stripe over Square because of better international support" → DECISION with rationale
4. "Mobile app is out of scope for v1" → SCOPE (out_of_scope item)
5. "Sarah (PM)", "Mike from DevOps" → STAKEHOLDERS with roles

OUTPUT:
{
  "functional_reqs": [
    {"id": "FR-001", "text": "Checkout must accept Visa, Mastercard, and PayPal payment methods", "priority": 1, "moscow": "Must", "confidence": 0.93, "source_span": "checkout to accept Visa, Mastercard, and PayPal", "reasoning": "Clear feature requirement listing specific payment methods needed"}
  ],
  "nfrs": [
    {"id": "NFR-001", "text": "API must handle 1000 requests per second", "category": "Scalability", "priority": 1, "confidence": 0.90, "reasoning": "Explicit capacity requirement with measurable metric"}
  ],
  "stakeholders": [
    {"name": "Sarah", "role": "Product Manager", "influence_score": 0.9, "mentioned_count": 1, "reasoning": "Named as PM, driving feature requirements"},
    {"name": "Mike", "role": "DevOps Engineer", "influence_score": 0.75, "mentioned_count": 1, "reasoning": "From DevOps team, involved in technical capacity decisions"}
  ],
  "decisions": [
    {"id": "DEC-001", "text": "Use Stripe for payment processing instead of Square", "rationale": "Better international support", "date_mentioned": "", "reasoning": "Explicit decision with comparison and justification provided"}
  ],
  "scope": {
    "in_scope": ["Checkout with payment processing"],
    "out_of_scope": ["Mobile app (explicitly excluded for v1)"],
    "assumptions": []
  }
}
"""


def _build_extraction_prompt(state: BRDState) -> str:
    """Build the structured extraction prompt with chain-of-thought and few-shot examples."""
    classified = state.get("classified_sentences", [])
    rag_examples = state.get("rag_examples", [])
    source_type = state.get("source_type", "document")
    raw_input = state.get("raw_input", "")

    # Format classified sentences by label
    by_label: dict[str, list[str]] = {}
    for item in classified:
        label = item["label"]
        if label == "noise":
            continue
        by_label.setdefault(label, []).append(
            f"  [{item['confidence']:.2f}] {item['text']}"
        )

    classified_block = ""
    for label, sentences in by_label.items():
        classified_block += f"\n{label.upper()}:\n" + "\n".join(sentences) + "\n"

    # Format RAG examples (top 6 most similar)
    rag_block = ""
    for ex in rag_examples[:6]:
        rag_block += f"  [{ex['source']}|{ex['similarity']:.2f}] {ex['text'][:100]}\n"

    prompt = f"""You are a Principal Business Analyst & Solution Architect with expertise in extracting high-fidelity requirements from complex stakeholder communications.

=== YOUR MISSION ===
Analyze the provided {source_type} and transform it into a mathematically sound, structured BRD. 
You must identify explicitly stated requirements while detecting the underlying business intent.

=== ARCHITECTURAL PRINCIPLES ===
1. **Zero Inference**: Standardize the language, but do NOT add features not mentioned.
2. **MoSCoW Precision**: 
   - [Must] = Mandatory for launch. Keywords: 'must', 'required', 'critical', 'essential', 'legally compliant'.
   - [Should] = High priority but launchable without. Keywords: 'should', 'expected', 'highly recommended'.
   - [Could] = Desirable. Keywords: 'could', 'nice-to-have', 'optional', 'if time permits'.
   - [Wont] = Out of scope for this phase. Keywords: 'wont', 'excluded', 'future iteration'.
3. **NFR Categorization**: Map every quantitative or qualitative constraint to its specific architectural pillar (Security, Performance, etc.).
4. **Entity Integrity**: Stakeholders must be actual named individuals or specific team titles. NEVER extract generic words like 'Users', 'Stakeholders', 'Customers', or 'Team' as a stakeholder's name.

=== FEW-SHOT EXAMPLES ===
{FEW_SHOT_EXAMPLES}

=== PRE-CLASSIFIED CONTEXT ===
{classified_block if classified_block else "(none found)"}

=== SIMILAR HISTORICAL PATTERNS ===
{rag_block if rag_block else "(none available)"}

=== SOURCE MATERIAL ===
{raw_input}

=== STEP-BY-STEP REASONING (CoT) ===
Before your JSON output, internally analyze:
- "Is this sentence a functional action or a structural constraint?"
- "Does this person have the authority to influence the design?"
- "What architectural category does this performance requirement impact?"

=== REQUIREMENT JSON SCHEMA ===
Return ONLY the following JSON structure:
{{
  "functional_reqs": [
    {{
      "id": "FR-XXX",
      "text": "The [system] shall [action]...",
      "priority": 1,
      "moscow": "Must|Should|Could|Wont",
      "confidence": 0.0-1.0,
      "source_span": "direct quote",
      "reasoning": "Analysis of intensity and category"
    }}
  ],
  "nfrs": [
    {{
      "id": "NFR-XXX",
      "text": "Measurement or quality constraint",
      "category": "Performance|Security|Reliability|Scalability|Usability|Maintainability",
      "priority": 1|2,
      "confidence": 0.0-1.0,
      "reasoning": "Categorization logic"
    }}
  ],
  "stakeholders": [
    {{
      "name": "Full Name",
      "role": "Role (e.g. CTO, PM)",
      "influence_score": 0.0-1.0,
      "mentioned_count": X,
      "reasoning": "Impact on requirements"
    }}
  ],
  "decisions": [
    {{
      "id": "DEC-XXX",
      "text": "What was selected/finalized",
      "rationale": "Why this path was chosen",
      "date_mentioned": "Date or Q-target",
      "reasoning": "Identifier for commitment"
    }}
  ],
  "scope": {{
    "in_scope": ["features included"],
    "out_of_scope": ["explicit exclusions"],
    "assumptions": ["stated assumptions"]
  }}
}}

=== FINAL DIRECTIVE ===
Extract ALL unique entities. If a category is empty, use empty list []. JSON ONLY.

Go:"""
    return prompt


def assign_moscow_priority(text: str) -> str:
    """Classify a requirement into MoSCoW priority based on keyword analysis."""
    text_lower = text.lower()
    
    # Must: Critical, Mandatory, Non-negotiable
    if any(kw in text_lower for kw in ["must", "required", "critical", "mandatory", "essential", "have to", "shall", "non-negotiable", "fundamental"]):
        return "Must"
    
    # Should: Recommended, Important, Expected
    if any(kw in text_lower for kw in ["should", "recommended", "important", "expected", "highly desirable", "high priority"]):
        return "Should"
    
    # Could: Optional, Nice-to-have, If time permits
    if any(kw in text_lower for kw in ["could", "optional", "nice-to-have", "if time permits", "desirable", "maybe"]):
        return "Could"
    
    # Wont: Out of scope, Future, Excluded
    if any(kw in text_lower for kw in ["won't", "wont", "not in scope", "out of scope", "future iteration", "excluded", "not required", "phase 2"]):
        return "Wont"
        
    return "Should"  # Default to Should for meaningful items


def _regex_fallback_extract(state: BRDState) -> dict:
    """
    Enhanced fallback extractor using both classifier output AND keyword patterns.
    Catches items that classifier might miss due to lower confidence categories.
    """
    classified = state.get("classified_sentences", [])
    raw = state.get("raw_input", "")

    fr_counter = 1
    nfr_counter = 1
    dec_counter = 1
    functional_reqs = []
    nfrs = []
    stakeholders = []
    decisions = []
    scope = {"in_scope": [], "out_of_scope": [], "assumptions": []}
    
    seen_texts = set()  # Avoid duplicates

    # 1. Process classifier output
    for item in classified:
        text = item["text"]
        label = item["label"]
        conf = item["confidence"]
        
        text_key = text.lower()[:50]
        if text_key in seen_texts:
            continue
        seen_texts.add(text_key)

        if label == "functional_req":
            try:
                moscow = assign_moscow_priority(text)
            except:
                moscow = "Should"
            functional_reqs.append({
                "id": f"FR-{fr_counter:03d}",
                "text": text,
                "priority": 1 if conf > 0.8 else 2,
                "moscow": moscow,
                "confidence": conf,
                "source_span": text[:80],
                "reasoning": f"Classified as functional requirement by ML model with {conf:.0%} confidence. MoSCoW={moscow} based on keyword analysis.",
            })
            fr_counter += 1

        elif label == "nfr":
            cat = _detect_nfr_category(text)
            nfrs.append({
                "id": f"NFR-{nfr_counter:03d}",
                "text": text,
                "category": cat,
                "priority": 1,
                "confidence": conf,
                "reasoning": f"Classified as NFR ({cat}) by ML model. Contains quality/constraint language.",
            })
            nfr_counter += 1

        elif label == "stakeholder":
            name_match = re.search(r"\b([A-Z][a-z]+ [A-Z][a-z]+|[A-Z][a-z]+)\b", text)
            name = name_match.group(0) if name_match else "Unknown Stakeholder"
            count = raw.lower().count(name.lower())
            stakeholders.append({
                "name": name,
                "role": _detect_role(text),
                "influence_score": round(conf, 2),
                "mentioned_count": count,
                "reasoning": f"Named entity detected in stakeholder context. Mentioned {count} time(s).",
            })

        elif label == "decision":
            decisions.append({
                "id": f"DEC-{dec_counter:03d}",
                "text": text,
                "rationale": "",
                "date_mentioned": "",
                "reasoning": "Contains decision language (decided, agreed, chosen, selected).",
            })
                # 2. Keyword-based extraction for items classifier might miss
    import nltk
    try:
        sentences = nltk.sent_tokenize(raw)
    except:
        sentences = raw.split('.') # Fallback if nltk not ready
    
    # Patterns for direct extraction
    fr_patterns = [
        r"(?:must|shall|should|need to|require)\s+(?:be able to|support|allow|enable|provide|have|process)",
        r"(?:system|application|platform|service|dashboard)\s+(?:must|shall|should|will)\s+",
        r"user(?:s)?\s+(?:must|shall|should|can|will)\s+(?:be able to|access|manage|view|create)",
    ]
    
    nfr_patterns = [
        r"(?:within|under|less than|latency of)\s+\d+\s*(?:ms|milliseconds?|seconds?|minutes?)",
        r"\d+(\.\d+)?%?\s+(?:uptime|availability|reliability|SLA)",
        r"(?:encrypt|secure|auth|password|ssl|tls|https|MFA|AES|compliance)",
        r"(?:scalab|concurrent|throughput|capacity|load|10k|100k|million)",
    ]
    
    stakeholder_patterns = [
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\(([^)]+)\)",  # Name (Role)
        r"([A-Z][a-z]+)\s+(?:is the|serves as|working as)\s+(?:a|the)?\s+(\w+(?:\s+\w+)?)",  # Name is Role
        r"([A-Z][a-z]+)\s+from\s+(\w+(?:\s+\w+)?)", # Name from Team
    ]
    
    decision_patterns = [
        r"(?:we |team |project |it was |is )\s*(?:decided|agreed|chosen|selected|opted|migrated)\s*(?:to|on|for|from)",
        r"(?:approved|confirmed|finalized)\s+(?:the use of|to|that)",
        r"(?:choice of|decision to|selected vendor|using)\s+([^.]*)(?:instead of|rather than)",
    ]
    
    for sent in sentences:
        text_key = sent.lower()[:50]
        if text_key in seen_texts or len(sent.split()) < 3:
            continue
        
        # Check for functional requirements
        for pattern in fr_patterns:
            if re.search(pattern, sent, re.IGNORECASE):
                seen_texts.add(text_key)
                try:
                    moscow = assign_moscow_priority(sent)
                except:
                    moscow = "Should"
                functional_reqs.append({
                    "id": f"FR-{fr_counter:03d}",
                    "text": sent.strip(),
                    "priority": 1 if moscow == "Must" else 2,
                    "moscow": moscow,
                    "confidence": 0.75,
                    "source_span": sent[:80],
                    "reasoning": f"Heuristic match: Requirement pattern with MoSCoW={moscow}.",
                })
                fr_counter += 1
                break
        
        # Check for NFRs
        for pattern in nfr_patterns:
            if re.search(pattern, sent, re.IGNORECASE) and text_key not in seen_texts:
                seen_texts.add(text_key)
                cat = _detect_nfr_category(sent)
                nfrs.append({
                    "id": f"NFR-{nfr_counter:03d}",
                    "text": sent.strip(),
                    "category": cat,
                    "priority": 1 if cat in ["Security", "Reliability"] else 2,
                    "confidence": 0.80,
                    "reasoning": f"Heuristic match: Qualitative constraint detected for {cat}.",
                })
                nfr_counter += 1
                break
        
        # Check for stakeholders
        for pattern in stakeholder_patterns:
            match = re.search(pattern, sent)
            if match and text_key not in seen_texts:
                name = match.group(1)
                role = match.group(2) if len(match.groups()) > 1 else "Stakeholder"
                
                # Validation: avoid common words and generic entities
                noise_names = {
                    "the", "this", "our", "all", "we", "i", "you", "them",
                    "stakeholder", "stakeholders", "user", "users", "customer", "customers",
                    "system", "application", "platform", "server", "database", "api",
                    "team", "project", "program", "milestone", "requirement", "requirements",
                    "meeting", "sync", "discussion", "email", "document", "file"
                }
                if name.lower().strip() in noise_names or len(name.strip()) < 2:
                    continue
                
                if name.lower() not in [s.get("name", "").lower() for s in stakeholders]:
                    stakeholders.append({
                        "name": name,
                        "role": _detect_role(sent) or role,
                        "influence_score": 0.7,
                        "mentioned_count": raw.lower().count(name.lower()),
                        "reasoning": f"Entity pattern: {name} in a {role} context.",
                    })
                break
        
        # Check for decisions
        for pattern in decision_patterns:
            if re.search(pattern, sent, re.IGNORECASE) and text_key not in seen_texts:
                seen_texts.add(text_key)
                decisions.append({
                    "id": f"DEC-{dec_counter:03d}",
                    "text": sent.strip(),
                    "rationale": "Explicitly stated in project history.",
                    "date_mentioned": "",
                    "reasoning": "Heuristic match: Commitment language (decision/choice).",
                })
                dec_counter += 1
                break

    # Basic scope from functional reqs
    scope["in_scope"] = [r["text"][:60] for r in functional_reqs[:3]]
    out_scope_match = re.search(r"(?:out of scope|excluded|not in v1|phase 2)\s*:\s*([^.]*)", raw.lower())
    if out_scope_match:
        scope["out_of_scope"] = [out_scope_match.group(1).strip()]
    return {
        "functional_reqs": functional_reqs,
        "nfrs": nfrs,
        "stakeholders": stakeholders,
        "decisions": decisions,
        "scope": scope,
    }


def _detect_nfr_category(text: str) -> str:
    """Detect NFR category with high-precision keyword lists."""
    t = text.lower()
    categories = {
        "Security": ["secure", "auth", "encrypt", "password", "ssl", "tls", "permission", "access control", "MFA", "compliance", "SOC2", "GDPR", "AES"],
        "Reliability": ["reliable", "uptime", "availab", "fault", "recovery", "failover", "SLA", "redundancy", "99.", "backup"],
        "Scalability": ["scale", "load", "throughput", "concurrent", "capacity", "volume", "TPS", "horizontal", "vertical", "10k", "100k"],
        "Usability": ["easy", "user-friendly", "accessible", "intuitive", "UX", "UI", "look and feel", "localization", "responsive", "design"],
        "Maintainability": ["maintain", "document", "code quality", "testable", "legacy", "refactor", "comment", "modular"],
        "Performance": ["fast", "speed", "latency", "response", "ms", "seconds", "millisecond", "P99", "P95", "throughput", "lag"]
    }
    for cat, kws in categories.items():
        if any(kw in t for kw in kws): return cat
    return "Performance"


def _detect_role(text: str) -> str:
    """Detect stakeholder role using domain-specific clusters."""
    t = text.lower()
    role_keywords = {
        "Product Management": ["product manager", "pm", "product owner", "po", "business analyst", "ba", "requirement lead"],
        "Engineering / Architecture": ["tech lead", "architect", "engineer", "developer", "engineering lead", "CTO", "DevOps"],
        "Compliance & Legal": ["security", "compliance", "legal", "privacy", "CISO", "audit"],
        "Operations": ["operations", "admin", "SRE", "support", "maintenance"],
        "Quality Assurance": ["tester", "qa", "quality", "test lead"],
        "Executive Leadership": ["director", "VP", "VP", "Head of", "sponsor", "executive", "CEO", "CFO"]
    }
    for role, kws in role_keywords.items():
        if any(kw in t for kw in kws): return role
    return "Business Stakeholder"


def _merge_extractions(llm_result: dict, classifier_result: dict) -> dict:
    """
    Merge LLM extraction with classifier-based extraction.
    LLM results take priority, but classifier catches items LLM might miss.
    """
    import hashlib
    
    def text_hash(text: str) -> str:
        normalized = text.lower().strip()[:50]
        return hashlib.md5(normalized.encode()).hexdigest()[:8]
    
    merged = {
        "functional_reqs": [],
        "nfrs": [],
        "stakeholders": [],
        "decisions": [],
        "scope": llm_result.get("scope", classifier_result.get("scope", {})),
    }
    
    # Merge functional requirements
    seen_fr = set()
    fr_counter = 1
    
    for req in llm_result.get("functional_reqs", []):
        h = text_hash(req.get("text", ""))
        if h not in seen_fr:
            seen_fr.add(h)
            req["id"] = f"FR-{fr_counter:03d}"
            req["extraction_source"] = "llm"
            merged["functional_reqs"].append(req)
            fr_counter += 1
    
    for req in classifier_result.get("functional_reqs", []):
        h = text_hash(req.get("text", ""))
        if h not in seen_fr:
            seen_fr.add(h)
            req["id"] = f"FR-{fr_counter:03d}"
            req["extraction_source"] = "classifier"
            merged["functional_reqs"].append(req)
            fr_counter += 1
    
    # Merge NFRs
    seen_nfr = set()
    nfr_counter = 1
    
    for req in llm_result.get("nfrs", []):
        h = text_hash(req.get("text", ""))
        if h not in seen_nfr:
            seen_nfr.add(h)
            req["id"] = f"NFR-{nfr_counter:03d}"
            req["extraction_source"] = "llm"
            merged["nfrs"].append(req)
            nfr_counter += 1
    
    for req in classifier_result.get("nfrs", []):
        h = text_hash(req.get("text", ""))
        if h not in seen_nfr:
            seen_nfr.add(h)
            req["id"] = f"NFR-{nfr_counter:03d}"
            req["extraction_source"] = "classifier"
            merged["nfrs"].append(req)
            nfr_counter += 1
    
    # Merge stakeholders (by name)
    seen_names = set()
    
    for sh in llm_result.get("stakeholders", []):
        name = sh.get("name", "").lower().strip()
        if name and name not in seen_names:
            seen_names.add(name)
            sh["extraction_source"] = "llm"
            merged["stakeholders"].append(sh)
    
    for sh in classifier_result.get("stakeholders", []):
        name = sh.get("name", "").lower().strip()
        if name and name not in seen_names:
            seen_names.add(name)
            sh["extraction_source"] = "classifier"
            merged["stakeholders"].append(sh)
    
    # Merge decisions
    seen_dec = set()
    dec_counter = 1
    
    for dec in llm_result.get("decisions", []):
        h = text_hash(dec.get("text", ""))
        if h not in seen_dec:
            seen_dec.add(h)
            dec["id"] = f"DEC-{dec_counter:03d}"
            dec["extraction_source"] = "llm"
            merged["decisions"].append(dec)
            dec_counter += 1
    
    for dec in classifier_result.get("decisions", []):
        h = text_hash(dec.get("text", ""))
        if h not in seen_dec:
            seen_dec.add(h)
            dec["id"] = f"DEC-{dec_counter:03d}"
            dec["extraction_source"] = "classifier"
            merged["decisions"].append(dec)
            dec_counter += 1
    
    return merged


def _build_source_map(extracted: dict, raw: str) -> dict:
    """Map requirement IDs to their character positions in raw_input."""
    source_map = {}

    for req in extracted.get("functional_reqs", []):
        span = req.get("source_span", req.get("text", ""))
        start = raw.find(span[:40]) if span else -1
        if start >= 0:
            source_map[req["id"]] = {
                "start": start,
                "end": start + len(span),
                "text": span,
            }

    for req in extracted.get("nfrs", []):
        text = req.get("text", "")
        start = raw.find(text[:40])
        if start >= 0:
            source_map[req["id"]] = {
                "start": start,
                "end": start + len(text),
                "text": text,
            }

    return source_map


def extractor_agent(state: BRDState) -> BRDState:
    """
    Extracts structured BRD fields using Gemini LLM with chain-of-thought prompting.
    Falls back to regex extraction if LLM unavailable or API key missing.
    
    HYBRID APPROACH:
    1. If LLM available: Use LLM to analyze FULL text (not just classified sentences)
    2. If LLM fails: Fall back to classifier-based extraction
    3. Merge results from both approaches for best coverage
    """
    start_time = time.time()

    try:
        llm = get_llm_safe()
        raw = state.get("raw_input", "")

        # First, get classifier-based extraction as baseline
        classifier_extracted = _regex_fallback_extract(state)
        
        if llm is not None:
            prompt = _build_extraction_prompt(state)

            try:
                from langchain_core.messages import HumanMessage
                print(f"[ExtractorAgent] Calling LLM...")
                response = llm.invoke([HumanMessage(content=prompt)])
                response_text = response.content.strip()

                # Strip markdown code fences if present
                response_text = re.sub(r"^```(?:json)?\n?", "", response_text)
                response_text = re.sub(r"\n?```$", "", response_text)
                response_text = response_text.strip()

                # Try to find JSON in the response
                if not response_text.startswith('{'):
                    # Try to extract JSON from response
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    if json_match:
                        response_text = json_match.group()

                llm_extracted = json.loads(response_text)
                print(f"[ExtractorAgent] LLM extraction successful")
                
                # Use LLM results as primary, merge with classifier for coverage
                extracted = _merge_extractions(llm_extracted, classifier_extracted)

            except json.JSONDecodeError as e:
                print(f"[ExtractorAgent] LLM returned invalid JSON: {e}")
                print(f"[ExtractorAgent] Response preview: {response_text[:200] if response_text else 'empty'}...")
                print(f"[ExtractorAgent] Using classifier-based fallback")
                extracted = classifier_extracted
            except Exception as e:
                print(f"[ExtractorAgent] LLM call failed: {e}")
                print(f"[ExtractorAgent] Using classifier-based fallback")
                extracted = classifier_extracted
        else:
            print("[ExtractorAgent] No API key — using classifier-based extraction")
            extracted = classifier_extracted

        # Apply extracted data to state
        state["functional_reqs"] = extracted.get("functional_reqs", [])
        state["nfrs"] = extracted.get("nfrs", [])
        state["stakeholders"] = extracted.get("stakeholders", [])
        state["decisions"] = extracted.get("decisions", [])
        state["scope"] = extracted.get("scope", {"in_scope": [], "out_of_scope": [], "assumptions": []})

        # Build source map for Source Trace tab
        state["source_map"] = _build_source_map(extracted, raw)

        # Analytics
        state.setdefault("analytics", {})
        # Ensure MoSCoW priority is assigned to ALL functional requirements
        for fr in state["functional_reqs"]:
            if not fr.get("moscow"):
                fr["moscow"] = assign_moscow_priority(fr.get("text", ""))
            
        state["analytics"]["label_counts"] = {
            "functional_reqs": len(state["functional_reqs"]),
            "nfrs": len(state["nfrs"]),
            "stakeholders": len(state["stakeholders"]),
            "decisions": len(state["decisions"]),
        }
        
        # Calculate MoSCoW distribution for analytics
        moscow_counts = {"Must": 0, "Should": 0, "Could": 0, "Wont": 0}
        for fr in state["functional_reqs"]:
            m = fr.get("moscow", "Should")
            if m in moscow_counts: moscow_counts[m] += 1
        state["analytics"]["moscow_distribution"] = moscow_counts

        state["processing_times"]["extractor"] = round(time.time() - start_time, 3)

    except Exception as e:
        state["error"] = f"Extractor agent error: {str(e)}"

    return state


if __name__ == "__main__":
    test_state = {
        "raw_input": (
            "The system must allow users to reset their passwords via email link. "
            "The API must respond in under 200ms at P99. "
            "We decided to use Stripe for all payment processing. "
            "Sarah will own the final sign-off on the dashboard. "
            "Q3 2024 is the target launch date."
        ),
        "source_type": "email",
        "classified_sentences": [
            {"text": "The system must allow users to reset their passwords via email link.", "label": "functional_req", "confidence": 0.95},
            {"text": "The API must respond in under 200ms at P99.", "label": "nfr", "confidence": 0.91},
            {"text": "We decided to use Stripe for all payment processing.", "label": "decision", "confidence": 0.88},
            {"text": "Sarah will own the final sign-off on the dashboard.", "label": "stakeholder", "confidence": 0.82},
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

    result = extractor_agent(test_state)
    if result.get("error"):
        print(f"ERROR: {result['error']}")
    else:
        print(f"FRs extracted      : {len(result['functional_reqs'])}")
        print(f"NFRs extracted     : {len(result['nfrs'])}")
        print(f"Stakeholders       : {len(result['stakeholders'])}")
        print(f"Decisions          : {len(result['decisions'])}")
        print(f"Processing time    : {result['processing_times'].get('extractor')}s")
        # Show reasoning for first FR
        if result['functional_reqs']:
            print(f"\nSample reasoning: {result['functional_reqs'][0].get('reasoning', 'N/A')}")
