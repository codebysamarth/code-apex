"""
ML Classifier Agent
===================
Loads your trained TF-IDF + Logistic Regression model (classifier.pkl)
and classifies each sentence in the input into one of 6 labels:
  functional_req | nfr | decision | timeline | stakeholder | noise

Model is loaded at MODULE LEVEL so it loads once at startup, not per request.
Sentence splitting uses NLTK for accurate boundary detection.
"""

import os
import re
import json
import time
import joblib
import nltk
from state import BRDState
from dotenv import load_dotenv

load_dotenv()

# NLTK downloads moved to main.py

# ---------------------------------------------------------------------------
# Module-level model loading — runs ONCE at startup
# ---------------------------------------------------------------------------
MODEL_PATH = os.getenv("MODEL_PATH", "./models")

try:
    _pipeline = joblib.load(f"{MODEL_PATH}/classifier.pkl")
    with open(f"{MODEL_PATH}/label_classes.json", "r") as f:
        _label_classes = json.load(f)
    print(f"[ClassifierAgent] SUCCESS: Model and labels loaded from {MODEL_PATH}")
except Exception as e:
    _pipeline = None
    _label_classes = []
    print(f"[ClassifierAgent] ERROR: Failed to load model from {MODEL_PATH}")
    print(f"[ClassifierAgent] Exception: {type(e).__name__}: {str(e)}")
    print(f"[ClassifierAgent] Current working directory: {os.getcwd()}")


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------
def normalize_text(text: str) -> str:
    """
    Normalise a sentence before feeding it to the classifier.
    - Replace 4-digit years with YEAR token (avoids Enron 2001/2000 date bias)
    - Replace email addresses with EMAIL token
    - Replace URLs with URL token
    """
    text = re.sub(r"\b(19|20)\d{2}\b", "YEAR", text)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "EMAIL", text)
    text = re.sub(r"https?://\S+", "URL", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------
def _llm_classify(sentences: list[str], domain: str) -> list[dict]:
    """Uses LLM to classify sentences into BRD categories for non-software domains."""
    from mcp_config import get_llm_safe
    from langchain_core.messages import HumanMessage
    
    llm = get_llm_safe()
    if not llm:
        return []

    prompt = f"""You are a {domain} Requirement Expert. Classify each sentence into exactly one of these labels:
Labels: [functional_req, nfr, decision, timeline, stakeholder, noise]

Sentences:
{chr(10).join(f"{i+1}. {s}" for i, s in enumerate(sentences))}

Return ONLY a JSON array of objects: [{{"text": "...", "label": "...", "confidence": 0.9}}]
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw_content = response.content
        if isinstance(raw_content, list):
            content = "".join([c["text"] if isinstance(c, dict) and "text" in c else str(c) for c in raw_content])
        else:
            content = str(raw_content)
        content = content.strip()
        # Clean response
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
        
        # Extract JSON if surrounded by text
        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
            
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"[ClassifierAgent] LLM classification failed: {e}")
        # Return fallback noise classification to keep pipeline moving without crash
        return [{"text": s, "label": "noise", "confidence": 0.0} for s in sentences]

def classify_agent(state: BRDState) -> BRDState:
    """
    Classifies sentences in raw_input.
    Software domain -> Logistic Regression ML Model
    Other domains   -> Zero-Shot LLM Classifier (Industry-aware)
    """
    start_time = time.time()
    domain = state.get("domain", "software")
    raw = state.get("raw_input", "")
    
    if not raw:
        state["classified_sentences"] = []
        return state

    try:
        sentences = nltk.sent_tokenize(raw)
        classified = []

        # BRANCH 1: Software domain uses the trained ML pipeline
        if domain == "software" and _pipeline is not None:
            for sent in sentences:
                word_count = len(sent.split())
                if word_count < 3:
                    classified.append({"text": sent, "label": "noise", "confidence": 1.0})
                    continue
                
                label = _pipeline.predict([sent])[0]
                probs = _pipeline.predict_proba([sent])[0]
                confidence = round(float(max(probs)), 2)
                classified.append({"text": sent, "label": label, "confidence": confidence})
        
        # BRANCH 2: All other domains use the industry-aware Zero-Shot LLM Classifier
        else:
            # Process in batches of 15 to manage LLM context
            for i in range(0, len(sentences), 15):
                batch = sentences[i : i+15]
                batch_classified = _llm_classify(batch, domain)
                classified.extend(batch_classified)

        # Apply industry-specific post-processing if available
        from post_processing_rules import apply_post_processing_rules 
        for item in classified:
            label, confidence, _ = apply_post_processing_rules(item["text"], item["label"], item["confidence"], domain)
            item["label"] = label
            item["confidence"] = confidence

        state["classified_sentences"] = classified
        state["processing_times"]["classifier"] = round(time.time() - start_time, 3)

        # Build analytics for confidence distribution
        conf_buckets = {"high": 0, "medium": 0, "low": 0, "very_low": 0}
        for item in classified:
            c = item["confidence"]
            if c >= 0.90:
                conf_buckets["high"] += 1
            elif c >= 0.70:
                conf_buckets["medium"] += 1
            elif c >= 0.50:
                conf_buckets["low"] += 1
            else:
                conf_buckets["very_low"] += 1

        state.setdefault("analytics", {})
        state["analytics"]["confidence_distribution"] = conf_buckets
        state["analytics"]["total_sentences_classified"] = len(classified)

    except Exception as e:
        state["error"] = f"Classifier agent error: {str(e)}"
        print(f"[classifier_agent] Error: {str(e)}")

    return state


if __name__ == "__main__":
    # Quick smoke test
    test_sentences = [
        "The system must allow users to log in with SSO.",
        "The API response time must be under 200ms at the 99th percentile.",
        "We decided to use Stripe for all payment processing.",
        "The Q3 2024 deadline is set for the go-live of the dashboard.",
        "Sarah will own the sign-off process and manage the stakeholder review.",
    ]

    state = {
        "raw_input": " ".join(test_sentences),
        "source_type": "email",
        "classified_sentences": [],
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

    result = classify_agent(state)

    if result.get("error"):
        print(f"ERROR: {result['error']}")
    else:
        print(f"Classified {len(result['classified_sentences'])} sentences:\n")
        for item in result["classified_sentences"]:
            print(f"  [{item['label']:20s}] ({item['confidence']:.2f}) {item['text'][:70]}")
        print(f"\nProcessing time: {result['processing_times'].get('classifier')}s")
