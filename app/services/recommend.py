"""Builds what the AI is told about a user, and tidies what comes back."""

import re
from dataclasses import dataclass
from datetime import timedelta

from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, select

from app.ai.base import CookContext
from app.models import CookLog, IdeaSet, PantryItem, Recipe, User, utcnow
from app.schemas import DishIdea, FullRecipe
from app.services.safety import Conflict, find_conflicts
from app.services.text import clean, name_key

CUISINES: tuple[str, ...] = ("malaysian", "chinese", "indian", "thai", "japanese", "korean", "western", "italian")
CUISINE_NAMES = {
    "malaysian": "Malaysian", "chinese": "Chinese", "indian": "Indian", "thai": "Thai",
    "japanese": "Japanese", "korean": "Korean", "western": "Western", "italian": "Italian",
}
MEALS: tuple[str, ...] = ("breakfast", "lunch", "dinner", "snack")
SKILLS: tuple[str, ...] = ("beginner", "home", "confident")
TIME_CHOICES: tuple[int, ...] = (15, 30, 45, 60, 0)
MAX_INGREDIENTS = 80

# Basics every kitchen is assumed to have. They never count towards "in hand" and are never "to buy".
STAPLES: frozenset[str] = frozenset({
    "salt", "sea salt", "fine salt", "pepper", "black pepper", "white pepper", "ground pepper",
    "ground black pepper", "ground white pepper", "sugar", "white sugar", "caster sugar", "oil", "cooking oil",
    "vegetable oil", "neutral oil", "water", "hot water", "warm water", "cold water", "ice",
    "盐", "食盐", "细盐", "糖", "白糖", "砂糖", "细砂糖", "油", "食用油", "植物油", "水", "清水", "热水", "温水",
    "冷水", "冰", "冰块", "胡椒粉", "白胡椒粉", "黑胡椒", "黑胡椒粉",
})
_STAPLE_TAILS = (" to taste", " as needed", " for frying", " for cooking", " for seasoning", "适量", "少许")


def is_staple(name: str) -> bool:
    key = name_key(name)
    for tail in _STAPLE_TAILS:
        if key.endswith(tail):
            key = key[: -len(tail)].strip()
    return key in STAPLES
FRESH_HOURS = 18  # how long suggestions count as "tonight's"
# Rice, noodles, sauces and spices usually outlast one dish, so cooking does not remove them by default.
LONG_LASTING: frozenset[str] = frozenset({"grain", "sauce_spice"})


class CookOptions(BaseModel):
    """The choices made on the Cook form. Carried through to recipe writing."""

    ingredients: list[str] = Field(default_factory=list)
    minutes: int = 0
    cuisine: str = ""
    meal: str = ""
    servings: int = 2
    extras_ok: bool = True

    @field_validator("ingredients")
    @classmethod
    def _tidy_ingredients(cls, value: list[str]) -> list[str]:
        lines = [clean(line, 80) for line in value]
        return [line for line in lines if line][:MAX_INGREDIENTS]

    @field_validator("minutes")
    @classmethod
    def _known_time(cls, value: int) -> int:
        return value if value in TIME_CHOICES else 0

    @field_validator("cuisine")
    @classmethod
    def _known_cuisine(cls, value: str) -> str:
        return value if value in CUISINES else ""

    @field_validator("meal")
    @classmethod
    def _known_meal(cls, value: str) -> str:
        return value if value in MEALS else ""

    @field_validator("servings")
    @classmethod
    def _sane_servings(cls, value: int) -> int:
        return min(max(value, 1), 12)


def build_context(session: Session, user: User, options: CookOptions, avoid: list[str] | None = None) -> CookContext:
    """Combine the form choices with the user's profile and cooking history.

    Diet and allergies always come from the saved profile, never from the form.
    `avoid` adds dish titles that should not be suggested again.
    """
    now = utcnow()
    recent = session.exec(
        select(Recipe.title).where(Recipe.user_id == user.id, Recipe.created_at >= now - timedelta(days=10))
        .order_by(Recipe.created_at.desc()).limit(12)
    ).all()
    saved = session.exec(
        select(Recipe.title).where(Recipe.user_id == user.id, Recipe.is_saved == True)  # noqa: E712
        .order_by(Recipe.created_at.desc()).limit(6)
    ).all()
    loved = session.exec(
        select(Recipe.title).join(CookLog, CookLog.recipe_id == Recipe.id)
        .where(CookLog.user_id == user.id, CookLog.rating >= 4)
        .order_by(CookLog.cooked_at.desc()).limit(6)
    ).all()
    liked = list(dict.fromkeys([*loved, *saved]))[:8]
    return CookContext(
        ingredients=options.ingredients,
        lang=user.lang,
        diets=list(user.diets or []),
        allergies=list(user.allergies or []),
        dislikes=user.dislikes or "",
        favourite_cuisines=[CUISINE_NAMES[c] for c in (user.cuisines or []) if c in CUISINE_NAMES],
        skill=user.skill if user.skill in SKILLS else "home",
        minutes=options.minutes,
        cuisine=CUISINE_NAMES.get(options.cuisine, ""),
        meal=options.meal,
        servings=options.servings,
        extras_ok=options.extras_ok,
        recent_titles=[title for title in dict.fromkeys([*(avoid or []), *recent]) if title not in liked],
        liked_titles=liked,
    )


@dataclass
class RankedIdea:
    idea: DishIdea
    conflicts: list[Conflict]

    @property
    def have(self) -> int:
        return len(self.idea.uses)

    @property
    def total(self) -> int:
        return len(self.idea.uses) + len(self.idea.missing)


def _tidy_names(names: list[str], limit: int = 20) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in names:
        name = clean(raw)
        key = name_key(name)
        if key and key not in seen:
            seen.add(key)
            out.append(name)
    return out[:limit]


def tidy_idea(idea: DishIdea) -> DishIdea:
    uses = [name for name in _tidy_names(idea.uses) if not is_staple(name)]
    used = {name_key(name) for name in uses}
    return DishIdea(
        title=clean(idea.title, 90) or "?",
        blurb=clean(idea.blurb, 240),
        minutes=min(max(idea.minutes, 1), 600),
        difficulty=idea.difficulty,
        cuisine=clean(idea.cuisine, 40),
        uses=uses,
        missing=[name for name in _tidy_names(idea.missing) if name_key(name) not in used and not is_staple(name)],
    )


def rank_ideas(ideas: list[DishIdea], user: User) -> list[RankedIdea]:
    """Order ideas: no diet or allergy conflict first, then fewest missing, then quickest."""
    ranked = []
    for idea in ideas:
        idea = tidy_idea(idea)
        conflicts = find_conflicts([idea.title, *idea.uses, *idea.missing], list(user.allergies or []), list(user.diets or []))
        ranked.append(RankedIdea(idea, conflicts))
    ranked.sort(key=lambda r: (bool(r.conflicts), len(r.idea.missing), r.idea.minutes))
    return ranked


def annotate(ideas: list[DishIdea], user: User) -> list[RankedIdea]:
    """Stored ideas in their saved order, checked against the user's current profile."""
    return [
        RankedIdea(idea, find_conflicts([idea.title, *idea.uses, *idea.missing], list(user.allergies or []), list(user.diets or [])))
        for idea in ideas
    ]


def save_ideas(session: Session, user: User, source: str, options: CookOptions, ranked: list[RankedIdea]) -> None:
    """Replace the user's stored suggestions with this ranked set."""
    current = session.exec(select(IdeaSet).where(IdeaSet.user_id == user.id)).first()
    if current is None:
        current = IdeaSet(user_id=user.id)
    current.source = source
    current.options = options.model_dump()
    current.ideas = [r.idea.model_dump() for r in ranked]
    current.created_at = utcnow()
    session.add(current)
    session.commit()


@dataclass
class StoredIdeas:
    source: str
    options: CookOptions
    ideas: list[DishIdea]
    fresh: bool


def recipe_count(ingredients: list[dict]) -> tuple[int, int]:
    """(in hand, total) for a recipe's leaf numeral, leaving out staples like salt and oil."""
    counted = [item for item in ingredients if not item.get("staple", is_staple(item.get("name", "")))]
    return sum(1 for item in counted if item.get("have")), len(counted)


def up_to_date(stored: "StoredIdeas", items: list[PantryItem]) -> list[DishIdea]:
    """Stored ideas with anything since used up moved from "uses" to "missing".

    Only applies to ideas made from the kitchen: an ingredient that was in the
    kitchen when the ideas were made, and is not there now, is now to buy.
    """
    if stored.source != "pantry":
        return stored.ideas
    current = {item.name_key for item in items}
    had = {name_key(re.sub(r"\s*\(.*\)\s*$", "", line)) for line in stored.options.ingredients}
    refreshed = []
    for idea in stored.ideas:
        gone = [name for name in idea.uses if name_key(name) in had and name_key(name) not in current]
        if gone:
            idea = idea.model_copy(update={
                "uses": [name for name in idea.uses if name not in gone],
                "missing": [*gone, *idea.missing],
            })
        refreshed.append(idea)
    return refreshed


def drop_cooked(session: Session, user: User, title: str) -> None:
    """Take a dish off the stored suggestions once it has been cooked (its leaf is torn off)."""
    row = session.exec(select(IdeaSet).where(IdeaSet.user_id == user.id)).first()
    if row is None:
        return
    key = name_key(title)
    remaining = [idea for idea in row.ideas if name_key(idea.get("title", "")) != key]
    if len(remaining) != len(row.ideas):
        row.ideas = remaining
        session.add(row)


def load_ideas(session: Session, user: User) -> StoredIdeas | None:
    row = session.exec(select(IdeaSet).where(IdeaSet.user_id == user.id)).first()
    if row is None or not row.ideas:
        return None
    try:
        options = CookOptions.model_validate(row.options)
        ideas = [DishIdea.model_validate(item) for item in row.ideas]
    except ValueError:
        return None
    fresh = row.created_at >= utcnow() - timedelta(hours=FRESH_HOURS)
    return StoredIdeas(row.source, options, ideas, fresh)


def tidy_recipe(recipe: FullRecipe) -> dict:
    """Clamp and clean an AI recipe before it is stored and shown."""
    ingredients = []
    for item in recipe.ingredients[:40]:
        name = clean(item.name, 80)
        if name:
            staple = is_staple(name)
            ingredients.append({"name": name, "amount": clean(item.amount, 40), "have": staple or bool(item.have),
                                "staple": staple})
    return {
        "title": clean(recipe.title, 90) or "?",
        "description": clean(recipe.description, 400),
        "cuisine": clean(recipe.cuisine, 40),
        "minutes": min(max(recipe.minutes, 1), 600),
        "servings": min(max(recipe.servings, 1), 24),
        "difficulty": recipe.difficulty,
        "ingredients": ingredients,
        "steps": [step for step in (clean(s, 600) for s in recipe.steps[:30]) if step],
        "tips": [tip for tip in (clean(s, 300) for s in recipe.tips[:5]) if tip],
        "substitutions": [sub for sub in (clean(s, 300) for s in recipe.substitutions[:10]) if sub],
    }


def pantry_matches(ingredient_names: list[str], items: list[PantryItem]) -> list[PantryItem]:
    """Pantry items that a recipe appears to use (for the "used up?" list)."""
    keys = [name_key(name) for name in ingredient_names]
    matched = []
    for item in items:
        words = f" {item.name_key} "
        if any(key and (f" {key} " in words or words in f" {key} ") for key in keys):
            matched.append(item)
    return matched
