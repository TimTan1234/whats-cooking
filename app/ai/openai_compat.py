"""Any OpenAI-compatible chat completions endpoint (for example the Coarena Model API)."""

import asyncio
import base64
import logging
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.ai import prompts
from app.ai.base import AIError, CookContext
from app.schemas import CookQuestion, Detection, DishIdea, FullRecipe, IdeaList, QuestionList, json_schema

log = logging.getLogger("whatscooking.ai")

T = TypeVar("T", bound=BaseModel)

_RETRY_CODES = {429, 500, 502, 503, 504}
_CONFIG_CODES = {400, 401, 402, 403, 404, 422}
_ATTEMPTS = 3


def strict_schema(node: Any) -> Any:
    """The JSON schema with "additionalProperties": false on every object, as strict mode requires."""
    if isinstance(node, dict):
        node = {key: strict_schema(value) for key, value in node.items()}
        if node.get("type") == "object":
            node["additionalProperties"] = False
        return node
    if isinstance(node, list):
        return [strict_schema(item) for item in node]
    return node


class OpenAICompatAI:
    is_mock = False

    def __init__(self, base_url: str, api_key: str, model: str, timeout_seconds: int = 60,
                 vision_model: str = "", vision_effort: str = "") -> None:
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._model = model
        self._vision_model = vision_model.strip() or model
        self._vision_effort = vision_effort.strip().lower()
        self._timeout = timeout_seconds

    async def _ask(self, answer: type[T], content: list[dict], lang: str, model: str = "", effort: str = "") -> T:
        body: dict[str, Any] = {
            "model": model or self._model,
            "messages": [
                {"role": "system", "content": prompts.system_prompt(lang)},
                {"role": "user", "content": content},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": answer.__name__, "strict": True, "schema": strict_schema(json_schema(answer))},
            },
        }
        if effort:
            body["reasoning_effort"] = effort

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(1, _ATTEMPTS + 1):
                last = attempt == _ATTEMPTS
                try:
                    response = await client.post(self._url, headers=self._headers, json=body)
                except httpx.TimeoutException as exc:
                    log.warning("AI request timed out after %ss", self._timeout)
                    raise AIError("busy", "timed out") from exc
                except httpx.HTTPError as exc:
                    log.warning("AI request failed (attempt %s): %s", attempt, exc)
                    if not last:
                        await asyncio.sleep(2 * attempt)
                        continue
                    raise AIError("busy", str(exc)) from exc

                code = response.status_code
                if code != 200:
                    log.warning("AI API error %s (attempt %s): %s", code, attempt, response.text[:300])
                    if code in _RETRY_CODES and not last:
                        await asyncio.sleep(2 * attempt)
                        continue
                    if code in _RETRY_CODES:
                        raise AIError("busy", str(code))
                    if code in _CONFIG_CODES:
                        raise AIError("config", response.text[:200])
                    raise AIError("failed", str(code))

                try:
                    message = response.json()["choices"][0]["message"]
                except (ValueError, KeyError, IndexError, TypeError) as exc:
                    raise AIError("failed", "unreadable response") from exc
                text = message.get("content")
                if not text or message.get("refusal"):
                    raise AIError("blocked")
                try:
                    return answer.model_validate_json(text)
                except ValidationError as exc:
                    log.warning("AI answer did not match the schema (attempt %s): %s", attempt, exc)
                    if last:
                        raise AIError("failed", "unexpected answer") from exc
        raise AIError("failed")  # pragma: no cover - loop always returns or raises

    async def detect_ingredients(self, image: bytes, lang: str) -> Detection:
        url = "data:image/jpeg;base64," + base64.b64encode(image).decode("ascii")
        content = [
            {"type": "text", "text": prompts.detect_prompt()},
            {"type": "image_url", "image_url": {"url": url, "detail": "high"}},
        ]
        return await self._ask(Detection, content, lang, model=self._vision_model, effort=self._vision_effort)

    async def ask_questions(self, ctx: CookContext) -> list[CookQuestion]:
        answer = await self._ask(QuestionList, [{"type": "text", "text": prompts.questions_prompt(ctx)}], ctx.lang)
        return answer.questions

    async def suggest_dishes(self, ctx: CookContext, count: int = 5) -> list[DishIdea]:
        answer = await self._ask(IdeaList, [{"type": "text", "text": prompts.suggest_prompt(ctx, count)}], ctx.lang)
        return answer.ideas

    async def write_recipe(self, ctx: CookContext, idea: DishIdea) -> FullRecipe:
        return await self._ask(FullRecipe, [{"type": "text", "text": prompts.recipe_prompt(ctx, idea)}], ctx.lang)
