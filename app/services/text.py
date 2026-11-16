"""Small text helpers for ingredient names."""

import re
import unicodedata

_NOT_WORD = re.compile(r"[^\w\s]+")


def clean(raw: object, limit: int = 60) -> str:
    """Collapse whitespace, trim and cap the length of user or AI text."""
    text = " ".join(str(raw or "").split())
    return text[:limit].strip()


def _singular(word: str) -> str:
    if len(word) <= 3 or not word.isascii():
        return word
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("oes"):
        return word[:-2]
    if word.endswith(("ss", "us", "is")):
        return word
    if word.endswith("s"):
        return word[:-1]
    return word


def name_key(name: str) -> str:
    """Key used to spot the same ingredient written slightly differently.

    "Tomatoes", "tomato " and "TOMATO" all map to "tomato".
    """
    text = unicodedata.normalize("NFKC", name).casefold()
    text = _NOT_WORD.sub(" ", text)
    return " ".join(_singular(word) for word in text.split())


def split_list(raw: str, limit: int = 30) -> list[str]:
    """Split a comma / newline separated field into clean, unique entries."""
    seen: set[str] = set()
    out: list[str] = []
    for part in re.split(r"[,，、;；\n]+", raw or ""):
        item = clean(part, 40)
        key = item.casefold()
        if item and key not in seen:
            seen.add(key)
            out.append(item)
        if len(out) >= limit:
            break
    return out
