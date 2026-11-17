"""A user's taste: what they say they love, and what they keep asking the Cook tab for."""

from sqlmodel import Session, select

from app.models import Taste, User, utcnow
from app.services.text import clean, name_key

MAX_CRAVINGS = 8
MAX_ANSWERS = 12
USUAL_AFTER = 2  # a dish type counts as usual once it has been chosen this many times


def get(session: Session, user: User) -> Taste:
    row = session.exec(select(Taste).where(Taste.user_id == user.id)).first()
    return row if row is not None else Taste(user_id=user.id)


def _push(recent: list[str], new: list[str], limit: int) -> list[str]:
    """Newest first, without repeats."""
    out: list[str] = []
    seen: set[str] = set()
    for text in [*new, *recent]:
        key = name_key(text)
        if key and key not in seen:
            seen.add(key)
            out.append(text)
    return out[:limit]


def record(session: Session, user: User, dish_type: str, craving: str, answers: list[str]) -> None:
    """Remember one Cook request. The caller commits."""
    row = get(session, user)
    if dish_type:
        counts = dict(row.dish_types or {})
        counts[dish_type] = counts.get(dish_type, 0) + 1
        row.dish_types = counts
    if craving:
        row.cravings = _push(list(row.cravings or []), [craving], MAX_CRAVINGS)
    if answers:
        row.answers = _push(list(row.answers or []), answers, MAX_ANSWERS)
    row.updated_at = utcnow()
    session.add(row)


def save_likes(session: Session, user: User, likes: str) -> None:
    row = get(session, user)
    row.likes = clean(likes, 200)
    session.add(row)


def summary(session: Session, user: User) -> dict:
    """What is known: typed likes, usual dish types (most chosen first), recent cravings and answers."""
    row = get(session, user)
    counts = row.dish_types or {}
    usual = sorted((kind for kind, n in counts.items() if n >= USUAL_AFTER), key=lambda kind: -counts[kind])
    return {
        "likes": row.likes or "",
        "dish_types": usual[:3],
        "cravings": list(row.cravings or [])[:5],
        "answers": list(row.answers or [])[:6],
    }


def reset(session: Session, user: User) -> None:
    """Forget what was learned; keep what they typed themselves."""
    row = get(session, user)
    row.dish_types, row.cravings, row.answers = {}, [], []
    row.updated_at = utcnow()
    session.add(row)
    session.commit()
