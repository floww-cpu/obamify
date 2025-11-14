#!/usr/bin/env python3
"""Simple test without external dependencies."""

import sys
import os
sys.path.insert(0, '.')

def test_imports():
    """Test that all our modules can be imported."""
    try:
        from app.utils.temp_file_manager import TempFileManager
        print("✅ TempFileManager imported successfully")
        
        from app import create_app
        print("✅ Flask app created successfully")
        
        app = create_app()
        with app.app_context():
            # Test that the configuration is set correctly
            assert "TEMP_IMAGE_DIR" in app.config
            assert "TEMP_IMAGE_URL_BASE" in app.config
            assert "TEMP_IMAGE_EXPIRY_HOURS" in app.config
            print("✅ Configuration is correct")
            
            # Test that temp directory exists
            temp_dir = app.config["TEMP_IMAGE_DIR"]
            assert os.path.exists(temp_dir), f"Temp directory {temp_dir} does not exist"
            print(f"✅ Temp directory exists: {temp_dir}")
            
            # Test TempFileManager functionality
            test_data = b"test image data"
            filename = TempFileManager.save_temp_image(test_data, "image/png")
            print(f"✅ Saved temp image: {filename}")
            
            # Test URL generation
            url = TempFileManager.get_temp_image_url(filename)
            print(f"✅ Generated URL: {url}")
            
            # Test file path retrieval
            filepath = TempFileManager.get_temp_image_path(filename)
            assert filepath is not None
            assert filepath.exists()
            print(f"✅ File path works: {filepath}")
            
            # Test cleanup
            deleted_count = TempFileManager.cleanup_expired_files()
            print(f"✅ Cleanup completed, deleted {deleted_count} files")
            
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)