"""Test setup: a fresh database per test and the demo AI (no network)."""

import io

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("AI_MOCK", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("AI_BASE_URL", "")
    monkeypatch.setenv("AI_API_KEY", "")
    monkeypatch.setenv("COOKIE_SECURE", "0")

    from app import auth
    from app.config import get_settings

    get_settings.cache_clear()
    auth._failures.clear()

    from app.main import create_app

    application = create_app()
    yield application
    get_settings.cache_clear()


def make_user(username: str, password: str = "correct horse", **fields):
    from app import auth
    from app.db import get_engine
    from app.models import User

    with Session(get_engine()) as session:
        user = User(username=username, password_hash=auth.hash_password(password), **fields)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def login(app, username: str, password: str = "correct horse") -> TestClient:
    client = TestClient(app)
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    assert response.url.path == "/"
    return client


@pytest.fixture
def mei(app) -> TestClient:
    make_user("mei")
    return login(app, "mei")


@pytest.fixture
def ali(app) -> TestClient:
    make_user("ali")
    return login(app, "ali")


@pytest.fixture
def photo() -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (640, 480), (40, 140, 90)).save(buffer, "JPEG")
    return buffer.getvalue()
