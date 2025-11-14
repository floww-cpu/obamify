#!/usr/bin/env python3
"""Manual test of the temp file functionality."""

import base64
import sys
import os
sys.path.insert(0, '.')

def test_temp_file_manager():
    """Test TempFileManager functionality directly."""
    print("Testing TempFileManager...")
    
    # Create a mock Flask app context
    from flask import Flask
    app = Flask(__name__)
    
    # Set up the configuration
    project_root = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(project_root, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    app.config.update({
        "TEMP_IMAGE_DIR": temp_dir,
        "TEMP_IMAGE_URL_BASE": "http://localhost:8000",
        "TEMP_IMAGE_EXPIRY_HOURS": 48,
    })
    
    with app.app_context():
        try:
            from app.utils.temp_file_manager import TempFileManager
            
            # Test data - a simple 1x1 PNG
            test_png_data = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            )
            
            # Test saving temp image
            filename = TempFileManager.save_temp_image(test_png_data, "image/png")
            print(f"✅ Saved temp image: {filename}")
            
            # Test URL generation
            url = TempFileManager.get_temp_image_url(filename)
            print(f"✅ Generated URL: {url}")
            
            # Test file path retrieval
            filepath = TempFileManager.get_temp_image_path(filename)
            if filepath and filepath.exists():
                print(f"✅ File path works: {filepath}")
                print(f"   File size: {filepath.stat().st_size} bytes")
            else:
                print("❌ File path test failed")
                return False
            
            # Test expiry check (should not be expired)
            is_expired = TempFileManager.is_file_expired(filename)
            if not is_expired:
                print("✅ File expiry check works (not expired)")
            else:
                print("❌ File expiry check failed (should not be expired)")
                return False
            
            # Test cleanup (should not delete the fresh file)
            deleted_count = TempFileManager.cleanup_expired_files()
            print(f"✅ Cleanup completed, deleted {deleted_count} files")
            
            # Verify file still exists after cleanup
            filepath_after = TempFileManager.get_temp_image_path(filename)
            if filepath_after and filepath_after.exists():
                print("✅ File still exists after cleanup")
            else:
                print("❌ File was incorrectly deleted")
                return False
            
            print("\n🎉 All TempFileManager tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_temp_file_manager()
    sys.exit(0 if success else 1)