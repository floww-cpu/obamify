# Obamify Flask API

A lightweight Flask service that turns any input image into an "obamified" version
by blending it with a target portrait. The API can return either a single PNG
frame or an animated GIF that loops smoothly through the transformation.

## Features

- REST API built with Flask.
- Accepts JSON payloads (base64-encoded images) or `multipart/form-data` uploads.
- Optional secondary target image; falls back to `assets/pfp_transparent.png`.
- Tunable blend strength, output size and GIF animation parameters.
- Responses can be returned either as base64-encoded JSON payloads or as raw
  binary image data.

## Getting started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Running the development server

```bash
# Option A: using flask CLI
env FLASK_APP=wsgi.py flask run --host=0.0.0.0 --port=8000

# Option B: directly through Python
python wsgi.py
```

The service exposes two endpoints:

| Method | Path             | Description                        |
|--------|------------------|------------------------------------|
| GET    | `/health`        | Simple health check returning OK. |
| POST   | `/api/transform` | Perform the image transformation. |

## API reference

### `POST /api/transform`

The endpoint accepts parameters via JSON or `multipart/form-data`.

#### JSON payload example

```json
{
  "source_image": "<base64 encoded source>",
  "target_image": "<optional base64 target>",
  "blend_ratio": 0.65,
  "max_dimension": 1024,
  "make_gif": true,
  "gif_frame_count": 16,
  "gif_duration": 90,
  "response_format": "json"
}
```

- `source_image` (required): base64 string representing the source image.
- `target_image` (optional): base64 string for a custom target image. If omitted
  the default face in `assets/pfp_transparent.png` is used.
- `blend_ratio` (optional, 0.0-1.0, default `0.65`): how strongly the target
  image influences the final result.
- `max_dimension` (optional, default `1024`): the maximum width/height in pixels.
  Larger images are downscaled while preserving aspect ratio.
- `make_gif` (optional, default `false`): whether to generate an animated GIF.
- `gif_frame_count` (optional, default `12`): number of frames when creating a
  GIF. Must be between 2 and 120.
- `gif_duration` (optional, default `80`): frame duration in milliseconds.
- `response_format` (optional, `json` or `binary`, default `json`): whether to
  return a JSON response containing a base64 encoded image or a direct binary
  response suitable for a browser download.

#### Multipart form example

```bash
curl -X POST http://localhost:8000/api/transform \
  -F "source_image=@/path/to/source.png" \
  -F "make_gif=true" \
  -F "response_format=binary" \
  --output obamified.gif
```

When posting form data you may either upload `target_image` as another file or
provide a base64 encoded string in a regular text field.

#### Successful JSON response

```json
{
  "image": "<base64 output>",
  "mime_type": "image/png",
  "width": 512,
  "height": 512,
  "frame_count": 1
}
```

If `response_format=binary` the API streams the generated file directly with the
appropriate `Content-Type` header (`image/png` or `image/gif`).

#### Error handling

Invalid inputs yield a 400 response with an `error` message describing the
problem. Transformation errors (for example, corrupted images) return a 422
status code.

## Project layout

```
app/
  __init__.py              # Flask application factory
  routes.py                # HTTP endpoints & validation
  services/
    transformation_service.py  # Image blending & GIF generation logic
  utils/
    image_io.py            # Safe image decoding helpers
assets/
  pfp_transparent.png      # Default target portrait
requirements.txt           # Runtime dependencies
wsgi.py                    # Application entry-point
```

## Development

Install the development dependencies and run the unit test suite with:

```bash
pip install -r requirements-dev.txt
pytest
```

## Contributing

Issues and pull requests are welcome. Please ensure new contributions include
reproducible steps and clearly document any new parameters or behaviours.
