#!/usr/bin/env python3
"""Build the static site that documents the Python API."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SITE = ROOT / "site"
ASSETS = ROOT / "assets"


def copy_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Source path '{source}' does not exist.")
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def build() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # Copy the static site description (HTML/CSS/manifest/service worker).
    for item in SITE.iterdir():
        target = DIST / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    # Publish public assets (icons and the default portrait) under dist/assets.
    copy_tree(ASSETS, DIST / "assets")


if __name__ == "__main__":
    build()
