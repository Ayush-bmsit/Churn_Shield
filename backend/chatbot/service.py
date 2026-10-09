"""LLM HTTP client. Provider is selected with LLM_PROVIDER / LLM_BASE_URL / LLM_API_KEY.

This is the only place that talks to an LLM vendor. Swap providers by changing env vars.
"""

import httpx

from backend.config import settings

PROVIDER_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "openai_compatible": "",
}


class LLMNotConfiguredError(RuntimeError):
    pass


def _base_url() -> str:
    if settings.llm_base_url.strip():
        return settings.llm_base_url.strip().rstrip("/")
    provider = settings.llm_provider.strip().lower()
    url = PROVIDER_BASE_URLS.get(provider, "")
    if provider == "openai_compatible" and not url:
        raise LLMNotConfiguredError("LLM_PROVIDER=openai_compatible requires LLM_BASE_URL")
    if not url:
        raise LLMNotConfiguredError(
            f"Unknown LLM_PROVIDER={settings.llm_provider}. Use openai, groq, or openai_compatible."
        )
    return url


def llm_configured() -> bool:
    return bool(settings.llm_api_key.strip())


def complete(system_prompt: str, user_prompt: str) -> str:
    if not llm_configured():
        raise LLMNotConfiguredError(
            "LLM_API_KEY is not set. The chatbot will not invent answers without a real LLM."
        )
    url = _base_url() + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.llm_model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
        response = client.post(url, headers=headers, json=body)
        if response.status_code >= 400:
            raise RuntimeError(f"LLM HTTP {response.status_code}: {response.text[:500]}")
        data = response.json()
    return data["choices"][0]["message"]["content"].strip()
