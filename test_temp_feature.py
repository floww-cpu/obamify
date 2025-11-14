#!/usr/bin/env python3
"""
Simple test script to verify the temporary image feature works.
Run this with: python test_temp_feature.py
"""

import base64
import json
import requests
import time
from pathlib import Path

# Create a simple test image (1x1 pixel PNG)
test_png_data = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)

def test_temp_feature():
    """Test the temporary image hosting feature."""
    base_url = "http://localhost:8000"
    
    print("Testing temporary image feature...")
    
    # Test 1: Transform with URL response format
    print("\n1. Testing transform with response_format=url")
    
    payload = {
        "source_image": base64.b64encode(test_png_data).decode(),
        "response_format": "url",
        "make_gif": False
    }
    
    try:
        response = requests.post(f"{base_url}/api/transform", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Transform successful!")
            print(f"   URL: {result['url']}")
            print(f"   Expires in: {result['expires_in_hours']} hours")
            
            # Test 2: Access the temporary URL
            print("\n2. Testing temporary URL access")
            temp_url = result['url']
            img_response = requests.get(temp_url, timeout=10)
            
            if img_response.status_code == 200:
                print(f"✅ Temporary image accessible via URL!")
                print(f"   Content-Type: {img_response.headers.get('Content-Type')}")
                print(f"   Content-Length: {len(img_response.content)} bytes")
            else:
                print(f"❌ Failed to access temporary image: {img_response.status_code}")
                
        else:
            print(f"❌ Transform failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the Flask app is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    
    # Test 3: Test cleanup endpoint
    print("\n3. Testing cleanup endpoint")
    try:
        cleanup_response = requests.post(f"{base_url}/api/temp/cleanup", timeout=10)
        if cleanup_response.status_code == 200:
            result = cleanup_response.json()
            print(f"✅ Cleanup endpoint works!")
            print(f"   {result['message']}")
        else:
            print(f"❌ Cleanup failed: {cleanup_response.status_code}")
    except Exception as e:
        print(f"❌ Error during cleanup test: {e}")
    
    print("\n✅ All tests completed!")
    return True

if __name__ == "__main__":
    test_temp_feature()