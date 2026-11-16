"""Google Gemini provider (google-genai SDK)."""

import asyncio
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.ai import prompts
from app.ai.base import AIError, CookContext
from app.schemas import Detection, DishIdea, FullRecipe, IdeaList, json_schema

log = logging.getLogger("whatscooking.ai")

T = TypeVar("T", bound=BaseModel)

_RETRY_CODES = {429, 500, 502, 503, 504}
_CONFIG_CODES = {400, 401, 403, 404}
_ATTEMPTS = 3


class GeminiAI:
    is_mock = False

    def __init__(self, api_key: str, model: str, timeout_seconds: int = 60,
                 vision_model: str = "", vision_thinking: str = "") -> None:
        from google import genai
        from google.genai import errors, types

        self._types = types
        self._errors = errors
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._vision_model = vision_model.strip() or model
        self._vision_thinking = vision_thinking.strip().lower()
        self._timeout = timeout_seconds

    async def _ask(self, answer: type[T], contents: list, lang: str, model: str = "", thinking: str = "") -> T:
        model = model or self._model
        options = {}
        if thinking:
            options["thinking_config"] = self._types.ThinkingConfig(thinking_level=thinking)
        config = self._types.GenerateContentConfig(
            system_instruction=prompts.system_prompt(lang),
            response_mime_type="application/json",
            response_json_schema=json_schema(answer),
            **options,
        )
        for attempt in range(1, _ATTEMPTS + 1):
            last = attempt == _ATTEMPTS
            try:
                response = await asyncio.wait_for(
                    self._client.aio.models.generate_content(model=model, contents=contents, config=config),
                    timeout=self._timeout,
                )
            except asyncio.TimeoutError as exc:
                log.warning("Gemini request timed out after %ss", self._timeout)
                raise AIError("busy", "timed out") from exc
            except self._errors.APIError as exc:
                code = getattr(exc, "code", None)
                log.warning("Gemini API error %s (attempt %s): %s", code, attempt, getattr(exc, "message", exc))
                if code in _RETRY_CODES and not last:
                    await asyncio.sleep(2 * attempt)
                    continue
                if code in _RETRY_CODES:
                    raise AIError("busy", str(code)) from exc
                if code in _CONFIG_CODES:
                    raise AIError("config", str(getattr(exc, "message", "") or code)) from exc
                raise AIError("failed", str(code)) from exc

            text = getattr(response, "text", None)
            if not text:
                raise AIError("blocked")
            try:
                return answer.model_validate_json(text)
            except ValidationError as exc:
                log.warning("Gemini answer did not match the schema (attempt %s): %s", attempt, exc)
                if last:
                    raise AIError("failed", "unexpected answer") from exc
        raise AIError("failed")  # pragma: no cover - loop always returns or raises

    async def detect_ingredients(self, image: bytes, lang: str) -> Detection:
        contents = [prompts.detect_prompt(), self._types.Part.from_bytes(data=image, mime_type="image/jpeg")]
        return await self._ask(Detection, contents, lang, model=self._vision_model, thinking=self._vision_thinking)

    async def suggest_dishes(self, ctx: CookContext, count: int = 5) -> list[DishIdea]:
        answer = await self._ask(IdeaList, [prompts.suggest_prompt(ctx, count)], ctx.lang)
        return answer.ideas

    async def write_recipe(self, ctx: CookContext, idea: DishIdea) -> FullRecipe:
        return await self._ask(FullRecipe, [prompts.recipe_prompt(ctx, idea)], ctx.lang)
