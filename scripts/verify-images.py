#!/usr/bin/env python3
"""
Verify images in MongoDB have proper Base64 data

Usage:
    python scripts/verify-images.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services import DBConn
from app.config.Config import settings

def verify_images():
    """Check all images in MongoDB for valid data"""
    
    print("🔍 Checking images in MongoDB...\n")
    
    # Get all images
    images = DBConn.find_docs(
        collection="Images",
        query={},
        include_id=True
    )
    
    if not images:
        print("❌ No images found in MongoDB")
        return
    
    print(f"Found {len(images)} images\n")
    
    valid_count = 0
    invalid_count = 0
    
    for img in images:
        filename = img.get('filename', 'unknown')
        path = img.get('path', 'unknown')
        data = img.get('data', '')
        
        # Check if data exists and looks like Base64
        if not data:
            print(f"❌ {filename} ({path})")
            print(f"   Error: No data field\n")
            invalid_count += 1
        elif len(data) < 100:
            print(f"❌ {filename} ({path})")
            print(f"   Error: Data too short ({len(data)} chars) - not real Base64")
            print(f"   Data preview: {data[:50]}\n")
            invalid_count += 1
        elif data == "the image data":
            print(f"❌ {filename} ({path})")
            print(f"   Error: Contains placeholder text instead of image data\n")
            invalid_count += 1
        else:
            # Looks valid
            data_kb = len(data) / 1024
            print(f"✓ {filename} ({path})")
            print(f"   Data size: {data_kb:.1f} KB (Base64)")
            print(f"   Preview: {data[:50]}...\n")
            valid_count += 1
    
    print("="*60)
    print(f"Summary:")
    print(f"  ✓ Valid: {valid_count}")
    print(f"  ❌ Invalid: {invalid_count}")
    print(f"  Total: {len(images)}")
    print("="*60)
    
    if invalid_count > 0:
        print("\n⚠️  Some images have invalid data!")
        print("Please re-upload them using:")
        print("  cd backend")
        print("  python scripts/bulk-upload-images.py")

if __name__ == "__main__":
    try:
        verify_images()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

