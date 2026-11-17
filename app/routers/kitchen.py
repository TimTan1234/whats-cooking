"""The Kitchen tab: the user's pantry and the two main actions."""

from itertools import groupby
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from sqlmodel import Session, select

from app import i18n
from app.auth import current_user
from app.db import get_session
from app.models import CookLog, PantryItem, Recipe, User
from app.schemas import CATEGORIES
from app.services import pantry, recommend
from app.services.text import clean, name_key
from app.web import flash, owned, redirect, render

router = APIRouter()

# Pantry changes return to the pantry list; ?at=pantry puts their message beside it.
PANTRY = "/?at=pantry#pantry"

@router.get("/")
def kitchen(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    items = pantry.list_items(session, user)
    # Tonight's leaf: from the latest kitchen or "today" suggestions while they are fresh, checked
    # against the profile as it is now, so a newly added allergy never leads with a dish it rules out.
    tonight, tonight_pick = None, 0
    stored = recommend.load_ideas(session, user)
    if stored is not None and stored.fresh and (stored.source == "today" or (stored.source == "pantry" and items)):
        checked = recommend.annotate(recommend.up_to_date(stored, items), user)
        tonight_pick = next((index for index, ranked in enumerate(checked) if not ranked.conflicts), 0)
        tonight = checked[tonight_pick]
    last = session.exec(
        select(CookLog, Recipe)
        .join(Recipe, Recipe.id == CookLog.recipe_id)
        .where(CookLog.user_id == user.id)
        .order_by(CookLog.cooked_at.desc(), CookLog.id.desc())
        .limit(1)
    ).first()
    groups = [(category, list(rows)) for category, rows in groupby(items, key=lambda item: item.category)]
    return render(request, "kitchen.html", user=user, active="kitchen", items=items, groups=groups, tonight=tonight,
                  categories=CATEGORIES,
                  tonight_pick=tonight_pick, pantry_flashes=request.query_params.get("at") == "pantry",
                  tonight_source=stored.source if tonight else "", last=last)


@router.post("/pantry")
def add_item(
    request: Request,
    name: Annotated[str, Form()] = "",
    quantity: Annotated[str, Form()] = "",
    category: Annotated[str, Form()] = "other",
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    if not name_key(clean(name)):
        flash(request, "error", i18n.t(user.lang, "pantry.need_name"))
        return redirect(PANTRY)
    key_name = name_key(clean(name))
    existing = session.exec(
        select(PantryItem).where(PantryItem.user_id == user.id, PantryItem.name_key == key_name)
    ).first()
    shown = existing.name if existing is not None else clean(name)  # the name as the list shows it
    added = pantry.add_items(session, user, [(name, quantity, category)])
    changed = bool(clean(quantity, 40)) or (category in CATEGORIES and category != "other")
    key = "pantry.added_one" if added else "pantry.updated_one" if changed else "pantry.already"
    flash(request, "ok", i18n.t(user.lang, key, name=shown))
    return redirect(PANTRY)


@router.get("/pantry/{item_id}")
def edit_item_page(request: Request, item_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
    item = owned(session, PantryItem, item_id, user)
    return render(request, "pantry_item.html", user=user, active="kitchen", item=item, categories=CATEGORIES)


@router.post("/pantry/{item_id}")
def edit_item(
    request: Request,
    item_id: int,
    name: Annotated[str, Form()] = "",
    quantity: Annotated[str, Form()] = "",
    category: Annotated[str, Form()] = "other",
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    item = owned(session, PantryItem, item_id, user)
    new_name = clean(name)
    key = name_key(new_name)
    if not key:
        flash(request, "error", i18n.t(user.lang, "pantry.need_name"))
        return redirect(f"/pantry/{item_id}")
    clash = session.exec(
        select(PantryItem).where(PantryItem.user_id == user.id, PantryItem.name_key == key, PantryItem.id != item.id)
    ).first()
    if clash is not None:
        flash(request, "error", i18n.t(user.lang, "pantry.duplicate", name=clash.name))
        return redirect(f"/pantry/{item_id}")
    item.name = new_name
    item.name_key = key
    item.quantity = clean(quantity, 40)
    item.category = category if category in CATEGORIES else "other"
    session.add(item)
    session.commit()
    flash(request, "ok", i18n.t(user.lang, "pantry.saved", name=new_name))
    return redirect(PANTRY)


@router.post("/pantry/{item_id}/delete")
def delete_item(request: Request, item_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
    item = owned(session, PantryItem, item_id, user)
    name = item.name
    session.delete(item)
    session.commit()
    flash(request, "ok", i18n.t(user.lang, "pantry.removed", name=name))
    return redirect(PANTRY)
