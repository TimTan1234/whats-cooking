"""Pantry operations shared by the kitchen and scan pages."""

from sqlmodel import Session, select

from app.models import PantryItem, User
from app.schemas import CATEGORIES
from app.services.text import clean, name_key

MAX_ITEMS = 300


def list_items(session: Session, user: User) -> list[PantryItem]:
    items = session.exec(select(PantryItem).where(PantryItem.user_id == user.id)).all()
    order = {category: index for index, category in enumerate(CATEGORIES)}
    return sorted(items, key=lambda item: (order.get(item.category, len(order)), item.name.casefold()))


def add_items(session: Session, user: User, entries: list[tuple[str, str, str]]) -> int:
    """Add (name, quantity, category) entries, merging with what is there.

    Returns how many new ingredients were added. An ingredient the user already
    has keeps its row; its quantity is updated when a new one is given.
    """
    existing = {item.name_key: item for item in list_items(session, user)}
    added = 0
    for raw_name, raw_quantity, raw_category in entries:
        name = clean(raw_name)
        key = name_key(name)
        if not key:
            continue
        quantity = clean(raw_quantity, 40)
        category = raw_category if raw_category in CATEGORIES else "other"
        item = existing.get(key)
        if item is not None:
            if quantity:
                item.quantity = quantity
            if category != "other":
                item.category = category
            session.add(item)
            continue
        if len(existing) >= MAX_ITEMS:
            break
        item = PantryItem(user_id=user.id, name=name, name_key=key, quantity=quantity, category=category)
        session.add(item)
        existing[key] = item
        added += 1
    session.commit()
    return added


def describe(items: list[PantryItem]) -> list[str]:
    """Ingredient lines for the AI prompt, e.g. "Eggs (6)"."""
    return [f"{item.name} ({item.quantity})" if item.quantity else item.name for item in items]
