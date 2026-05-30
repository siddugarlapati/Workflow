"""
WorkFlow — LLM Factory
Provides a pluggable LLM abstraction so the AI service can swap
providers without changing business logic.
Supports: Google Gemini (Primary when API key is present) & Ollama (Fallback)
"""
import os
import structlog
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings

logger = structlog.get_logger()


class LLMFactory:
    """
    Returns a configured LangChain chat model.
    Funnels model requests to Google Gemini 1.5 Flash if GEMINI_API_KEY is defined,
    falling back gracefully to local Ollama if missing/mocked.
    """

    _chat_model = None

    @classmethod
    def _get_api_key(cls) -> str | None:
        key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
        if not key or key.lower() in ("placeholder", "none", "mock_key") or not key.strip():
            return None
        return key.strip()

    @classmethod
    def get_chat_llm(cls, temperature: float = 0.1):
        """
        Returns a configured chat model.
        Uses ChatGoogleGenerativeAI if a Gemini API key is configured,
        otherwise falls back to ChatOllama.
        """
        api_key = cls._get_api_key()
        if api_key:
            logger.info("llm.initializing", provider="gemini", model="gemini-2.5-flash")
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=api_key,
                temperature=temperature,
                max_output_tokens=4096,
            )
        else:
            logger.info(
                "llm.initializing",
                provider="ollama",
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
            )
            return ChatOllama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=temperature,
                num_predict=600,
                format="",
            )

    @classmethod
    def get_json_llm(cls):
        """
        Returns a chat model configured to output JSON.
        Uses ChatGoogleGenerativeAI with response_mime_type="application/json" if a Gemini API key is configured,
        otherwise falls back to ChatOllama with format="json".
        """
        api_key = cls._get_api_key()
        if api_key:
            logger.info("llm.initializing_json", provider="gemini", model="gemini-2.5-flash")
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=api_key,
                temperature=0.0,
                max_output_tokens=4096,
                model_kwargs={"response_mime_type": "application/json"}
            )
        else:
            return ChatOllama(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=0.0,
                num_predict=300,
                format="json",
            )

    @classmethod
    async def health_check(cls) -> dict:
        """Check the status of configured LLM providers."""
        api_key = cls._get_api_key()
        if api_key:
            return {
                "status": "ok",
                "provider": "gemini",
                "configured_model": "gemini-2.5-flash",
            }
        
        # Local Ollama fallback health check
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.ollama_base_url}/api/tags")
                models = resp.json().get("models", [])
                available = [m["name"] for m in models]
                model_ready = any(
                    settings.ollama_model in m for m in available
                )
                return {
                    "status": "ok" if model_ready else "model_not_found",
                    "available_models": available,
                    "configured_model": settings.ollama_model,
                }
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
