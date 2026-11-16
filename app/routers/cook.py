"""The Cook tab: "what should I cook?" and the dish suggestions."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from sqlmodel import Session

from app import i18n
from app.ai import AIError, get_ai
from app.auth import current_user
from app.db import get_session
from app.models import User
from app.services import pantry, recommend
from app.services.recommend import CookOptions
from app.web import flash, redirect, render

router = APIRouter()
log = logging.getLogger("whatscooking.cook")


def cook_form(request: Request, user: User, session: Session, source: str = "pantry", custom: str = "",
              options: CookOptions | None = None, error: str = "", status_code: int = 200):
    items = pantry.list_items(session, user)
    if not items and source == "pantry" and not custom:
        source = "custom"
    rules = [i18n.rule_label(user.lang, rule, rule not in i18n.KNOWN_RULES)
             for rule in [*(user.diets or []), *(user.allergies or [])]]
    return render(
        request, "cook.html", user=user, active="cook", status_code=status_code, error=error,
        pantry_count=len(items), source=source, custom=custom,
        options=options or CookOptions(), rules=rules,
        cuisines=recommend.CUISINES, meals=recommend.MEALS, times=recommend.TIME_CHOICES,
    )


async def _suggest_and_store(session: Session, user: User, source: str, options: CookOptions,
                             avoid: list[str] | None = None) -> bool:
    """Ask the AI for dishes and store them. Returns False when nothing came back."""
    ctx = recommend.build_context(session, user, options, avoid)
    ideas = await get_ai().suggest_dishes(ctx)
    ranked = recommend.rank_ideas(ideas[:8], user)
    if not ranked:
        return False
    recommend.save_ideas(session, user, source, options, ranked)
    return True


@router.get("/cook")
def cook_page(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    return cook_form(request, user, session)


@router.post("/cook")
async def suggest(
    request: Request,
    source: Annotated[str, Form()] = "pantry",
    custom: Annotated[str, Form()] = "",
    minutes: Annotated[int, Form()] = 0,
    cuisine: Annotated[str, Form()] = "",
    meal: Annotated[str, Form()] = "",
    servings: Annotated[int, Form()] = 2,
    extras_ok: Annotated[str, Form()] = "",
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    lang = user.lang
    custom = custom[:6000]
    if source == "custom":
        lines = custom.replace("，", "\n").replace(",", "\n").splitlines()
    else:
        source = "pantry"
        lines = pantry.describe(pantry.list_items(session, user))
    options = CookOptions(ingredients=lines, minutes=minutes, cuisine=cuisine, meal=meal,
                          servings=servings, extras_ok=bool(extras_ok))
    if not options.ingredients:
        key = "cook.empty_custom" if source == "custom" else "cook.empty_pantry"
        return cook_form(request, user, session, source, custom, options, i18n.t(lang, key), 400)

    try:
        found = await _suggest_and_store(session, user, source, options)
    except AIError as exc:
        log.warning("Dish suggestions failed: %s", exc)
        return cook_form(request, user, session, source, custom, options, i18n.t(lang, f"ai.{exc.kind}"), 502)
    if not found:
        return cook_form(request, user, session, source, custom, options, i18n.t(lang, "cook.no_ideas"), 200)
    return redirect("/cook/ideas")


@router.get("/cook/ideas")
def ideas_page(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    stored = recommend.load_ideas(session, user)
    if stored is None:
        return redirect("/cook")
    ideas = recommend.up_to_date(stored, pantry.list_items(session, user))
    return render(request, "ideas.html", user=user, active="cook",
                  ranked=recommend.annotate(ideas, user), options=stored.options)


@router.post("/cook/again")
async def suggest_again(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    """Different dishes for the same choices, avoiding the ones just shown."""
    stored = recommend.load_ideas(session, user)
    if stored is None:
        return redirect("/cook")
    options = stored.options
    if stored.source == "pantry":  # the kitchen may have changed since
        options = options.model_copy(update={"ingredients": pantry.describe(pantry.list_items(session, user))})
        options = CookOptions.model_validate(options.model_dump())
        if not options.ingredients:
            return redirect("/cook")
    try:
        found = await _suggest_and_store(session, user, stored.source, options, [idea.title for idea in stored.ideas])
    except AIError as exc:
        log.warning("Dish suggestions failed: %s", exc)
        flash(request, "error", i18n.t(user.lang, f"ai.{exc.kind}"))
        return redirect("/cook/ideas")
    if not found:
        flash(request, "error", i18n.t(user.lang, "cook.no_ideas"))
    return redirect("/cook/ideas")
