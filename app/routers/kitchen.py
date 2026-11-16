"""The Kitchen tab: the user's pantry and the two main actions."""

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

@router.get("/")
def kitchen(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    items = pantry.list_items(session, user)
    # Tonight's leaf: the best match from the latest kitchen suggestions, while they are fresh.
    tonight = None
    stored = recommend.load_ideas(session, user)
    if stored is not None and stored.fresh and stored.source == "pantry" and items:
        tonight = recommend.annotate(recommend.up_to_date(stored, items)[:1], user)[0]
    last = session.exec(
        select(CookLog, Recipe)
        .join(Recipe, Recipe.id == CookLog.recipe_id)
        .where(CookLog.user_id == user.id)
        .order_by(CookLog.cooked_at.desc(), CookLog.id.desc())
        .limit(1)
    ).first()
    return render(request, "kitchen.html", user=user, active="kitchen", items=items, tonight=tonight, last=last)


@router.post("/pantry")
def add_item(
    request: Request,
    name: Annotated[str, Form()] = "",
    quantity: Annotated[str, Form()] = "",
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    if not name_key(clean(name)):
        flash(request, "error", i18n.t(user.lang, "pantry.need_name"))
        return redirect("/")
    added = pantry.add_items(session, user, [(name, quantity, "other")])
    key = "pantry.added_one" if added else "pantry.updated_one"
    flash(request, "ok", i18n.t(user.lang, key, name=clean(name)))
    return redirect("/")


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
    return redirect("/")


@router.post("/pantry/{item_id}/delete")
def delete_item(request: Request, item_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
    item = owned(session, PantryItem, item_id, user)
    name = item.name
    session.delete(item)
    session.commit()
    flash(request, "ok", i18n.t(user.lang, "pantry.removed", name=name))
    return redirect("/")
