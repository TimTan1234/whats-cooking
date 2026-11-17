"""Recipes: writing one from a chosen dish, saving, and the cooked log."""

import logging
from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlmodel import Session, select

from app import i18n
from app.ai import AIError, get_ai
from app.auth import current_user
from app.db import get_session
from app.models import CookLog, PantryItem, Recipe, User
from app.schemas import DishIdea
from app.services import pantry, recommend
from app.services.recommend import CookOptions
from app.services.safety import dish_conflicts
from app.services.text import name_key
from app.web import flash, owned, redirect, render

router = APIRouter()
log = logging.getLogger("whatscooking.recipes")


@router.get("/recipes")
def recipes_page(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    saved = session.exec(
        select(Recipe).where(Recipe.user_id == user.id, Recipe.is_saved == True)  # noqa: E712
        .order_by(Recipe.created_at.desc())
    ).all()
    # What helps choose between saved dishes: how much of each the kitchen has now, and how it went last time.
    items = pantry.list_items(session, user)
    ratings = _last_ratings(session, user)
    titles = Counter(name_key(recipe.title) for recipe in saved)
    rows = []
    for recipe in saved:
        have, total = recommend.recipe_count(recommend.in_hand_now(recipe.data.get("ingredients", []), items))
        rows.append({"recipe": recipe, "have": have, "total": total, "rating": ratings.get(recipe.id),
                     "twin": titles[name_key(recipe.title)] > 1})
    cooked = session.exec(
        select(CookLog, Recipe).join(Recipe, Recipe.id == CookLog.recipe_id)
        .where(CookLog.user_id == user.id)
        .order_by(CookLog.cooked_at.desc(), CookLog.id.desc()).limit(50)
    ).all()
    return render(request, "recipes.html", user=user, active="saved", saved=rows, cooked=cooked)


def _last_ratings(session: Session, user: User) -> dict[int, int]:
    """The most recent rating given to each of the user's recipes."""
    rated = session.exec(
        select(CookLog).where(CookLog.user_id == user.id, CookLog.rating != None)  # noqa: E711
        .order_by(CookLog.cooked_at.desc(), CookLog.id.desc())
    ).all()
    latest: dict[int, int] = {}
    for log_row in rated:
        latest.setdefault(log_row.recipe_id, log_row.rating)
    return latest


def _recipe_error(request: Request, user: User, kind: str, dish: DishIdea, pick: int):
    return render(request, "recipe_error.html", user=user, active="cook", status_code=502,
                  error=i18n.t(user.lang, f"ai.{kind}"), dish=dish, pick=pick)


@router.post("/recipes")
async def create_recipe(
    request: Request,
    pick: Annotated[int, Form()] = 0,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    """Write the full recipe for one of the user's stored dish suggestions."""
    lang = user.lang
    stored = recommend.load_ideas(session, user)
    if stored is None or not 0 <= pick < len(stored.ideas):
        flash(request, "error", i18n.t(lang, "recipe.bad_request"))
        return redirect("/cook")
    # Write from the kitchen as it is now, matching what the leaf showed.
    items = pantry.list_items(session, user)
    dish = recommend.up_to_date(stored, items)[pick]
    options = stored.options
    if stored.source in recommend.KITCHEN_SOURCES and items:
        options = CookOptions.model_validate({**options.model_dump(), "ingredients": pantry.describe(items)})

    ctx = recommend.build_context(session, user, options)
    try:
        written = await get_ai().write_recipe(ctx, dish)
    except AIError as exc:
        log.warning("Recipe writing failed: %s", exc)
        return _recipe_error(request, user, exc.kind, dish, pick)

    data = recommend.tidy_recipe(written)
    if not data["ingredients"] or not data["steps"]:
        return _recipe_error(request, user, "failed", dish, pick)
    data["uses"] = dish.uses  # the kitchen ingredients this dish was chosen for
    recommend.link_to_kitchen(data["ingredients"], items)
    recipe = Recipe(
        user_id=user.id, title=data["title"], cuisine=data["cuisine"], minutes=data["minutes"],
        difficulty=data["difficulty"], lang=lang, data=data,
    )
    session.add(recipe)
    session.commit()
    session.refresh(recipe)
    return redirect(f"/recipes/{recipe.id}")


def _recipe(session: Session, recipe_id: int, user: User) -> Recipe:
    """One of the user's recipes that can still be opened (a deleted one only keeps its cooking history)."""
    recipe = owned(session, Recipe, recipe_id, user)
    if recipe.data.get("removed"):
        raise HTTPException(status_code=404)
    return recipe


def _from_saved(request: Request) -> bool:
    return request.query_params.get("from") == "saved"


@router.get("/recipes/{recipe_id}")
def recipe_page(request: Request, recipe_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
    recipe = _recipe(session, recipe_id, user)
    written = recipe.data.get("ingredients", [])
    names = [item.get("name", "") for item in written]
    conflicts = dish_conflicts(recipe.title, names, list(user.allergies or []), list(user.diets or []))
    items = pantry.list_items(session, user)
    used = recommend.pantry_matches([*names, *recipe.data.get("uses", [])], items)
    ingredients = recommend.in_hand_now(written, items)  # the kitchen may have changed since it was written
    logs = session.exec(
        select(CookLog).where(CookLog.user_id == user.id, CookLog.recipe_id == recipe.id)
        .order_by(CookLog.cooked_at.desc(), CookLog.id.desc())
    ).all()
    have, total = recommend.recipe_count(ingredients)
    torn_have, _ = recommend.recipe_count(written)  # the leaf as it read before this cook used things up
    # Opened from the Saved tab (either list), the page belongs to Saved even once it is no longer saved.
    from_saved = _from_saved(request)
    in_saved = from_saved or recipe.is_saved
    return render(
        request, "recipe.html", user=user, active="saved" if in_saved else "cook",
        in_saved=in_saved, keep_from="?from=saved" if from_saved else "",
        recipe=recipe, data=recipe.data, ingredients=ingredients, conflicts=conflicts, used=used, keeps=recommend.LONG_LASTING,
        times_cooked=len(logs), last_rating=next((log_row.rating for log_row in logs if log_row.rating), None),
        last_cooked=logs[0].cooked_at if logs else None,
        have=have, total=total, torn_have=torn_have,
    )


@router.post("/recipes/{recipe_id}/save")
def toggle_saved(request: Request, recipe_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
    recipe = _recipe(session, recipe_id, user)
    recipe.is_saved = not recipe.is_saved
    session.add(recipe)
    session.commit()
    flash(request, "ok", i18n.t(user.lang, "recipe.saved" if recipe.is_saved else "recipe.unsaved"))
    return redirect(f"/recipes/{recipe_id}{'?from=saved' if _from_saved(request) else ''}")


@router.post("/recipes/{recipe_id}/cooked")
async def mark_cooked(request: Request, recipe_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
    recipe = _recipe(session, recipe_id, user)
    form = await request.form()
    try:
        rating = int(form.get("rating", 0))
    except (TypeError, ValueError):
        rating = 0
    session.add(CookLog(user_id=user.id, recipe_id=recipe.id, rating=rating if 1 <= rating <= 5 else None))
    recommend.drop_cooked(session, user, recipe.title)
    removed = 0
    for raw_id in form.getlist("used"):
        try:
            item = session.get(PantryItem, int(raw_id))
        except (TypeError, ValueError):
            continue
        if item is not None and item.user_id == user.id:
            session.delete(item)
            removed += 1
    session.commit()
    message = i18n.t(user.lang, "recipe.cooked_removed", n=removed) if removed else i18n.t(user.lang, "recipe.cooked_plain")
    flash(request, "ok", message)
    return redirect(f"/recipes/{recipe_id}?cooked=1{'&from=saved' if _from_saved(request) else ''}")  # the leaf tears once, on this visit only


@router.post("/recipes/{recipe_id}/delete")
def delete_recipe(request: Request, recipe_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
    recipe = _recipe(session, recipe_id, user)
    cooked = session.exec(select(CookLog.id).where(CookLog.recipe_id == recipe.id, CookLog.user_id == user.id)).first()
    if cooked is None:
        session.delete(recipe)
        message = "recipe.deleted"
    else:
        # Its cooks and ratings stay in the history and keep shaping suggestions; only the title is kept with them.
        recipe.is_saved = False
        recipe.data = {"removed": True}
        session.add(recipe)
        message = "recipe.deleted_history_kept"
    session.commit()
    flash(request, "ok", i18n.t(user.lang, message))
    return redirect("/recipes")
