from __future__ import annotations

import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from .routes import register_routes


def create_app() -> Flask:
    """Application factory."""

    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # Allow all origins for development
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True
        }
    })

    project_root = Path(__file__).resolve().parent.parent
    temp_dir = project_root / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    app.config.update(
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=12 * 1024 * 1024,  # 12 MB uploads
        DEFAULT_MAX_IMAGE_DIMENSION=1024,
        DEFAULT_BLEND_RATIO=0.65,
        DEFAULT_GIF_FRAME_COUNT=12,
        DEFAULT_GIF_DURATION=80,
        DEFAULT_RESPONSE_FORMAT="json",
        DEFAULT_TARGET_IMAGE=str(project_root / "assets" / "pfp_transparent.png"),
        TEMP_IMAGE_DIR=str(temp_dir),
        TEMP_IMAGE_URL_BASE=os.environ.get("TEMP_IMAGE_URL_BASE", "http://localhost:8000"),
        TEMP_IMAGE_EXPIRY_HOURS=48,
    )

    register_routes(app)

    return app
