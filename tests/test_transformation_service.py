from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image, ImageStat

from app.services.transformation_service import (
    TransformationRequest,
    TransformationResult,
    transform,
)


def _solid_image(color: str, size: int = 64) -> Image.Image:
    image = Image.new("RGBA", (size, size), color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    loaded = Image.open(buffer)
    loaded.load()
    return loaded


def test_transform_returns_png() -> None:
    request = TransformationRequest(
        source=_solid_image("#336699"),
        target=_solid_image("#ffcc00"),
        blend_ratio=0.5,
        make_gif=False,
        gif_frame_count=8,
        gif_duration=80,
        max_dimension=None,
    )

    result = transform(request)
    assert isinstance(result, TransformationResult)
    assert result.mime_type == "image/png"
    assert result.frame_count == 1
    assert result.width == 64 and result.height == 64
    assert len(result.data) > 0
    base64_payload = result.as_base64()
    assert isinstance(base64_payload, str)
    assert base64_payload


def test_transform_generates_gif_with_scaling() -> None:
    request = TransformationRequest(
        source=_solid_image("#112233", size=256),
        target=_solid_image("#ddeeff", size=128),
        blend_ratio=0.75,
        make_gif=True,
        gif_frame_count=6,
        gif_duration=90,
        max_dimension=128,
    )

    result = transform(request)
    assert result.mime_type == "image/gif"
    assert result.frame_count == 6
    assert result.width == 128 and result.height == 128
    assert len(result.data) > 0


def test_blend_ratio_progressively_lightens_result() -> None:
    ratios = [-0.1, 0.0, 0.5, 1.5]
    means = []

    for ratio in ratios:
        request = TransformationRequest(
            source=_solid_image("#000000"),
            target=_solid_image("#ffffff"),
            blend_ratio=ratio,
            make_gif=False,
            gif_frame_count=4,
            gif_duration=80,
            max_dimension=None,
        )
        result = transform(request)
        image = Image.open(BytesIO(result.data)).convert("L")
        means.append(ImageStat.Stat(image).mean[0])

    assert means[0] == pytest.approx(means[1])
    assert means[1] < means[2] < means[3]
