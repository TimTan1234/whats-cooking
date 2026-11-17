"""The Cook tab: "what should I cook?", the AI's questions, and the dish suggestions."""

import logging
import re
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from sqlmodel import Session, select

from app import i18n
from app.ai import AIError, get_ai
from app.auth import current_user
from app.db import get_session
from app.models import CookDraft, User, utcnow
from app.schemas import CookQuestion
from app.services import pantry, recommend, taste
from app.services.recommend import CookOptions
from app.services.text import clean
from app.web import flash, local_date, local_path, redirect, render

router = APIRouter()
log = logging.getLogger("whatscooking.cook")
LIST_SEPARATORS = re.compile(r"[,，、;；\n]+")  # as people type lists, in English and Chinese
OPEN_ORDER = timedelta(hours=3)  # how long an unfinished order still counts as this sitting's

MAX_QUESTIONS = 3
MAX_ANSWERS = 4
PANTRY_PREVIEW = 5  # kitchen items named under the source chips


def cook_form(request: Request, user: User, session: Session, source: str = "pantry", custom: str = "",
              options: CookOptions | None = None):
    items = pantry.list_items(session, user)
    if not items and source == "pantry" and not custom:
        source = "custom"
    diets, allergies = ([i18n.rule_label(user.lang, rule, rule not in i18n.KNOWN_RULES) for rule in rules or []]
                        for rules in (user.diets, user.allergies))
    return render(
        request, "cook.html", user=user, active="cook", invalid=request.session.pop("cook_invalid", ""),
        pantry_count=len(items), pantry_names=[item.name for item in items[:PANTRY_PREVIEW]], source=source, custom=custom,
        options=options or CookOptions(), diets=diets, allergies=allergies, dish_types=recommend.DISH_TYPES,
        cuisines=recommend.CUISINES, meals=recommend.MEALS, times=recommend.TIME_CHOICES,
    )


async def _suggest_and_store(session: Session, user: User, source: str, options: CookOptions,
                             avoid: list[str] | None = None, learn: bool = False) -> bool:
    """Ask the AI for dishes and store them. Returns False when nothing came back.

    `learn` remembers this request's dish type, craving and answers in the user's taste.
    """
    today = source == "today"
    ctx = recommend.build_context(session, user, options, avoid, today=today)
    ideas = await get_ai().suggest_dishes(ctx)
    ranked = recommend.rank_ideas(ideas[:8], user, by_kitchen=not today)
    if not ranked:
        return False
    if learn:
        taste.record(session, user, options.dish_type, options.craving, options.answers)
    recommend.save_ideas(session, user, source, options, ranked)
    return True


def _read_choices(session: Session, user: User, source: str, custom: str, minutes: int, cuisine: str, meal: str,
                  servings: int, extras_ok: str, dish_type: str, craving: str) -> tuple[str, CookOptions]:
    if source == "custom":
        lines = LIST_SEPARATORS.split(custom)
    else:
        source = "pantry"
        lines = pantry.describe(pantry.list_items(session, user))
    options = CookOptions(ingredients=lines, minutes=minutes, cuisine=cuisine, meal=meal, servings=servings,
                          extras_ok=bool(extras_ok), dish_type=dish_type, craving=craving)
    return source, options


def _tidy_questions(questions: list[CookQuestion]) -> list[dict]:
    tidy = []
    for question in questions[:MAX_QUESTIONS]:
        text = clean(question.question, 120)
        answers = list(dict.fromkeys(a for a in (clean(a, 40) for a in question.answers) if a))[:MAX_ANSWERS]
        if text and len(answers) >= 2:
            tidy.append({"question": text, "answers": answers})
    return tidy


def _answer(question: dict, picked: str) -> str:
    return f"{question['question']} → {picked}"


def _draft(session: Session, user: User) -> CookDraft | None:
    return session.exec(select(CookDraft).where(CookDraft.user_id == user.id)).first()


def _save_draft(session: Session, user: User, source: str, custom: str, options: CookOptions,
                questions: list[dict] | None = None) -> None:
    draft = _draft(session, user) or CookDraft(user_id=user.id)
    draft.source = source
    draft.options = {**options.model_dump(), "custom": custom}
    draft.questions = questions or []
    draft.created_at = utcnow()
    session.add(draft)
    session.commit()


def _last_choices(session: Session, user: User) -> tuple[str, str, CookOptions, bool] | None:
    """The latest request as (source, custom list, options, still open): the draft, or the choices behind the
    current dishes. A draft from this sitting is an order still on its way to dishes."""
    draft = _draft(session, user)
    stored = recommend.load_ideas(session, user)
    if draft is not None and (stored is None or draft.created_at >= stored.made):
        still_open = utcnow() - draft.created_at < OPEN_ORDER
        return draft.source, str(draft.options.get("custom", "")), CookOptions.model_validate(draft.options), still_open
    if stored is not None and stored.source in ("pantry", "custom"):
        custom = "\n".join(stored.options.ingredients) if stored.source == "custom" else ""
        return stored.source, custom, stored.options, False
    return None


def _send_back(request: Request, session: Session, user: User, source: str, custom: str, options: CookOptions,
               message_key: str, questions: list[dict] | None = None):
    """Keep the choices, say what went wrong, and go back to the questions or the form.

    An empty typed list is pointed out at the list itself; anything else is a message at the top of the page.
    """
    _save_draft(session, user, source, custom, options, questions)
    if message_key == "cook.empty_custom":
        request.session["cook_invalid"] = "custom"
    else:
        flash(request, "error", i18n.t(user.lang, message_key))
    return redirect("/cook/questions" if questions else "/cook?change=1")


def _drop_draft(session: Session, user: User) -> None:
    draft = _draft(session, user)
    if draft is not None:
        session.delete(draft)
        session.commit()


async def _suggest_now(request: Request, session: Session, user: User, source: str, custom: str,
                       options: CookOptions, questions: list[dict] | None = None):
    """Make ideas from the choices and go to them, or go back with what went wrong."""
    try:
        found = await _suggest_and_store(session, user, source, options, learn=True)
    except AIError as exc:
        log.warning("Dish suggestions failed: %s", exc)
        return _send_back(request, session, user, source, custom, options, f"ai.{exc.kind}", questions)
    if not found:
        return _send_back(request, session, user, source, custom, options, "cook.no_ideas", questions)
    _drop_draft(session, user)
    return redirect("/cook/ideas")


@router.get("/cook")
def cook_page(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    # ?custom= carries a list handed over from the Scan review ("Cook with just these")
    custom = request.query_params.get("custom", "")[:6000]
    if custom:
        return cook_form(request, user, session, source="custom", custom=custom)
    # ?change= brings back all of the latest choices ("Change my choices", or after something went wrong),
    # and so does an order still open (Back from the questions, or a tab switch while they wait)
    last = _last_choices(session, user)
    if last is not None and (request.query_params.get("change") or last[3]):
        return cook_form(request, user, session, *last[:3])
    # otherwise only the settings carry over; the dish and the craving are tonight's to choose
    settings = CookOptions()
    if last is not None:
        settings = last[2].model_copy(update={"ingredients": [], "dish_type": "", "craving": "", "answers": []})
    return cook_form(request, user, session, options=settings)


@router.post("/cook/questions")
async def ask_questions(
    request: Request,
    source: Annotated[str, Form()] = "pantry",
    custom: Annotated[str, Form()] = "",
    minutes: Annotated[int, Form()] = 0,
    cuisine: Annotated[str, Form()] = "",
    meal: Annotated[str, Form()] = "",
    servings: Annotated[int, Form()] = 2,
    extras_ok: Annotated[str, Form()] = "",
    dish_type: Annotated[str, Form()] = "",
    craving: Annotated[str, Form()] = "",
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    """Step 2: the AI asks a few questions. If it has none, or cannot be reached, suggest straight away."""
    custom = custom[:6000]
    source, options = _read_choices(session, user, source, custom, minutes, cuisine, meal, servings, extras_ok,
                                    dish_type, craving)
    if not options.ingredients:
        key = "cook.empty_custom" if source == "custom" else "cook.empty_pantry"
        return _send_back(request, session, user, source, custom, options, key)

    try:
        questions = _tidy_questions(await get_ai().ask_questions(recommend.build_context(session, user, options)))
    except AIError as exc:
        log.warning("Questions failed, suggesting without them: %s", exc)
        questions = []
    if not questions:
        return await _suggest_now(request, session, user, source, custom, options)

    _save_draft(session, user, source, custom, options, questions)
    return redirect("/cook/questions")


@router.get("/cook/questions")
def questions_page(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    draft = _draft(session, user)
    if draft is None or not draft.questions:
        return redirect("/cook")
    # answers kept from a try that failed stay picked
    answered = set(draft.options.get("answers", []))
    picked = [next((a for a in q["answers"] if _answer(q, a) in answered), "") for q in draft.questions]
    return render(request, "cook_questions.html", user=user, active="cook", questions=draft.questions,
                  picked=picked, source=draft.source, options=CookOptions.model_validate(draft.options))


@router.post("/cook/answers")
async def answer_questions(request: Request, user: User = Depends(current_user),
                           session: Session = Depends(get_session)):
    """Step 3: the answers join the choices and the dishes are suggested."""
    draft = _draft(session, user)
    if draft is None or not draft.questions:
        return redirect("/cook")
    form = await request.form()
    answers = []
    for index, question in enumerate(draft.questions):
        picked = str(form.get(f"q{index}", ""))
        if picked in question["answers"]:  # anything else is "either is fine"
            answers.append(_answer(question, picked))
    custom = str(draft.options.get("custom", ""))
    options = CookOptions.model_validate({**draft.options, "answers": answers})
    return await _suggest_now(request, session, user, draft.source, custom, options, draft.questions)


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
    dish_type: Annotated[str, Form()] = "",
    craving: Annotated[str, Form()] = "",
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    """Suggest dishes straight from the choices, without questions."""
    custom = custom[:6000]
    source, options = _read_choices(session, user, source, custom, minutes, cuisine, meal, servings, extras_ok,
                                    dish_type, craving)
    if not options.ingredients:
        key = "cook.empty_custom" if source == "custom" else "cook.empty_pantry"
        return _send_back(request, session, user, source, custom, options, key)
    return await _suggest_now(request, session, user, source, custom, options)


@router.post("/today")
async def today_for_you(request: Request, back: Annotated[str, Form()] = "/", user: User = Depends(current_user),
                        session: Session = Depends(get_session)):
    """Dishes chosen from the user's taste, not their kitchen. Kept for the rest of the local day.

    If none come back, the user returns to the page they asked from.
    """
    stored = recommend.load_ideas(session, user)
    if stored is not None and stored.source == "today" and local_date(stored.made) == local_date(utcnow()):
        return redirect("/cook/ideas")
    options = CookOptions(ingredients=pantry.describe(pantry.list_items(session, user)))
    try:
        found = await _suggest_and_store(session, user, "today", options)
    except AIError as exc:
        log.warning("Today's suggestions failed: %s", exc)
        flash(request, "error", i18n.t(user.lang, f"ai.{exc.kind}"))
        return redirect(local_path(back))
    if not found:
        flash(request, "error", i18n.t(user.lang, "today.no_ideas"))
        return redirect(local_path(back))
    return redirect("/cook/ideas")


@router.get("/cook/ideas")
def ideas_page(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    stored = recommend.load_ideas(session, user)
    if stored is None:
        return redirect("/cook")
    ideas = recommend.up_to_date(stored, pantry.list_items(session, user))
    ranked = recommend.annotate(ideas, user)
    # every dish clashes with the profile: one warning for the page, before the leaves
    clash = [] if not all(r.conflicts for r in ranked) else list(dict.fromkeys(
        i18n.rule_label(user.lang, c.rule, c.custom) for r in ranked for c in r.conflicts))
    return render(request, "ideas.html", user=user, active="cook",
                  ranked=ranked, clash=clash, options=stored.options, source=stored.source)


@router.post("/cook/again")
async def suggest_again(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    """Different dishes for the same choices, avoiding the ones just shown."""
    stored = recommend.load_ideas(session, user)
    if stored is None:
        return redirect("/cook")
    options = stored.options
    if stored.source in recommend.KITCHEN_SOURCES:  # the kitchen may have changed since
        options = CookOptions.model_validate(
            {**options.model_dump(), "ingredients": pantry.describe(pantry.list_items(session, user))})
        if not options.ingredients and stored.source == "pantry":
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
