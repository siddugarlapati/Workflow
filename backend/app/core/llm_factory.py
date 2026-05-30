"""
Aegis — LLM Factory (Gemini + Local Fallback)
===============================================
Primary: Google Gemini 2.5 Flash
Fallback: Ollama local model (llama3.2:3b)

Uses LangChain's `.with_fallbacks()` to automatically retry with Ollama
when the Gemini API is unavailable, quota-exhausted (429), or misconfigured.
"""

from __future__ import annotations

import os
import urllib.request

import structlog
from langchain_core.language_models import BaseLanguageModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from app.config import settings

logger = structlog.get_logger()

GEMINI_MODEL = "gemini-2.5-flash"
LOCAL_MODEL = "llama3.2:3b"  # local fallback — change as needed
LOCAL_BASE_URL = "http://localhost:11434"


def _build_gemini(
    api_key: str,
    temperature: float = 0.1,
    json_mode: bool = False,
) -> ChatGoogleGenerativeAI:
    """Factory helper: instantiate Gemini 2.5 Flash."""
    kwargs: dict = {
        "model": GEMINI_MODEL,
        "google_api_key": api_key,
        "temperature": temperature,
        "max_output_tokens": 4096,
    }
    if json_mode:
        kwargs["model_kwargs"] = {"response_mime_type": "application/json"}
    return ChatGoogleGenerativeAI(**kwargs)


def _build_fallback(
    temperature: float = 0.1,
    json_mode: bool = False,
) -> ChatOllama:
    """Factory helper: instantiate local Ollama fallback."""
    kwargs: dict = {
        "model": LOCAL_MODEL,
        "base_url": LOCAL_BASE_URL,
        "temperature": temperature,
        "num_predict": 4096,
    }
    if json_mode:
        kwargs["format"] = "json"
    return ChatOllama(**kwargs)


class LLMFactory:
    """
    Provides chat models with **automatic fallback** via LangChain's
    `.with_fallbacks()`. Tries Google Gemini 2.5 Flash first; if the
    actual API call fails (quota, network, auth), silently retries
    with a local Ollama model (llama3.2:3b).

    All methods are idempotent and safe to call without a GEMINI_API_KEY.
    """

    # ── Private helpers ────────────────────────────────────────────────────────

    @classmethod
    def _get_api_key(cls) -> str | None:
        """Returns the Gemini API key or None if not configured."""
        key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
        if not key or key.lower() in ("placeholder", "none", "mock_key") or not key.strip():
            return None
        return key.strip()

    # ── Public factory methods ─────────────────────────────────────────────────

    @classmethod
    def get_chat_llm(cls, temperature: float = 0.1) -> BaseLanguageModel:
        """
        Returns a chat model. Uses Gemini primary with Ollama fallback.
        The `.with_fallbacks()` wrapper automatically retries on failure.
        """
        api_key = cls._get_api_key()
        fallback = _build_fallback(temperature=temperature)

        if api_key:
            logger.info("llm.initializing", provider="gemini", model=GEMINI_MODEL)
            primary = _build_gemini(api_key, temperature=temperature)
            return primary.with_fallbacks([fallback])

        logger.info("llm.no_gemini_key", fallback="ollama")
        return fallback

    @classmethod
    def get_json_llm(cls) -> BaseLanguageModel:
        """
        Returns a JSON-capable chat model. Uses Gemini primary with Ollama fallback.
        The `.with_fallbacks()` wrapper automatically retries on failure.
        """
        api_key = cls._get_api_key()
        fallback = _build_fallback(temperature=0.0, json_mode=True)

        if api_key:
            logger.info("llm.initializing_json", provider="gemini", model=GEMINI_MODEL)
            primary = _build_gemini(api_key, temperature=0.0, json_mode=True)
            return primary.with_fallbacks([fallback])

        logger.info("llm.no_gemini_key", fallback="ollama")
        return fallback

    @classmethod
    async def health_check(cls) -> dict:
        """Returns the LLM provider status."""
        api_key = cls._get_api_key()
        gemini_status = "ok" if api_key else "unconfigured"
        active_provider = "gemini" if api_key else "ollama"

        # Quick local model health ping (stdlib only — no hidden deps)
        ollama_ok = False
        try:
            req = urllib.request.Request(
                f"{LOCAL_BASE_URL}/api/tags",
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                ollama_ok = resp.status == 200
        except Exception:
            pass

        return {
            "status": "ok" if (api_key or ollama_ok) else "degraded",
            "provider": active_provider,
            "gemini": {
                "model": GEMINI_MODEL,
                "configured": bool(api_key),
                "status": gemini_status,
            },
            "ollama": {
                "model": LOCAL_MODEL,
                "base_url": LOCAL_BASE_URL,
                "reachable": ollama_ok,
            },
        }