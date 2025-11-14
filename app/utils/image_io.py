from __future__ import annotations

import base64
import binascii
import re
from io import BytesIO

from PIL import Image, ImageFile
from werkzeug.datastructures import FileStorage

ImageFile.LOAD_TRUNCATED_IMAGES = True

_DATA_URL_RE = re.compile(r"^data:(?P<mime>[^;]+);base64,(?P<data>.+)$", re.IGNORECASE)


class ImageDecodingError(ValueError):
    """Raised when raw image input cannot be decoded into a Pillow image."""


def decode_base64_image(encoded: str) -> Image.Image:
    if not encoded:
        raise ImageDecodingError("No base64 encoded image data was provided.")

    payload = encoded.strip()
    match = _DATA_URL_RE.match(payload)
    if match:
        payload = match.group("data")

    try:
        binary = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:  # pragma: no cover - defensive
        raise ImageDecodingError("The provided string is not valid base64 image data.") from exc

    return _load_image_from_bytes(binary)


def load_image_from_file(file: FileStorage) -> Image.Image:
    if file is None:
        raise ImageDecodingError("No uploaded image file was provided.")

    try:
        file.stream.seek(0)
        image = Image.open(file.stream)
        image.load()
    except (OSError, ValueError) as exc:
        raise ImageDecodingError("Unable to read the uploaded image file.") from exc

    return image


def _load_image_from_bytes(binary: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(binary))
        image.load()
    except (OSError, ValueError) as exc:
        raise ImageDecodingError("Unable to decode the provided image bytes.") from exc
    return image
