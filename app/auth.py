"""Passwords, sign-in and the "who is logged in" dependency."""

import re
import time

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Depends, Request
from sqlmodel import Session, select

from app.db import get_session
from app.models import User

MIN_PASSWORD_LENGTH = 8
MAX_FAILURES = 5
LOCK_SECONDS = 300
USERNAME_RE = re.compile(r"^[\w.-]{2,32}$")

_hasher = PasswordHasher()
_failures: dict[str, list[float]] = {}


class NotAuthenticated(Exception):
    """Raised when a page needs a signed-in user and there is none."""


def normalise_username(raw: str) -> str:
    return (raw or "").strip().casefold()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def _recent_failures(username: str) -> list[float]:
    cutoff = time.monotonic() - LOCK_SECONDS
    recent = [stamp for stamp in _failures.get(username, []) if stamp > cutoff]
    if recent:
        _failures[username] = recent
    else:
        _failures.pop(username, None)
    return recent


def is_locked(username: str) -> bool:
    return len(_recent_failures(username)) >= MAX_FAILURES


def record_failure(username: str) -> None:
    _failures.setdefault(username, []).append(time.monotonic())


def clear_failures(username: str) -> None:
    _failures.pop(username, None)


def authenticate(session: Session, username: str, password: str) -> User | None:
    """Return the user for a correct username and password, otherwise None."""
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None or not verify_password(user.password_hash, password):
        return None
    return user


def session_marker(user: User) -> str:
    """Changes when the password changes, which signs out older sessions."""
    return user.password_hash[-16:]


def sign_in(request: Request, user: User) -> None:
    request.session.clear()
    request.session["uid"] = user.id
    request.session["mark"] = session_marker(user)


def sign_out(request: Request) -> None:
    request.session.clear()


def current_user(request: Request, session: Session = Depends(get_session)) -> User:
    uid = request.session.get("uid")
    user = session.get(User, uid) if isinstance(uid, int) else None
    if user is None or request.session.get("mark") != session_marker(user):
        request.session.pop("uid", None)
        raise NotAuthenticated()
    return user
