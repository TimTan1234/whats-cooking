"""Account administration. There is no public sign-up; accounts are made here.

    python -m app.cli create-user mei
    python -m app.cli reset-password mei
    python -m app.cli list-users
    python -m app.cli delete-user mei

And one command for judging photo analysis on your own photos:

    python -m app.cli scan-test fridge.jpg shelf.jpg --model gemini-4-carbon
"""

import argparse
import asyncio
import getpass
import sys
import time
from pathlib import Path

from sqlmodel import Session, select

from app import auth
from app.config import get_settings
from app.db import init_engine
from app.models import CookLog, IdeaSet, PantryItem, Recipe, User


def _read_password(from_stdin: bool) -> str:
    if from_stdin:
        password = sys.stdin.readline().rstrip("\n")
    else:
        password = getpass.getpass("Password: ")
        if getpass.getpass("Repeat password: ") != password:
            raise SystemExit("The two passwords do not match.")
    if len(password) < auth.MIN_PASSWORD_LENGTH:
        raise SystemExit(f"Password must be at least {auth.MIN_PASSWORD_LENGTH} characters.")
    return password


def _find(session: Session, username: str) -> User:
    user = session.exec(select(User).where(User.username == auth.normalise_username(username))).first()
    if user is None:
        raise SystemExit(f"No user called '{username}'.")
    return user


def scan_test(paths: list[str], lang: str, model: str, thinking: str) -> None:
    """Print what the AI finds in the given photos, without touching any account."""
    from app.ai import get_ai, reset_ai
    from app.routers.scan import find_ingredients
    from app.services.images import ImageRejected, prepare_image

    settings = get_settings()
    if model:
        settings.gemini_vision_model = model
    if thinking:
        settings.gemini_vision_thinking = thinking
    reset_ai()
    if get_ai().is_mock:
        print("Demo mode (no GEMINI_API_KEY): the result below is sample data, not a reading of your photos.")
    else:
        print(f"Model: {settings.gemini_vision_model or settings.gemini_model}"
              f"   thinking: {settings.gemini_vision_thinking or 'model default'}")

    try:
        images = [prepare_image(Path(path).read_bytes()) for path in paths]
    except (OSError, ImageRejected) as exc:
        raise SystemExit(f"Could not read a photo: {exc}")
    started = time.monotonic()
    found = asyncio.run(find_ingredients(images, lang))
    print(f"{len(found)} ingredients from {len(images)} photo(s) in {time.monotonic() - started:.1f}s\n")
    for item in found:
        print(f"{item.number:>3}  {item.confidence:<6}  {item.name}"
              f"{' (' + item.quantity + ')' if item.quantity else ''}  -  {item.evidence}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Manage What's Cooking accounts.")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create-user", help="add an account")
    create.add_argument("username")
    create.add_argument("--lang", choices=["en", "zh"], default="en", help="starting language (default: en)")
    create.add_argument("--password-stdin", action="store_true", help="read the password from standard input")

    reset = commands.add_parser("reset-password", help="set a new password for an account")
    reset.add_argument("username")
    reset.add_argument("--password-stdin", action="store_true", help="read the password from standard input")

    commands.add_parser("list-users", help="show all accounts")

    delete = commands.add_parser("delete-user", help="remove an account and everything it owns")
    delete.add_argument("username")
    delete.add_argument("--yes", action="store_true", help="do not ask for confirmation")

    scan = commands.add_parser("scan-test", help="show what the AI finds in photos")
    scan.add_argument("photos", nargs="+", help="photo files")
    scan.add_argument("--lang", choices=["en", "zh"], default="en")
    scan.add_argument("--model", default="", help="try a different Gemini model for this run")
    scan.add_argument("--thinking", default="", choices=["", "low", "medium", "high"], help="thinking level for this run")

    args = parser.parse_args(argv)
    if args.command == "scan-test":
        scan_test(args.photos, args.lang, args.model, args.thinking)
        return
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    engine = init_engine(settings.db_url)

    with Session(engine) as session:
        if args.command == "create-user":
            username = auth.normalise_username(args.username)
            if not auth.USERNAME_RE.match(username):
                raise SystemExit("Username must be 2-32 characters: letters, numbers, dot, dash or underscore.")
            if session.exec(select(User).where(User.username == username)).first() is not None:
                raise SystemExit(f"User '{username}' already exists.")
            password = _read_password(args.password_stdin)
            session.add(User(username=username, password_hash=auth.hash_password(password), lang=args.lang))
            session.commit()
            print(f"Created user '{username}'.")

        elif args.command == "reset-password":
            user = _find(session, args.username)
            user.password_hash = auth.hash_password(_read_password(args.password_stdin))
            session.add(user)
            session.commit()
            print(f"Password changed for '{user.username}'. Their existing sessions are signed out.")

        elif args.command == "list-users":
            users = session.exec(select(User).order_by(User.username)).all()
            if not users:
                print("No users yet. Add one with: python -m app.cli create-user <name>")
            for user in users:
                print(f"{user.username}\t{user.lang}\tcreated {user.created_at:%Y-%m-%d}")

        elif args.command == "delete-user":
            user = _find(session, args.username)
            if not args.yes:
                answer = input(f"Delete '{user.username}' with their pantry, recipes and history? [y/N] ")
                if answer.strip().lower() != "y":
                    raise SystemExit("Nothing deleted.")
            for model in (CookLog, IdeaSet, PantryItem, Recipe):
                for row in session.exec(select(model).where(model.user_id == user.id)).all():
                    session.delete(row)
                session.flush()
            session.delete(user)
            session.commit()
            print(f"Deleted '{user.username}'.")


if __name__ == "__main__":
    main()
