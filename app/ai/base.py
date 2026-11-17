"""What the rest of the app needs from an AI provider."""

from dataclasses import dataclass, field
from typing import Protocol

from app.schemas import CookQuestion, Detection, DishIdea, FullRecipe


class AIError(Exception):
    """An AI request failed in a way the user should be told about.

    kind is one of:
      busy     - rate limited, overloaded or timed out; trying again may work
      config   - the API key or model name is wrong
      blocked  - the provider returned no answer (for example a safety block)
      failed   - anything else
    """

    def __init__(self, kind: str, detail: str = "") -> None:
        super().__init__(f"{kind}: {detail}" if detail else kind)
        self.kind = kind
        self.detail = detail


@dataclass
class CookContext:
    """Everything the AI is told when suggesting dishes or writing a recipe."""

    ingredients: list[str]
    lang: str = "en"
    diets: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    dislikes: str = ""
    favourite_cuisines: list[str] = field(default_factory=list)
    skill: str = "home"
    minutes: int = 0  # 0 means no limit
    cuisine: str = ""  # "" means any
    meal: str = ""  # "" means any
    servings: int = 2
    extras_ok: bool = True
    recent_titles: list[str] = field(default_factory=list)
    liked_titles: list[str] = field(default_factory=list)
    disliked_titles: list[str] = field(default_factory=list)
    dish_type: str = ""  # "" means any
    craving: str = ""  # what they feel like today, in their own words
    answers: list[str] = field(default_factory=list)  # "question → answer" from the questions step
    likes: str = ""  # foods they love, typed on the profile
    usual_dish_types: list[str] = field(default_factory=list)
    recent_cravings: list[str] = field(default_factory=list)
    recent_answers: list[str] = field(default_factory=list)
    today: bool = False  # suggest from taste alone, not from the kitchen


class AIProvider(Protocol):
    is_mock: bool

    async def detect_ingredients(self, image: bytes, lang: str) -> Detection: ...

    async def ask_questions(self, ctx: CookContext) -> list[CookQuestion]: ...

    async def suggest_dishes(self, ctx: CookContext, count: int = 5) -> list[DishIdea]: ...

    async def write_recipe(self, ctx: CookContext, idea: DishIdea) -> FullRecipe: ...
