from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Optional

from flask import current_app


class TempFileManager:
    """Manages temporary image files with automatic cleanup."""
    
    @staticmethod
    def save_temp_image(image_data: bytes, mime_type: str) -> str:
        """Save image data temporarily and return the filename."""
        temp_dir = Path(current_app.config["TEMP_IMAGE_DIR"])
        
        # Generate unique filename with appropriate extension
        extension = "gif" if mime_type == "image/gif" else "png"
        filename = f"{uuid.uuid4().hex}.{int(time.time())}.{extension}"
        filepath = temp_dir / filename
        
        # Write the file
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        return filename
    
    @staticmethod
    def get_temp_image_path(filename: str) -> Optional[Path]:
        """Get the full path to a temporary image file."""
        temp_dir = Path(current_app.config["TEMP_IMAGE_DIR"])
        filepath = temp_dir / filename
        
        if filepath.exists():
            return filepath
        return None
    
    @staticmethod
    def get_temp_image_url(filename: str) -> str:
        """Generate the URL for a temporary image."""
        base_url = current_app.config["TEMP_IMAGE_URL_BASE"].rstrip("/")
        return f"{base_url}/api/temp/{filename}"
    
    @staticmethod
    def cleanup_expired_files() -> int:
        """Remove files older than the configured expiry time and return count of deleted files."""
        temp_dir = Path(current_app.config["TEMP_IMAGE_DIR"])
        expiry_hours = current_app.config["TEMP_IMAGE_EXPIRY_HOURS"]
        expiry_seconds = expiry_hours * 3600
        current_time = time.time()
        
        deleted_count = 0
        
        if not temp_dir.exists():
            return 0
        
        for filepath in temp_dir.iterdir():
            if filepath.is_file():
                # Extract timestamp from filename (format: uuid.timestamp.extension)
                try:
                    parts = filepath.name.split('.')
                    if len(parts) >= 3:
                        timestamp = int(parts[-2])
                        if current_time - timestamp > expiry_seconds:
                            filepath.unlink()
                            deleted_count += 1
                except (ValueError, IndexError):
                    # If we can't parse the timestamp, skip the file
                    continue
        
        return deleted_count
    
    @staticmethod
    def is_file_expired(filename: str) -> bool:
        """Check if a temporary file has expired."""
        try:
            parts = filename.split('.')
            if len(parts) >= 3:
                timestamp = int(parts[-2])
                expiry_hours = current_app.config["TEMP_IMAGE_EXPIRY_HOURS"]
                expiry_seconds = expiry_hours * 3600
                return time.time() - timestamp > expiry_seconds
        except (ValueError, IndexError):
            return True  # Treat unparseable filenames as expired
        
        return False