"""Helpers shared by the page routes: rendering, redirects, flash messages."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app import i18n
from app.ai import get_ai
from app.config import get_settings
from app.models import User

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Changes on every start, so browsers pick up new CSS and JS after an update.
ASSET_VERSION = str(int(datetime.now(timezone.utc).timestamp()))


def current_lang(request: Request, user: User | None = None) -> str:
    if user is not None and user.lang in i18n.LANGS:
        return user.lang
    chosen = request.session.get("lang")
    if chosen in i18n.LANGS:
        return chosen
    accepted = request.headers.get("accept-language", "").casefold()
    return "zh" if accepted.startswith("zh") else "en"


def flash(request: Request, level: str, message: str) -> None:
    """Queue a one-off message for the next page. level: "ok" or "error"."""
    queue = list(request.session.get("flash", []))
    queue.append([level, message])
    request.session["flash"] = queue[-5:]


def redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


def local_day(moment: datetime, lang: str) -> str:
    """A short local date such as "Tue 12 Nov" or "11月12日 周二"."""
    zone = ZoneInfo(get_settings().timezone)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    local = moment.astimezone(zone)
    return i18n.format_day(local, lang)


def render(request: Request, name: str, user: User | None = None, status_code: int = 200, **context: Any):
    lang = current_lang(request, user)
    settings = get_settings()

    def t(key: str, **values: Any) -> str:
        return i18n.t(lang, key, **values)

    context.update(
        user=user,
        lang=lang,
        t=t,
        app_name=settings.app_name,
        ai_service=settings.ai_service,
        demo_mode=get_ai().is_mock,
        flashes=request.session.pop("flash", []),
        asset_version=ASSET_VERSION,
        local_day=lambda moment: local_day(moment, lang),
        today=local_day(datetime.now(timezone.utc), lang),
        rule_label=lambda rule, custom=False: i18n.rule_label(lang, rule, custom),
    )
    context.setdefault("active", "")
    return templates.TemplateResponse(request, name, context, status_code=status_code)


def owned(session: Session, model: type, row_id: int, user: User):
    """Fetch a row by id, but only if it belongs to this user (else 404)."""
    row = session.get(model, row_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=404)
    return row
