"""Sign in, sign out and the language switch."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from sqlmodel import Session

from app import auth, i18n
from app.db import get_session
from app.models import User
from app.web import current_lang, local_path, redirect, remember_language, render

router = APIRouter()


def _signed_in_user(request: Request, session: Session) -> User | None:
    try:
        return auth.current_user(request, session)
    except auth.NotAuthenticated:
        return None


@router.get("/login")
def login_page(request: Request, session: Session = Depends(get_session)):
    if _signed_in_user(request, session) is not None:
        return redirect("/")
    return render(request, "login.html")


@router.post("/login")
def login(
    request: Request,
    username: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    session: Session = Depends(get_session),
):
    name = auth.normalise_username(username)
    lang = current_lang(request)
    if auth.is_locked(name):
        return render(request, "login.html", status_code=429, username=name, error=i18n.t(lang, "login.locked"))
    user = auth.authenticate(session, name, password)
    if user is None:
        auth.record_failure(name)
        return render(request, "login.html", status_code=401, username=name, error=i18n.t(lang, "login.wrong"))
    auth.clear_failures(name)
    auth.sign_in(request, user)
    return redirect("/")


@router.post("/logout")
def logout(request: Request):
    lang = request.session.get("lang")
    auth.sign_out(request)
    if lang in i18n.LANGS:
        request.session["lang"] = lang
    return redirect("/login")


@router.post("/lang")
def set_language(
    request: Request,
    lang: Annotated[str, Form()] = "en",
    back: Annotated[str, Form()] = "/",
    session: Session = Depends(get_session),
):
    remember_language(request, session, _signed_in_user(request, session), lang)
    return redirect(local_path(back))
