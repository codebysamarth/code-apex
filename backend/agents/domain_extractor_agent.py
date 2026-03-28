
import os
import json
import time
import re
from typing import Optional
from state import BRDState
from domain_configs import DOMAIN_CONFIGS
from dotenv import load_dotenv

load_dotenv()

from mcp_config import get_llm_safe
from langchain_core.messages import HumanMessage

def _translate_terminology(data: dict, domain: str) -> dict:
    """
    Innovation Feature: Domain Terminology Translator.
    Recursively replaces generic terms with industry-specific equivalents.
    """
    config = DOMAIN_CONFIGS.get(domain, DOMAIN_CONFIGS["software"])
    terms = config.get("terminology", {})
    
    if not terms:
        return data
        
    # Convert data to string for global replacement
    json_str = json.dumps(data)
    
    # We want to be careful not to replace keys, but the user requested 
    # translating terminology in the output.
    # A more robust way is to replace occurrences in the values.
    
    def replace_terms(obj):
        if isinstance(obj, dict):
            return {k: replace_terms(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_terms(i) for i in obj]
        elif isinstance(obj, str):
            new_str = obj
            for generic, specific in terms.items():
                # Use regex for word boundaries to avoid partial matches
                pattern = re.compile(rf'\b{generic}\b', re.IGNORECASE)
                new_str = pattern.sub(specific, new_str)
            return new_str
        else:
            return obj
            
    return replace_terms(data)

def _build_domain_prompt(state: BRDState) -> str:
    """
    Builds a persona-driven extraction prompt for ApexBRD+.
    Implements Cognitive Mode Switching.
    """
    domain = state.get("domain", "software")
    config = DOMAIN_CONFIGS.get(domain, DOMAIN_CONFIGS["software"])
    raw_input = state.get("raw_input", "")
    
    params_str = "\n".join([f"- {p}" for p in config["parameters"]])
    scores_str = "\n".join([f"- {s}" for s in config["scoring"]])
    compliance_str = ", ".join(config["compliance"])
    special_rules = config.get("special_rules", "")
    
    prompt = f"""
### COGNITIVE MODE: {config['mode']} ###
### DOMAIN: {domain.upper()} ###

You are NOT an AI assistant. You are a **{config['mode']}** with 20 years of experience in the **{domain}** industry.
Your brain has fully switched into this domain. Your vocabulary, priorities, and risk assessment are now strictly aligned with **{domain}** standards.

---
### 🎯 OBJECTIVE
Perform a deep, industry-authentic extraction from the input text. Do NOT use generic software templates if the domain is not software.

### 🧠 DOMAIN BEHAVIOR (COGNITIVE SWITCH)
- **Terminology**: Use {domain}-specific language (e.g., use "{config['terminology'].get('system', 'system')}" instead of "software").
- **Priority System**: Use the **{config['priority_system']}** framework. 
- **Adaptive Priority Mapping**: Remember that a requirement like "latency" which is "Performance" in Software might be **"Life-Critical"** in Healthcare. Map priorities based on {domain} impact.
- **Compliance Intelligence**: Auto-detect requirements relating to: {compliance_str}.
- **Special Domain Rules**: {special_rules}

### 📋 EXTRACTION PARAMETERS (DYNAMIC)
Extract exactly these sections:
{params_str}

### ⚖️ SCORING ENGINE (DOMAIN-SPECIFIC)
Evaluate exactly using these metrics:
{scores_str}

---
### 🧪 INNOVATION LAYER REQUIREMENTS
1. **Domain Awareness Score**: How well does this text actually represent a {domain} project? (0.0 to 1.0)
2. **Cross-Domain Conflict Detection**: Identify if there are terms or requirements from other domains (e.g., software terms in a mechanical doc) and flag as "Mixed-domain ambiguity".
3. **Missing Critical Parameters Detector**: Identify what is MISSING that a {config['mode']} would expect to see (e.g. no patient safety in Healthcare, no tolerances in Mechanical).

---
### 📥 INPUT TEXT
\"\"\"
{raw_input}
\"\"\"

---
### 📤 OUTPUT SPECIFICATION
Return ONLY a valid JSON object.
{{
  "document_title": "Industry-authentic title",
  "domain": "{domain}",
  "cognitive_mode": "{config['mode']}",
  "priority_framework": "{config['priority_system']}",
  "sections": {{
    "Section Name (from parameters)": [
       {{
         "title": "Title",
         "description": "Description using {domain} terminology",
         "priority": "Value from {config['priority_system']}",
         "mitigation": "Industrial risk mitigation if applicable"
       }}
    ]
  }},
  "domain_scores": {{
    "Score Name": {{ "value": 0.0-1.0, "rationale": "Why this score?" }}
  }},
  "compliance_check": {{
    "standard": "Relevant standard",
    "status": "met|partial|missing",
    "findings": "Architectural observation"
  }},
  "innovation_metrics": {{
    "domain_awareness_score": 0.0-1.0,
    "conflict_detection": "Description of ambiguity or 'None'",
    "missing_critical_params": ["What is missing?"]
  }},
  "standard_mapping": {{
    "functional_reqs": [
       {{ "text": "Requirement", "priority": 1, "moscow": "Must|Should|Could|Wont" }}
    ],
    "nfrs": [
       {{ "text": "Requirement", "category": "Category", "priority": 1 }}
    ],
    "stakeholders": [
       {{ "name": "Name", "role": "Role", "influence_score": 0.8 }}
    ],
    "decisions": [
       {{ "text": "Decision", "rationale": "Why" }}
    ]
  }}
}}
"""
    return prompt

def domain_extractor_agent(state: BRDState) -> BRDState:
    """
    ApexBRD+ Domain Extractor.
    Dynamically adapts extraction logic, parameters, and terminology.
    """
    start_time = time.time()
    domain = state.get("domain", "software")
    
    if domain == "software":
        from agents.extractor_agent import extractor_agent
        return extractor_agent(state)
        
    try:
        llm = get_llm_safe()
        if llm is None:
            state["error"] = "API Key missing/invalid. Domain switching (ApexBRD+) requires an active LLM."
            return state
            
        if domain not in DOMAIN_CONFIGS:
            state["error"] = f"Configuration for domain '{domain}' not found in DOMAIN_CONFIGS."
            return state
            
        config = DOMAIN_CONFIGS[domain]
        prompt = _build_domain_prompt(state)
        print(f"[ApexBRD+] Mode: {domain.upper()} Persona: {config.get('mode', 'Expert')}")
        
        # Retry LLM call with backoff for free-tier rate limiting (429)
        response = None
        last_error = None
        for attempt in range(3):
            try:
                response = llm.invoke([HumanMessage(content=prompt)])
                break
            except Exception as e:
                last_error = str(e)
                if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error or "Quota" in last_error:
                    wait = 15 * (attempt + 1)
                    print(f"[ApexBRD+] Rate limited, retrying in {wait}s (attempt {attempt+1}/3)...")
                    time.sleep(wait)
                    # Try a cheaper model on retry
                    from mcp_config import get_llm
                    try:
                        fallback_models = ["gemini-flash-latest", "gemini-pro-latest"]
                        for fb_model in fallback_models:
                            try:
                                llm = get_llm(fb_model)
                                break
                            except Exception:
                                continue
                    except Exception:
                        pass
                else:
                    break  # Non-retriable error

        if response is None:
            state["error"] = f"ApexBRD+ Domain Switch Error: {last_error}"
            return state

        raw_content = response.content
        if isinstance(raw_content, list):
            content = "".join([c["text"] if isinstance(c, dict) and "text" in c else str(c) for c in raw_content])
        else:
            content = str(raw_content)
        content = content.strip()
        
        # Parse JSON from content
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
        
        # Robust JSON extraction
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
            
        data = json.loads(content)
        
        # Innovation: Terminology Translation
        data = _translate_terminology(data, domain)
        
        # Populate state
        state["domain_data"] = data
        
        # MAP TO STANDARD STATE for cross-domain compatibility
        if "standard_mapping" in data:
            mapping = data["standard_mapping"]
            
            # Populate functional_reqs
            if "functional_reqs" in mapping:
                for i, fr in enumerate(mapping["functional_reqs"]):
                    state["functional_reqs"].append({
                        "id": f"FR-{i+1:03d}",
                        "text": fr.get("text", ""),
                        "priority": fr.get("priority", 1),
                        "moscow": fr.get("moscow", "Should"),
                        "confidence": 0.9,
                        "source_span": fr.get("text", "")[:50]
                    })
            
            # Populate nfrs
            if "nfrs" in mapping:
                for i, nfr in enumerate(mapping["nfrs"]):
                    state["nfrs"].append({
                        "id": f"NFR-{i+1:03d}",
                        "text": nfr.get("text", ""),
                        "category": nfr.get("category", "Performance"),
                        "priority": nfr.get("priority", 1),
                        "confidence": 0.9
                    })
            
            # Populate stakeholders
            if "stakeholders" in mapping:
                for sh in mapping["stakeholders"]:
                    state["stakeholders"].append({
                        "name": sh.get("name", "Unknown"),
                        "role": sh.get("role", "Stakeholder"),
                        "influence_score": sh.get("influence_score", 0.7),
                        "mentioned_count": 1
                    })
            
            # Populate decisions
            if "decisions" in mapping:
                for i, d in enumerate(mapping["decisions"]):
                    state["decisions"].append({
                        "id": f"DEC-{i+1:03d}",
                        "text": d.get("text", ""),
                        "rationale": d.get("rationale", ""),
                        "date_mentioned": ""
                    })

        state["processing_times"]["domain_extractor"] = round(time.time() - start_time, 3)
        
    except Exception as e:
        state["error"] = f"ApexBRD+ Domain Switch Error: {str(e)}"
        
    return state
