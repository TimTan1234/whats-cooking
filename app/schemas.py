"""Shapes of the answers we ask the AI for.

Every field is required and there are no defaults, so the JSON schema sent to
Gemini stays inside the subset it enforces.
"""

from typing import Any, Literal

from pydantic import BaseModel

Category = Literal["produce", "protein", "dairy_egg", "grain", "sauce_spice", "other"]
Confidence = Literal["high", "medium", "low"]
Difficulty = Literal["easy", "medium", "hard"]

CATEGORIES: tuple[str, ...] = ("produce", "protein", "dairy_egg", "grain", "sauce_spice", "other")


class DetectedIngredient(BaseModel):
    name: str
    quantity: str
    category: Category
    confidence: Confidence
    evidence: str  # what the AI saw that identifies it
    box_2d: list[int]  # [ymin, xmin, ymax, xmax] on a 0-1000 scale


class Detection(BaseModel):
    """The ingredients found in one photo."""

    ingredients: list[DetectedIngredient]


class DishIdea(BaseModel):
    title: str
    blurb: str
    minutes: int
    difficulty: Difficulty
    cuisine: str
    uses: list[str]
    missing: list[str]


class IdeaList(BaseModel):
    ideas: list[DishIdea]


class CookQuestion(BaseModel):
    """A short multiple-choice question asked before dishes are suggested."""

    question: str
    answers: list[str]


class QuestionList(BaseModel):
    questions: list[CookQuestion]


class RecipeIngredient(BaseModel):
    name: str
    amount: str
    have: bool


class FullRecipe(BaseModel):
    title: str
    description: str
    cuisine: str
    minutes: int
    servings: int
    difficulty: Difficulty
    ingredients: list[RecipeIngredient]
    steps: list[str]
    tips: list[str]
    substitutions: list[str]


def json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """JSON schema for a model with `$ref`s inlined and descriptive titles removed."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                return resolve(defs[node["$ref"].rsplit("/", 1)[-1]])
            # "title" is dropped as schema metadata (a string), never as a field name (a sub-schema)
            return {key: resolve(value) for key, value in node.items() if not (key == "title" and isinstance(value, str))}
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    return resolve(schema)
