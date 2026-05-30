import os
import base64
import structlog
from typing import Optional
import httpx

from app.config import settings

logger = structlog.get_logger()

async def analyze_image_with_gemini(
    image_bytes: bytes,
    mime_type: str,
    prompt: str
) -> Optional[str]:
    """
    Sends base64-encoded image bytes and a prompt to the Google Gemini 2.5 Flash API.
    Uses httpx for high performance async HTTP calls.
    Returns the parsed text response from Gemini, or None if key is missing/failed.
    """
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key.lower() in ("placeholder", "none", "mock_key") or not api_key.strip():
        logger.info("gemini.vision.skipped", reason="No valid Gemini API key found in configuration.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key.strip()}"
    headers = {"Content-Type": "application/json"}
    
    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": b64_data
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        logger.info("gemini.vision.calling", url="generativelanguage.googleapis.com", mime_type=mime_type)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            
            if resp.status_code == 200:
                data = resp.json()
                text_response = data["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("gemini.vision.success")
                return text_response
            else:
                logger.warning("gemini.vision.http_error", status_code=resp.status_code, body=resp.text)
                return None
    except Exception as exc:
        logger.error("gemini.vision.failed", error=str(exc))
        return None
