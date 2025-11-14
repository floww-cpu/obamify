from __future__ import annotations

import base64
from io import BytesIO

from PIL import Image

from app import create_app


def _encode_image(color: str = "#3478f6") -> str:
    image = Image.new("RGB", (48, 48), color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def test_health_endpoint_returns_ok() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/health")
    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {"status": "ok"}


def test_transform_endpoint_json_response() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/transform",
        json={
            "source_image": _encode_image("#ff6600"),
            "blend_ratio": 0.4,
            "max_dimension": 96,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload is not None
    assert payload["mime_type"] == "image/png"
    assert payload["frame_count"] == 1
    assert payload["width"] == payload["height"] == 96
    assert payload["image"]


def test_transform_endpoint_binary_gif_response() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/transform",
        json={
            "source_image": _encode_image("#222831"),
            "make_gif": True,
            "gif_frame_count": 4,
            "response_format": "binary",
        },
    )

    assert response.status_code == 200
    assert response.mimetype == "image/gif"
    assert response.data.startswith(b"GIF")
    assert response.headers["Content-Disposition"].startswith("inline; filename=")


def test_transform_endpoint_rejects_missing_payload() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post("/api/transform", json={})
    assert response.status_code == 400
    assert response.is_json
    assert "source_image" in response.get_json()["error"]
