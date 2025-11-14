from __future__ import annotations

from http import HTTPStatus
from typing import Any, Dict, Tuple

from flask import Blueprint, Flask, current_app, jsonify, request

from .services.transformation_service import (
    TransformationError,
    TransformationRequest,
    transform,
    load_default_target,
)
from .utils.image_io import ImageDecodingError, decode_base64_image, load_image_from_file

api_bp = Blueprint("api", __name__)
_VALID_RESPONSE_FORMATS = {"json", "binary"}


class RequestValidationError(ValueError):
    """Exception type raised when incoming payloads are invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@api_bp.route("/health", methods=["GET"])
def health() -> Tuple[Any, int]:
    return jsonify({"status": "ok"}), HTTPStatus.OK


@api_bp.route("/api/transform", methods=["POST"])
def transform_endpoint() -> Any:
    try:
        payload, response_format = _deserialize_request()
        result = transform(payload)
    except RequestValidationError as exc:
        return jsonify({"error": exc.message}), HTTPStatus.BAD_REQUEST
    except ImageDecodingError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST
    except TransformationError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.UNPROCESSABLE_ENTITY
    except Exception:  # pragma: no cover - defensive logging guard
        current_app.logger.exception("Unexpected failure while processing transformation.")
        return jsonify({"error": "An unexpected error occurred."}), HTTPStatus.INTERNAL_SERVER_ERROR

    if response_format == "binary":
        extension = "gif" if result.mime_type == "image/gif" else "png"
        filename = f"obamified.{extension}"
        response = current_app.response_class(result.data, mimetype=result.mime_type)
        response.headers["Content-Disposition"] = f"inline; filename={filename}"
        response.status_code = HTTPStatus.OK
        return response

    return (
        jsonify(
            {
                "image": result.as_base64(),
                "mime_type": result.mime_type,
                "width": result.width,
                "height": result.height,
                "frame_count": result.frame_count,
            }
        ),
        HTTPStatus.OK,
    )


def register_routes(app: Flask) -> None:
    app.register_blueprint(api_bp)


def _deserialize_request() -> Tuple[TransformationRequest, str]:
    config = current_app.config

    if request.is_json:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise RequestValidationError("Request body must be a JSON object.")
        return _deserialize_from_mapping(data, config)

    if request.files:
        data = {**request.form}
        data.update({key: request.files[key] for key in request.files})
        return _deserialize_from_multipart(data, config)

    raise RequestValidationError("Unsupported payload type. Use JSON or multipart/form-data.")


def _deserialize_from_mapping(data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[TransformationRequest, str]:
    source_payload = data.get("source_image")
    if not source_payload:
        raise RequestValidationError("source_image is required.")

    try:
        source = decode_base64_image(str(source_payload))
    except ImageDecodingError as exc:
        raise RequestValidationError(str(exc)) from exc

    target_image = data.get("target_image")
    if target_image:
        try:
            target = decode_base64_image(str(target_image))
        except ImageDecodingError as exc:
            raise RequestValidationError(str(exc)) from exc
    else:
        target = load_default_target(config["DEFAULT_TARGET_IMAGE"])

    blend_ratio = _parse_float(
        data.get("blend_ratio", data.get("proximity_importance")),
        default=config["DEFAULT_BLEND_RATIO"],
        lower=0.0,
        upper=1.0,
    )
    make_gif = _parse_bool(data.get("make_gif"), default=False)
    gif_frame_count = _parse_int(
        data.get("gif_frame_count", data.get("frame_count")),
        default=config["DEFAULT_GIF_FRAME_COUNT"],
        lower=2,
        upper=120,
    )
    gif_duration = _parse_int(
        data.get("gif_duration", data.get("frame_duration")),
        default=config["DEFAULT_GIF_DURATION"],
        lower=20,
        upper=5000,
    )
    max_dimension = _parse_int(
        data.get("max_dimension", data.get("size")),
        default=config["DEFAULT_MAX_IMAGE_DIMENSION"],
        lower=64,
        upper=4096,
    )
    response_format = _parse_response_format(
        data.get("response_format", config["DEFAULT_RESPONSE_FORMAT"])
    )

    payload = TransformationRequest(
        source=source,
        target=target,
        blend_ratio=blend_ratio,
        make_gif=make_gif,
        gif_frame_count=gif_frame_count,
        gif_duration=gif_duration,
        max_dimension=max_dimension,
    )

    return payload, response_format


def _deserialize_from_multipart(data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[TransformationRequest, str]:
    source_field = data.get("source_image")
    if source_field is None:
        raise RequestValidationError("source_image is required.")

    if isinstance(source_field, (str, bytes)):
        raw_source = source_field if isinstance(source_field, str) else source_field.decode("utf-8", errors="ignore")
        try:
            source = decode_base64_image(raw_source)
        except ImageDecodingError as exc:
            raise RequestValidationError(str(exc)) from exc
    else:
        source = load_image_from_file(source_field)

    target_field = data.get("target_image")
    if hasattr(target_field, "stream"):
        target = load_image_from_file(target_field)
    elif isinstance(target_field, bytes):
        raw_target = target_field.decode("utf-8", errors="ignore")
        try:
            target = decode_base64_image(raw_target)
        except ImageDecodingError as exc:
            raise RequestValidationError(str(exc)) from exc
    elif isinstance(target_field, str) and target_field.strip():
        try:
            target = decode_base64_image(target_field)
        except ImageDecodingError as exc:
            raise RequestValidationError(str(exc)) from exc
    else:
        target = load_default_target(config["DEFAULT_TARGET_IMAGE"])

    blend_ratio = _parse_float(
        data.get("blend_ratio", data.get("proximity_importance")),
        default=config["DEFAULT_BLEND_RATIO"],
        lower=0.0,
        upper=1.0,
    )
    make_gif = _parse_bool(data.get("make_gif"), default=False)
    gif_frame_count = _parse_int(
        data.get("gif_frame_count", data.get("frame_count")),
        default=config["DEFAULT_GIF_FRAME_COUNT"],
        lower=2,
        upper=120,
    )
    gif_duration = _parse_int(
        data.get("gif_duration", data.get("frame_duration")),
        default=config["DEFAULT_GIF_DURATION"],
        lower=20,
        upper=5000,
    )
    max_dimension = _parse_int(
        data.get("max_dimension", data.get("size")),
        default=config["DEFAULT_MAX_IMAGE_DIMENSION"],
        lower=64,
        upper=4096,
    )
    response_format = _parse_response_format(
        data.get("response_format", config["DEFAULT_RESPONSE_FORMAT"])
    )

    payload = TransformationRequest(
        source=source,
        target=target,
        blend_ratio=blend_ratio,
        make_gif=make_gif,
        gif_frame_count=gif_frame_count,
        gif_duration=gif_duration,
        max_dimension=max_dimension,
    )

    return payload, response_format


def _parse_response_format(value: Any) -> str:
    if not value:
        return "json"
    candidate = str(value).strip().lower()
    if candidate not in _VALID_RESPONSE_FORMATS:
        raise RequestValidationError(
            f"response_format must be one of {sorted(_VALID_RESPONSE_FORMATS)}"
        )
    return candidate


def _parse_bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise RequestValidationError("Boolean values must be true/false or 1/0.")


def _parse_float(value: Any, *, default: float, lower: float, upper: float) -> float:
    if value is None:
        candidate = default
    else:
        try:
            candidate = float(value)
        except (TypeError, ValueError):
            raise RequestValidationError("Expected a numeric value.") from None
    if not lower <= candidate <= upper:
        raise RequestValidationError(f"Value must be between {lower} and {upper} (inclusive).")
    return candidate


def _parse_int(value: Any, *, default: int, lower: int, upper: int) -> int:
    if value is None:
        candidate = default
    else:
        try:
            candidate = int(value)
        except (TypeError, ValueError):
            raise RequestValidationError("Expected an integer value.") from None
    if not lower <= candidate <= upper:
        raise RequestValidationError(f"Value must be between {lower} and {upper} (inclusive).")
    return candidate
