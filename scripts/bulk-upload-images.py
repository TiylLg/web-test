#!/usr/bin/env python3
"""
Bulk upload images to MongoDB via API

Usage:
    python scripts/bulk-upload-images.py

Configuration:
    - Set DROPSHIP_PASSWORD in .env file
    - Update IMAGES_DIR if needed
    
Note:
    This script groups images by category and uses the bulk upload endpoint
    for better performance.
"""

import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Configuration
BULK_UPLOAD_URL = os.getenv("BULK_UPLOAD_URL", "http://localhost:8000/api/v1/bulk-upload-images")
PASSWORD = os.getenv("DROPSHIP_PASSWORD")
IMAGES_DIR = Path(__file__).parent.parent.parent / "public" / "images"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def upload_all_images():
    """Upload all images from the images directory grouped by category"""
    
    # Check password
    if not PASSWORD:
        print(f"{Colors.RED}❌ Error: DROPSHIP_PASSWORD not found in environment{Colors.END}")
        print(f"{Colors.YELLOW}Set it in your .env file or export it:{Colors.END}")
        print(f"  export DROPSHIP_PASSWORD='your_password_here'")
        sys.exit(1)
    
    # Check directory exists
    if not IMAGES_DIR.exists():
        print(f"{Colors.RED}❌ Error: Images directory not found: {IMAGES_DIR}{Colors.END}")
        sys.exit(1)
    
    headers = {"X-Dropship-Password": PASSWORD}
    
    # Get all image files and group by category
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
    images_by_category = {
        'product': [],
        'studio': [],
        'studio-product': [],
        'other': []
    }
    
    for file_path in IMAGES_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            filename_lower = file_path.name.lower()
            
            # Determine category
            if 'product' in filename_lower and 'studio' not in filename_lower:
                category = 'product'
            elif 'studio' in filename_lower and 'product' in filename_lower:
                category = 'studio-product'
            elif 'studio' in filename_lower:
                category = 'studio'
            else:
                category = 'other'
            
            images_by_category[category].append(file_path)
    
    # Calculate total images
    total_images = sum(len(files) for files in images_by_category.values())
    
    if total_images == 0:
        print(f"{Colors.YELLOW}⚠️  No images found in {IMAGES_DIR}{Colors.END}")
        return
    
    print(f"{Colors.BLUE}📁 Found {total_images} images in {IMAGES_DIR}{Colors.END}")
    for category, files in images_by_category.items():
        if files:
            print(f"  {category}: {len(files)} images")
    print()
    
    # Upload statistics
    total_uploaded = 0
    total_updated = 0
    total_failed = 0
    
    # Upload each category
    for category, file_paths in images_by_category.items():
        if not file_paths:
            continue
        
        print(f"{Colors.BLUE}📦 Uploading {len(file_paths)} {category} images...{Colors.END}")
        
        try:
            # Prepare files for bulk upload
            files = []
            for file_path in sorted(file_paths):
                files.append(('files', (file_path.name, open(file_path, 'rb'), f'image/{file_path.suffix[1:]}')))
            
            data = {'category': category}
            
            # Send bulk upload request
            response = requests.post(BULK_UPLOAD_URL, headers=headers, files=files, data=data, timeout=60)
            
            # Close all file handles
            for _, file_tuple in files:
                file_tuple[1].close()
            
            if response.status_code in [200, 201]:
                result = response.json()
                
                print(f"{Colors.GREEN}✓ Category '{category}': {result['successful']}/{result['total']} successful{Colors.END}")
                
                # Show individual results
                for item in result['results']:
                    filename = item['filename']
                    file_size_kb = next((f.stat().st_size / 1024 for f in file_paths if f.name == filename), 0)
                    
                    if item['status'] == 'success':
                        action = item.get('action', 'uploaded')
                        if action == 'uploaded':
                            print(f"  {Colors.GREEN}✓{Colors.END} {filename} ({file_size_kb:.1f} KB) - uploaded")
                            total_uploaded += 1
                        elif action == 'updated':
                            print(f"  {Colors.YELLOW}✓{Colors.END} {filename} ({file_size_kb:.1f} KB) - updated")
                            total_updated += 1
                        else:
                            print(f"  {Colors.GREEN}✓{Colors.END} {filename} ({file_size_kb:.1f} KB) - {action}")
                            total_uploaded += 1
                    else:
                        error = item.get('error', 'Unknown error')
                        print(f"  {Colors.RED}✗{Colors.END} {filename} - {error}")
                        total_failed += 1
                
                print()
            else:
                print(f"{Colors.RED}✗ Error {response.status_code}: {response.text[:100]}{Colors.END}\n")
                total_failed += len(file_paths)
                
        except requests.exceptions.Timeout:
            print(f"{Colors.RED}✗ Timeout uploading {category} images{Colors.END}\n")
            total_failed += len(file_paths)
        except Exception as e:
            print(f"{Colors.RED}✗ Failed to upload {category} images: {str(e)}{Colors.END}\n")
            total_failed += len(file_paths)
    
    # Summary
    print(f"{'='*60}")
    print(f"{Colors.BLUE}📊 Upload Summary:{Colors.END}")
    print(f"  {Colors.GREEN}✓ Uploaded: {total_uploaded}{Colors.END}")
    if total_updated > 0:
        print(f"  {Colors.YELLOW}✓ Updated: {total_updated}{Colors.END}")
    if total_failed > 0:
        print(f"  {Colors.RED}✗ Failed: {total_failed}{Colors.END}")
    print(f"  Total: {total_images}")
    print(f"{'='*60}\n")
    
    if total_failed == 0:
        print(f"{Colors.GREEN}✅ All images uploaded successfully!{Colors.END}")
    elif total_uploaded + total_updated > 0:
        print(f"{Colors.YELLOW}⚠️  Upload completed with some failures{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Upload failed{Colors.END}")


if __name__ == "__main__":
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}  📸 Bulk Image Upload to MongoDB{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    try:
        upload_all_images()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Upload interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {e}{Colors.END}")
        sys.exit(1)

