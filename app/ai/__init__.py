"""AI provider selection: an OpenAI-compatible endpoint, Google's Gemini API, or demo answers."""

from app.ai.base import AIError, AIProvider, CookContext
from app.config import get_settings

__all__ = ["AIError", "AIProvider", "CookContext", "get_ai", "reset_ai"]

_provider: AIProvider | None = None


def get_ai() -> AIProvider:
    global _provider
    if _provider is None:
        settings = get_settings()
        if settings.use_mock_ai:
            from app.ai.mock import MockAI

            _provider = MockAI()
        elif settings.ai_base_url.strip():
            from app.ai.openai_compat import OpenAICompatAI

            _provider = OpenAICompatAI(
                settings.ai_base_url, settings.ai_api_key, settings.gemini_model, settings.ai_timeout_seconds,
                vision_model=settings.gemini_vision_model, vision_effort=settings.gemini_vision_thinking,
            )
        else:
            from app.ai.gemini import GeminiAI

            _provider = GeminiAI(
                settings.gemini_api_key, settings.gemini_model, settings.ai_timeout_seconds,
                vision_model=settings.gemini_vision_model, vision_thinking=settings.gemini_vision_thinking,
            )
    return _provider


def reset_ai() -> None:
    """Forget the cached provider (used when settings change, e.g. in tests)."""
    global _provider
    _provider = None
