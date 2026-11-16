"""The Scan tab: photos in, a reviewable ingredient list out."""

import asyncio
import base64
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session
from starlette.datastructures import UploadFile

from app import i18n
from app.ai import AIError, get_ai
from app.auth import current_user
from app.config import get_settings
from app.db import get_session
from app.models import User
from app.schemas import CATEGORIES
from app.services import detect, pantry
from app.services.detect import Found
from app.services.images import ImageRejected, annotate, prepare_image
from app.services.text import clean, name_key
from app.web import flash, redirect, render

router = APIRouter()
log = logging.getLogger("whatscooking.scan")

BLANK_ROWS = 3
MAX_ROWS = detect.MAX_FOUND


def _scan_page(request: Request, user: User, error: str = "", status_code: int = 200):
    settings = get_settings()
    return render(
        request, "scan.html", user=user, active="scan", error=error, status_code=status_code,
        max_photos=settings.max_photos, max_mb=settings.max_upload_mb,
    )


@router.get("/scan")
def scan_page(request: Request, user: User = Depends(current_user)):
    return _scan_page(request, user)


@router.post("/scan")
async def scan(request: Request, user: User = Depends(current_user)):
    settings = get_settings()
    lang = user.lang
    form = await request.form()
    uploads = [item for item in form.getlist("photos") if isinstance(item, UploadFile) and item.filename]
    if not uploads:
        return _scan_page(request, user, i18n.t(lang, "scan.no_photo"), 400)
    if len(uploads) > settings.max_photos:
        return _scan_page(request, user, i18n.t(lang, "scan.too_many", n=settings.max_photos), 400)

    limit = settings.max_upload_mb * 1024 * 1024
    images: list[bytes] = []
    for upload in uploads:
        raw = await upload.read(limit + 1)
        if len(raw) > limit:
            return _scan_page(request, user, i18n.t(lang, "scan.too_big", mb=settings.max_upload_mb), 413)
        try:
            images.append(await run_in_threadpool(prepare_image, raw))
        except ImageRejected:
            return _scan_page(request, user, i18n.t(lang, "scan.not_image", name=clean(upload.filename, 40)), 400)

    try:
        found = await find_ingredients(images, lang)
    except AIError as exc:
        log.warning("Ingredient detection failed: %s", exc)
        return _scan_page(request, user, i18n.t(lang, f"ai.{exc.kind}"), 502)
    if not found:
        return _scan_page(request, user, i18n.t(lang, "scan.nothing_found"), 200)

    photos = []
    for index, image in enumerate(images):
        marks = [(item.number, box, item.confidence == "low")
                 for item in found for photo, box in item.boxes if photo == index]
        preview = await run_in_threadpool(annotate, image, marks)
        photos.append("data:image/jpeg;base64," + base64.b64encode(preview).decode("ascii"))
    return render(request, "scan_review.html", user=user, active="scan", rows=found,
                  blank_rows=BLANK_ROWS, photos=photos)


async def find_ingredients(images: list[bytes], lang: str) -> list[Found]:
    """Read each photo on its own (in parallel), then merge into one numbered list."""
    ai = get_ai()
    answers = await asyncio.gather(*(ai.detect_ingredients(image, lang) for image in images))
    return detect.merge([answer.ingredients for answer in answers])


def read_review_form(form) -> list[tuple[str, str, str]]:
    """Read the kept rows of the review form as (name, quantity, category)."""
    try:
        count = min(int(form.get("count", 0)), MAX_ROWS + BLANK_ROWS)
    except (TypeError, ValueError):
        count = 0
    entries: list[tuple[str, str, str]] = []
    for index in range(count):
        if not form.get(f"keep_{index}"):
            continue
        name = clean(form.get(f"name_{index}", ""))
        if not name_key(name):
            continue
        category = form.get(f"cat_{index}", "other")
        entries.append((name, clean(form.get(f"qty_{index}", ""), 40), category if category in CATEGORIES else "other"))
    return entries


@router.post("/scan/save")
async def save_scan(request: Request, user: User = Depends(current_user), session: Session = Depends(get_session)):
    form = await request.form()
    entries = read_review_form(form)
    if not entries:
        flash(request, "error", i18n.t(user.lang, "scan.none_kept"))
        return redirect("/scan")
    if form.get("action") == "cook":
        # cook with just these, without touching the saved pantry
        lines = [f"{name} ({quantity})" if quantity else name for name, quantity, _ in entries]
        from app.routers.cook import cook_form  # imported here to avoid a circular import

        return cook_form(request, user, session, source="custom", custom="\n".join(lines))
    added = pantry.add_items(session, user, entries)
    flash(request, "ok", i18n.t(user.lang, "scan.saved", added=added, updated=len(entries) - added))
    return redirect("/")
