"""Application factory. Run with: uvicorn app.main:create_app --factory"""

import logging
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.ai import get_ai, reset_ai
from app.auth import NotAuthenticated, current_user
from app.config import get_settings
from app.db import get_engine, init_engine
from app.routers import auth as auth_routes
from app.routers import cook, kitchen, profile, recipes, scan
from app.web import BASE_DIR, redirect, render

SESSION_DAYS = 30
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; img-src 'self' data: blob:; style-src 'self'; script-src 'self'; "
    "font-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
)


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    init_engine(settings.db_url)
    reset_ai()
    if get_ai().is_mock:
        logging.getLogger("whatscooking").warning(
            "No AI key set (or AI_MOCK=1): running in demo mode with sample answers."
        )

    app = FastAPI(title=settings.app_name, docs_url=None, redoc_url=None, openapi_url=None)
    max_body = (settings.max_photos * settings.max_upload_mb + 1) * 1024 * 1024

    @app.middleware("http")
    async def guard(request: Request, call_next):
        if request.method not in SAFE_METHODS:
            # Refuse form posts that come from another site.
            origin = request.headers.get("origin")
            if origin and origin != "null":
                allowed = {request.headers.get("host", ""), request.headers.get("x-forwarded-host", "")}
                if urlsplit(origin).netloc not in allowed:
                    return PlainTextResponse("Cross-site request blocked.", status_code=403)
            elif origin == "null":
                return PlainTextResponse("Cross-site request blocked.", status_code=403)
            length = request.headers.get("content-length", "")
            if length.isdigit() and int(length) > max_body:
                return PlainTextResponse("Upload too large.", status_code=413)
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        if not request.url.path.startswith("/static/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    # Added last so it wraps the guard above and every route can use request.session.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.resolve_secret_key(),
        session_cookie="wc_session",
        max_age=SESSION_DAYS * 24 * 60 * 60,
        same_site="lax",
        https_only=settings.cookie_secure,
    )

    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    for module in (auth_routes, kitchen, scan, cook, recipes, profile):
        app.include_router(module.router)

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"status": "ok"}

    @app.exception_handler(NotAuthenticated)
    async def _needs_login(request: Request, _exc: NotAuthenticated):
        return redirect("/login")

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException):
        if exc.status_code != 404:
            return PlainTextResponse(str(exc.detail), status_code=exc.status_code)
        user = None
        try:
            from sqlmodel import Session

            with Session(get_engine()) as session:
                user = current_user(request, session)
        except NotAuthenticated:
            pass
        return render(request, "not_found.html", user=user, status_code=404)

    return app
