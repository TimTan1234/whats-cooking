"""Profile: language, diet, allergies, tastes and password."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from sqlmodel import Session

from app import auth, i18n
from app.auth import current_user
from app.db import get_session
from app.models import User
from app.services import recommend, taste
from app.services.safety import ALLERGENS, DIETS
from app.services.text import clean, split_list
from app.web import flash, redirect, render

router = APIRouter()


@router.get("/profile")
def profile_page(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    known = [a for a in user.allergies or [] if a in ALLERGENS]
    other = [a for a in user.allergies or [] if a not in ALLERGENS]
    return render(
        request, "profile.html", user=user, active="profile",
        diets=DIETS, allergens=ALLERGENS, cuisines=recommend.CUISINES, skills=recommend.SKILLS,
        known_allergies=known, other_allergies=", ".join(other), min_password=auth.MIN_PASSWORD_LENGTH,
        taste=taste.summary(session, user),
    )


@router.post("/profile")
async def save_profile(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    form = await request.form()
    lang = form.get("lang", user.lang)
    user.lang = lang if lang in i18n.LANGS else user.lang
    user.diets = [d for d in DIETS if d in form.getlist("diets")]
    known = [a for a in ALLERGENS if a in form.getlist("allergies")]
    other = [a for a in split_list(str(form.get("other_allergies", "")), 12) if a not in ALLERGENS]
    user.allergies = [*known, *other]
    user.dislikes = clean(form.get("dislikes", ""), 200)
    user.cuisines = [c for c in recommend.CUISINES if c in form.getlist("cuisines")]
    skill = form.get("skill", user.skill)
    user.skill = skill if skill in recommend.SKILLS else "home"
    taste.save_likes(session, user, str(form.get("likes", "")))
    session.add(user)
    session.commit()
    request.session["lang"] = user.lang
    flash(request, "ok", i18n.t(user.lang, "profile.saved"))
    return redirect("/profile")


@router.post("/profile/taste/reset")
def forget_taste(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    taste.reset(session, user)
    flash(request, "ok", i18n.t(user.lang, "taste.forgotten"))
    return redirect("/profile")


@router.post("/profile/password")
def change_password(
    request: Request,
    current: Annotated[str, Form()] = "",
    new: Annotated[str, Form()] = "",
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    if not auth.verify_password(user.password_hash, current):
        flash(request, "error", i18n.t(user.lang, "profile.wrong_password"))
        return redirect("/profile")
    if len(new) < auth.MIN_PASSWORD_LENGTH:
        flash(request, "error", i18n.t(user.lang, "profile.short_password", n=auth.MIN_PASSWORD_LENGTH))
        return redirect("/profile")
    user.password_hash = auth.hash_password(new)
    session.add(user)
    session.commit()
    auth.sign_in(request, user)  # keeps this device signed in; other devices are signed out
    flash(request, "ok", i18n.t(user.lang, "profile.password_changed"))
    return redirect("/profile")
