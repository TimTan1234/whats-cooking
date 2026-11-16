"""Turn the AI's per-photo answers into one numbered list for the review screen."""

from dataclasses import dataclass, field

from app.services.text import clean, name_key

Box = tuple[int, int, int, int]  # ymin, xmin, ymax, xmax on a 0-1000 scale

MAX_FOUND = 120
_RANK = {"low": 0, "medium": 1, "high": 2}


@dataclass
class Found:
    number: int
    name: str
    quantity: str
    category: str
    confidence: str
    evidence: str
    boxes: list[tuple[int, Box]] = field(default_factory=list)  # (photo index, box)


def clean_box(raw: object) -> Box | None:
    """A usable box, or None when the AI gave something that is not one."""
    try:
        ymin, xmin, ymax, xmax = (min(max(int(value), 0), 1000) for value in raw)  # type: ignore[union-attr]
    except (TypeError, ValueError):
        return None
    if ymax - ymin < 5 or xmax - xmin < 5:
        return None
    return ymin, xmin, ymax, xmax


def merge(per_photo: list[list]) -> list[Found]:
    """Combine the ingredients found in each photo into one numbered list.

    The same ingredient seen in several photos becomes one entry that keeps
    every box, the first amount given and the highest confidence.
    """
    by_key: dict[str, Found] = {}
    for photo, ingredients in enumerate(per_photo):
        for item in ingredients:
            name = clean(item.name)
            key = name_key(name)
            if not key:
                continue
            found = by_key.get(key)
            if found is None:
                if len(by_key) >= MAX_FOUND:
                    continue
                found = Found(
                    number=len(by_key) + 1, name=name, quantity=clean(item.quantity, 40),
                    category=item.category, confidence=item.confidence, evidence=clean(item.evidence, 120),
                )
                by_key[key] = found
            else:
                if not found.quantity:
                    found.quantity = clean(item.quantity, 40)
                if _RANK.get(item.confidence, 0) > _RANK.get(found.confidence, 0):
                    found.confidence = item.confidence
                    found.evidence = clean(item.evidence, 120)
            box = clean_box(item.box_2d)
            if box is not None:
                found.boxes.append((photo, box))
    return list(by_key.values())
