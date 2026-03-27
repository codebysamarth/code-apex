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

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

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
def classify_agent(state: BRDState) -> BRDState:
    """
    Classifies sentences in raw_input using the trained ML model.

    Pipeline:
    1. Tokenise raw_input into sentences using NLTK
    2. Filter by word count (8–120 words)
    3. Normalise each sentence
    - Predict label + confidence
    4. Apply post-processing rules (overrides)
    5. Apply noise filtering logic
    6. Store results in state["classified_sentences"]

    Noise filtering:
    - noise + confidence < 0.50 → DISCARD (clear noise)
    - noise + confidence >= 0.50 → KEEP (might be missed req)
    - all non-noise labels → always KEEP
    """
    start_time = time.time()
    
    # Import post-processing rules (integration of user-added file)
    try:
        from post_processing_rules import apply_post_processing_rules
    except ImportError:
        apply_post_processing_rules = None
        print("[ClassifierAgent] WARNING: post_processing_rules.py not found — using raw ML output.")

    try:
        if _pipeline is None:
            state["error"] = (
                "Classifier model not loaded. "
                f"Ensure classifier.pkl exists at {MODEL_PATH}/"
            )
            return state

        raw = state.get("raw_input", "")
        if not raw:
            state["classified_sentences"] = []
            return state

        sentences = nltk.sent_tokenize(raw)

        classified = []
        for sent in sentences:
            # Word count filter - reduced minimum to catch short requirements
            word_count = len(sent.split())
            if word_count < 4 or word_count > 150:
                continue

            normalized = normalize_text(sent)
            label = _pipeline.predict([normalized])[0]
            proba = _pipeline.predict_proba([normalized])[0]
            confidence = float(max(proba))
            
            # Application of post-processing overrides for high accuracy integration
            if apply_post_processing_rules:
                label, confidence, is_overridden = apply_post_processing_rules(sent, label, confidence)
                if is_overridden:
                    print(f"[ClassifierAgent] Rule Override: '{label}' ({confidence}) for '{sent[:30]}...'")

            # More lenient noise filtering - keep borderline cases for LLM review
            if label == "noise" and confidence > 0.85:
                continue  # Only discard very confident noise

            classified.append({
                "text": sent,
                "label": label,
                "confidence": round(confidence, 4),
                "normalized_text": normalized,
            })

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
