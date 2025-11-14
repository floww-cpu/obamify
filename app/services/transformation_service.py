from __future__ import annotations

import base64
import math
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Optional

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# Pillow safety guard to avoid decompression bombs on massive inputs.
Image.MAX_IMAGE_PIXELS = 20_000_000

try:  # Pillow>=9.1 provides the Resampling namespace.
    _RESAMPLING = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover - compatibility with older Pillow
    _RESAMPLING = Image.LANCZOS  # type: ignore[attr-defined]


class TransformationError(Exception):
    """Domain error raised when the transformation cannot be performed."""


@dataclass
class TransformationRequest:
    source: Image.Image
    target: Image.Image
    blend_ratio: float
    make_gif: bool
    gif_frame_count: int
    gif_duration: int
    max_dimension: Optional[int]


@dataclass
class TransformationResult:
    data: bytes
    mime_type: str
    width: int
    height: int
    frame_count: int

    def as_base64(self) -> str:
        return base64.b64encode(self.data).decode("ascii")


def load_default_target(path: str) -> Image.Image:
    default_path = Path(path)
    if not default_path.exists():
        raise TransformationError(
            f"Default target image was not found at '{default_path}'."
        )
    with default_path.open("rb") as handle:
        image = Image.open(handle)
        image.load()
    return ImageOps.exif_transpose(image).convert("RGBA")


def transform(payload: TransformationRequest) -> TransformationResult:
    source = _prepare_image(payload.source, payload.max_dimension)
    target = _prepare_image(payload.target, payload.max_dimension)

    # Ensure the two images have identical dimensions before blending.
    if target.size != source.size:
        target = target.resize(source.size, _RESAMPLING)

    blend_ratio = _clamp(payload.blend_ratio, 0.0, 1.0)

    if payload.make_gif:
        frames = _render_animation_frames(source, target, blend_ratio, payload.gif_frame_count)
        if not frames:
            raise TransformationError("Unable to create GIF frames from the provided images.")

        buffer = BytesIO()
        first, rest = frames[0], frames[1:]
        first.save(
            buffer,
            format="GIF",
            save_all=True,
            append_images=rest,
            loop=0,
            duration=max(20, payload.gif_duration),
            disposal=2,
        )
        data = buffer.getvalue()
        width, height = frames[0].size
        return TransformationResult(
            data=data,
            mime_type="image/gif",
            width=width,
            height=height,
            frame_count=len(frames),
        )

    final_image = _blend_frame(source, target, blend_ratio)
    buffer = BytesIO()
    final_image.save(buffer, format="PNG")
    data = buffer.getvalue()
    width, height = final_image.size
    return TransformationResult(
        data=data,
        mime_type="image/png",
        width=width,
        height=height,
        frame_count=1,
    )


def _prepare_image(image: Image.Image, max_dimension: Optional[int]) -> Image.Image:
    processed = ImageOps.exif_transpose(image).convert("RGBA")
    if max_dimension:
        width, height = processed.size
        longest_side = max(width, height)
        if longest_side > max_dimension:
            scale = max_dimension / float(longest_side)
            new_size = (
                max(1, int(round(width * scale))),
                max(1, int(round(height * scale))),
            )
            processed = processed.resize(new_size, _RESAMPLING)
    return processed


def _render_animation_frames(
    source: Image.Image,
    target: Image.Image,
    blend_ratio: float,
    frame_count: int,
) -> List[Image.Image]:
    count = max(2, frame_count)
    mixes = _animation_mix_values(blend_ratio, count)
    return [_blend_frame(source, target, mix) for mix in mixes]


def _blend_frame(source: Image.Image, target: Image.Image, mix: float) -> Image.Image:
    mix = _clamp(mix, 0.0, 1.0)
    # Primary blend between the source and the target.
    blended = Image.blend(source, target, mix)

    # Enhance definition so the result retains recognisable details.
    detail = ImageEnhance.Contrast(blended).enhance(1 + mix * 0.35)
    colorised = ImageEnhance.Color(detail).enhance(1 + mix * 0.25)

    if mix > 0:
        # Reintroduce a hint of the original source to keep eyes and facial
        # features readable while still leaning into the target colours.
        mask_strength = min(0.4, mix * 0.4)
        softened = source.filter(ImageFilter.GaussianBlur(radius=1.5))
        colorised = Image.blend(colorised, softened, mask_strength)

    return colorised.convert("RGB")


def _animation_mix_values(blend_ratio: float, frame_count: int) -> Iterable[float]:
    if frame_count <= 1:
        yield _clamp(blend_ratio, 0.0, 1.0)
        return

    for index in range(frame_count):
        phase = index / float(frame_count - 1)
        # Sinusoidal easing so the animation loops smoothly.
        yield _clamp(blend_ratio, 0.0, 1.0) * math.sin(math.pi * phase) ** 2


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
