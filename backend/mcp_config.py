"""
MCP Configuration
=================
Configures the LangChain Google GenAI client for use by the Extractor
and Critique agents. Loads API key from .env and returns a ready-to-use
ChatGoogleGenerativeAI instance.

Temperature is fixed at 0 for deterministic BRD extraction output.
"""

import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def get_llm(model_id: str = "gemini-flash-latest") -> ChatGoogleGenerativeAI:
    """
    Returns a ChatGoogleGenerativeAI instance.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_key_here":
        raise ValueError("GOOGLE_API_KEY not set")

    return ChatGoogleGenerativeAI(
        model=model_id,
        google_api_key=api_key,
        temperature=0,
        max_tokens=4096,
    )


def get_llm_safe() -> ChatGoogleGenerativeAI | None:
    """
    Returns the first available LLM model object.
    Does NOT probe — probing wastes quota. Errors are caught at call time.
    """
    # Models confirmed available for this API key (from ListModels)
    models_to_try = [
        "gemini-flash-latest",
        "gemini-pro-latest",
    ]

    for model in models_to_try:
        try:
            llm = get_llm(model)
            print(f"[mcp_config] Using model: {model}")
            return llm
        except ValueError as e:
            print(f"[mcp_config] API key error: {e}")
            return None
        except Exception as e:
            print(f"[mcp_config] Could not init '{model}': {str(e)[:80]}")
            continue

    print("[mcp_config] WARNING: No model could be initialized.")
    return None


if __name__ == "__main__":
    llm = get_llm_safe()
    if llm:
        print("MCP OK — LLM connected")
    else:
        print("Warning: No working model found — check API key and quota")
