"""Validate and shrink uploaded photos before they go to the AI."""

import io

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

try:  # iPhone photos chosen from the library can arrive as HEIC
    from pillow_heif import register_heif_opener

    register_heif_opener()
except Exception:  # pragma: no cover - optional dependency
    pass

MAX_EDGE = 2048  # sent to the AI
PREVIEW_EDGE = 900  # shown on the review screen
INK = (22, 22, 22)
RED = (200, 30, 40)
WHITE = (255, 255, 255)
Image.MAX_IMAGE_PIXELS = 60_000_000


class ImageRejected(Exception):
    """The upload is not a photo we can read."""


def prepare_image(raw: bytes) -> bytes:
    """Return a re-encoded JPEG no larger than MAX_EDGE on its long side.

    Re-encoding also drops EXIF data such as GPS location.
    """
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            image.thumbnail((MAX_EDGE, MAX_EDGE))
            out = io.BytesIO()
            image.save(out, "JPEG", quality=90, optimize=True)
            return out.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ImageRejected(str(exc)) from exc


def annotate(prepared: bytes, marks: list[tuple[int, tuple[int, int, int, int], bool]]) -> bytes:
    """A smaller copy of a photo with a numbered box around each ingredient found.

    marks holds (number, (ymin, xmin, ymax, xmax) on a 0-1000 scale, unsure).
    Unsure items are boxed in red, the rest in black.
    """
    with Image.open(io.BytesIO(prepared)) as image:
        image = image.convert("RGB")
        image.thumbnail((PREVIEW_EDGE, PREVIEW_EDGE))
        width, height = image.size
        draw = ImageDraw.Draw(image)
        line = max(3, width // 220)
        font = ImageFont.load_default(size=max(24, width // 18))
        for number, (ymin, xmin, ymax, xmax), unsure in marks:
            colour = RED if unsure else INK
            left, top = xmin * width / 1000, ymin * height / 1000
            right, bottom = xmax * width / 1000, ymax * height / 1000
            draw.rectangle((left, top, right, bottom), outline=colour, width=line)
            label = str(number)
            ink_left, ink_top, ink_right, ink_bottom = draw.textbbox((0, 0), label, font=font)
            pad = line + 2
            tag_width, tag_height = ink_right - ink_left + 2 * pad, ink_bottom - ink_top + 2 * pad
            x = min(max(left, 0), width - tag_width)
            y = min(max(top, 0), height - tag_height)
            draw.rectangle((x, y, x + tag_width, y + tag_height), fill=colour)
            draw.text((x + pad - ink_left, y + pad - ink_top), label, fill=WHITE, font=font)
        out = io.BytesIO()
        image.save(out, "JPEG", quality=78)
        return out.getvalue()
