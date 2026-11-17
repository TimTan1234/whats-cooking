"""Database tables. Every row except User belongs to exactly one user."""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    lang: str = "en"
    diets: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    allergies: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    dislikes: str = ""
    cuisines: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    skill: str = "home"
    created_at: datetime = Field(default_factory=utcnow)


class PantryItem(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "name_key", name="uq_pantry_user_key"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    name_key: str
    quantity: str = ""
    category: str = "other"
    added_at: datetime = Field(default_factory=utcnow)


class Recipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str
    cuisine: str = ""
    minutes: int = 0
    difficulty: str = "easy"
    lang: str = "en"
    data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    is_saved: bool = False
    created_at: datetime = Field(default_factory=utcnow)


class CookLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    recipe_id: int = Field(foreign_key="recipe.id", index=True)
    rating: Optional[int] = None
    cooked_at: datetime = Field(default_factory=utcnow)


class IdeaSet(SQLModel, table=True):
    """The latest dish suggestions for a user (one row per user, replaced each time)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    source: str = "pantry"
    options: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    ideas: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utcnow)


class Taste(SQLModel, table=True):
    """What a user likes: typed on the profile, and learned from what they ask the Cook tab for."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    likes: str = ""
    dish_types: dict[str, int] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    cravings: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    answers: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    updated_at: datetime = Field(default_factory=utcnow)


class CookDraft(SQLModel, table=True):
    """The latest Cook choices on their way to dishes, with the AI's questions if it asked any (one row per user)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True, unique=True)
    source: str = "pantry"
    options: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    questions: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utcnow)
