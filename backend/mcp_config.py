"""
MCP Configuration
=================
Configures the LangChain Google GenAI client for use by the Extractor
and Critique agents. Loads API key from .env and returns a ready-to-use
ChatGoogleGenerativeAI instance.

Note: langchain-mcp-adapters 0.0.4 is used for MCP tool binding.
Temperature is fixed at 0 for deterministic BRD extraction output.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def get_llm() -> ChatGoogleGenerativeAI:
    """
    Returns a ChatGoogleGenerativeAI instance configured for BRD extraction.
    Temperature=0 ensures deterministic, reproducible output.
    Uses gemini-2.0-flash-exp which is fast and capable.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_key_here":
        raise ValueError(
            "GOOGLE_API_KEY not set in .env file. "
            "Please add your Google API key to the .env file."
        )

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0,
        max_tokens=4096,
    )


def get_llm_safe() -> ChatGoogleGenerativeAI | None:
    """
    Returns LLM or None if API key not configured.
    Used to gracefully degrade to demo mode.
    """
    try:
        return get_llm()
    except ValueError:
        return None


if __name__ == "__main__":
    llm = get_llm_safe()
    if llm:
        print("MCP OK — LLM connected")
    else:
        print("Warning: GOOGLE_API_KEY not set — running in demo mode")
