# Image Upload API Documentation

Complete guide for uploading and managing images in MongoDB.

## 🎯 Overview

Images are stored in MongoDB with paths **without extensions**. The frontend refers to images without extensions, and the API automatically handles the extension mapping.

### **Example:**
```
Upload: product 1.png
Stored path: images/product 1  (no .png)
Frontend usage: <img src="/images/product 1" />
```

---

## 🔐 Authentication

All image endpoints use **DROPSHIP_PASSWORD** authentication (same as order export).

Add header: `X-Dropship-Password: your_password_here`

---

## 📍 API Endpoints

All image endpoints are under the **`images`** router tag in Swagger UI.

Base path: `/api/v1/`

---

## 📤 Upload Image

### **POST** `/api/v1/upload-image`

Upload a single image to MongoDB.

**Headers:**
```
X-Dropship-Password: your_password_here
Content-Type: multipart/form-data
```

**Body (form-data):**
- `file`: Image file (required)
- `category`: Optional category (`product`, `studio`, `studio-product`, `other`)

**Supported formats:** PNG, JPG, JPEG, GIF, SVG, WEBP

**Max file size:** 15MB

### **Example: cURL**

```bash
curl -X POST "http://localhost:8000/api/v1/upload-image" \
  -H "X-Dropship-Password: your_password_here" \
  -F "file=@/path/to/product 1.png" \
  -F "category=product"
```

### **Example: Python**

```python
import requests

url = "http://localhost:8000/api/v1/upload-image"
headers = {"X-Dropship-Password": "your_password_here"}

# Upload single image
with open("public/images/product 1.png", "rb") as f:
    files = {"file": f}
    data = {"category": "product"}  # Optional
    response = requests.post(url, headers=headers, files=files, data=data)
    print(response.json())
```

### **Example: JavaScript (Browser)**

```javascript
const uploadImage = async (file, category = null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (category) {
    formData.append('category', category);
  }

  const response = await fetch('http://localhost:8000/api/v1/upload-image', {
    method: 'POST',
    headers: {
      'X-Dropship-Password': 'your_password_here'
    },
    body: formData
  });

  return await response.json();
};

// Usage with file input
document.getElementById('fileInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const result = await uploadImage(file, 'product');
  console.log(result);
});
```

### **Example: Postman**

1. Method: `POST`
2. URL: `http://localhost:8000/api/v1/upload-image`
3. Headers:
   - `X-Dropship-Password`: `your_password_here`
4. Body:
   - Select `form-data`
   - Key: `file` (type: File) → Select your image
   - Key: `category` (type: Text) → `product`
5. Click "Send"

### **Response:**

```json
{
  "success": true,
  "action": "uploaded",
  "filename": "product 1.png",
  "path": "images/product 1",
  "category": "product",
  "size": 245632,
  "contentType": "image/png",
  "metadata": {
    "width": 1920,
    "height": 1080,
    "format": "PNG"
  }
}
```

---

## 📦 Bulk Upload Images

### **POST** `/api/v1/bulk-upload-images`

Upload multiple images at once with the same category.

**Headers:**
```
X-Dropship-Password: your_password_here
Content-Type: multipart/form-data
```

**Body (form-data):**
- `files`: Multiple image files (required)
- `category`: Category for all images (required: `product`, `studio`, `studio-product`, `other`)

**Max files:** No limit (but be mindful of request size)

### **Example: cURL**

```bash
curl -X POST "http://localhost:8000/api/v1/bulk-upload-images" \
  -H "X-Dropship-Password: your_password_here" \
  -F "files=@public/images/product 1.png" \
  -F "files=@public/images/product 2.png" \
  -F "files=@public/images/product 3.png" \
  -F "files=@public/images/product 4.png" \
  -F "category=product"
```

### **Example: Python**

```python
import requests
from pathlib import Path

url = "http://localhost:8000/api/v1/bulk-upload-images"
headers = {"X-Dropship-Password": "your_password_here"}

# Get all product images
image_dir = Path("public/images")
product_images = list(image_dir.glob("product *.png"))

# Prepare files for upload
files = [('files', (img.name, open(img, 'rb'), 'image/png')) for img in product_images]
data = {'category': 'product'}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

print(f"Total: {result['total']}")
print(f"Successful: {result['successful']}")
print(f"Failed: {result['failed']}")

# Print individual results
for item in result['results']:
    if item['status'] == 'success':
        print(f"✓ {item['filename']} → {item['path']}")
    else:
        print(f"✗ {item['filename']}: {item['error']}")

# Close all file handles
for _, file_tuple in files:
    file_tuple[1].close()
```

### **Example: JavaScript (Browser)**

```javascript
const bulkUploadImages = async (files, category) => {
  const formData = new FormData();
  
  // Add all files
  files.forEach(file => {
    formData.append('files', file);
  });
  
  // Add category
  formData.append('category', category);

  const response = await fetch('http://localhost:8000/api/v1/bulk-upload-images', {
    method: 'POST',
    headers: {
      'X-Dropship-Password': 'your_password_here'
    },
    body: formData
  });

  return await response.json();
};

// Usage with file input (multiple files)
document.getElementById('fileInput').addEventListener('change', async (e) => {
  const files = Array.from(e.target.files);
  const result = await bulkUploadImages(files, 'product');
  
  console.log(`Uploaded ${result.successful}/${result.total} images`);
  result.results.forEach(item => {
    if (item.status === 'success') {
      console.log(`✓ ${item.filename}`);
    } else {
      console.error(`✗ ${item.filename}: ${item.error}`);
    }
  });
});
```

### **Example: Postman**

1. Method: `POST`
2. URL: `http://localhost:8000/api/v1/bulk-upload-images`
3. Headers:
   - `X-Dropship-Password`: `your_password_here`
4. Body:
   - Select `form-data`
   - Key: `files` (type: File) → Select **multiple images** (hold Ctrl/Cmd)
   - Key: `category` (type: Text) → `product`
5. Click "Send"

### **Response:**

```json
{
  "success": true,
  "total": 4,
  "successful": 4,
  "failed": 0,
  "category": "product",
  "results": [
    {
      "filename": "product 1.png",
      "status": "success",
      "action": "uploaded",
      "path": "images/product 1",
      "size": 245632
    },
    {
      "filename": "product 2.png",
      "status": "success",
      "action": "uploaded",
      "path": "images/product 2",
      "size": 198432
    },
    {
      "filename": "product 3.png",
      "status": "success",
      "action": "updated",
      "path": "images/product 3",
      "size": 312567
    },
    {
      "filename": "product 4.png",
      "status": "success",
      "action": "uploaded",
      "path": "images/product 4",
      "size": 287345
    }
  ]
}
```

**Error Example (some failed):**

```json
{
  "success": false,
  "total": 4,
  "successful": 3,
  "failed": 1,
  "category": "product",
  "results": [
    {
      "filename": "product 1.png",
      "status": "success",
      "action": "uploaded",
      "path": "images/product 1",
      "size": 245632
    },
    {
      "filename": "product 2.png",
      "status": "success",
      "action": "uploaded",
      "path": "images/product 2",
      "size": 198432
    },
    {
      "filename": "large_image.bmp",
      "status": "failed",
      "error": "Invalid file type. Allowed: png, jpg, jpeg, gif, svg, webp"
    },
    {
      "filename": "product 4.png",
      "status": "success",
      "action": "uploaded",
      "path": "images/product 4",
      "size": 287345
    }
  ]
}
```

---

## 🖼️ Get Single Image

### **GET** `/api/v1/get-image/{path}`

Get a single image by path. Returns image binary with proper content-type. No authentication required.

**Note:** This endpoint is designed for frontend to dynamically load images from MongoDB.

### **Path Parameter:**
- `path`: Image path without extension (e.g., `product 1` or `images/product 1`)

### **Example: cURL**

```bash
# Get product image
curl http://localhost:8000/api/v1/get-image/product%201 -o product1.png

# Get studio image
curl http://localhost:8000/api/v1/get-image/studio%201 -o studio1.png
```

### **Example: Browser**

Simply use the URL in an `<img>` tag or CSS:

```html
<!-- HTML -->
<img src="http://localhost:8000/api/v1/get-image/product 1" alt="Product 1">

<!-- CSS -->
<div style="background-image: url('http://localhost:8000/api/v1/get-image/studio 1')"></div>
```

### **Example: JavaScript**

```javascript
// Direct image URL
const imageUrl = 'http://localhost:8000/api/v1/get-image/product 1';

// Use in React
function ProductCard() {
  return <img src={imageUrl} alt="Product" />;
}

// Fetch as blob
const response = await fetch('http://localhost:8000/api/v1/get-image/product 1');
const blob = await response.blob();
const objectUrl = URL.createObjectURL(blob);
```

### **Response Headers:**

```
Content-Type: image/png (or appropriate type)
Cache-Control: public, max-age=31536000, immutable
ETag: "507f1f77bcf86cd799439011"
Access-Control-Allow-Origin: *
Content-Disposition: inline; filename="product 1.png"
```

**Browser caching:** Images are cached for 1 year (31536000 seconds).

### **Frontend Helper (React):**

For easier usage in React, use the provided utilities:

```jsx
// src/utils/imageUtils.js
import { getImageUrl } from '../utils/imageUtils';

function ProductCard() {
  const imageUrl = getImageUrl('product 1');
  return <img src={imageUrl} alt="Product" />;
}

// Or use the DynamicImage component
import DynamicImage from '../components/DynamicImage';

function ProductCard() {
  return <DynamicImage src="product 1" alt="Product" />;
}
```

---

## 📥 Download All Images

### **GET** `/api/v1/download-all-images`

Download all images from MongoDB as a ZIP file. No authentication required.

**Note:** This endpoint is designed for frontend to download images on startup. All images are downloaded in their original format with filenames.

### **Example: cURL**

```bash
curl -X GET "http://localhost:8000/api/v1/download-all-images" \
  -o images.zip
```

### **Example: Python**

```python
import requests

url = "http://localhost:8000/api/v1/download-all-images"

# Download ZIP file
response = requests.get(url)

if response.status_code == 200:
    with open("images.zip", "wb") as f:
        f.write(response.content)
    print("✓ Downloaded images.zip")
else:
    print(f"Error: {response.status_code}")
```

### **Example: JavaScript (Browser)**

```javascript
const downloadAllImages = async () => {
  const response = await fetch('http://localhost:8000/api/v1/download-all-images');
  
  if (response.ok) {
    const blob = await response.blob();
    
    // Create download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'images.zip';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
};

// Usage
downloadAllImages();
```

### **Response:**

Returns a ZIP file containing all images with their original filenames.

```
images.zip
├── product 1.png
├── product 2.png
├── product 3.png
├── product 4.png
├── studio 1.png
├── studio 1 product 1.png
└── ...
```

---

## 📋 List Images

### **GET** `/api/v1/list-images`

Get list of all images (without base64 data).

**Headers:**
```
X-Dropship-Password: your_password_here
```

### **Example: cURL**

```bash
curl -X GET "http://localhost:8000/api/v1/list-images" \
  -H "X-Dropship-Password: your_password_here"
```

### **Example: Python**

```python
import requests

url = "http://localhost:8000/api/v1/list-images"
headers = {"X-Dropship-Password": "your_password_here"}

response = requests.get(url, headers=headers)
images = response.json()

print(f"Total images: {images['count']}")
for img in images['images']:
    print(f"- {img['filename']} ({img['size']} bytes)")
```

### **Response:**

```json
{
  "images": [
    {
      "filename": "product 1.png",
      "path": "images/product 1",
      "category": "product",
      "contentType": "image/png",
      "extension": "png",
      "size": 245632,
      "uploadedAt": "2025-10-26T12:00:00",
      "metadata": {
        "width": 1920,
        "height": 1080,
        "format": "PNG"
      }
    }
  ],
  "count": 1
}
```

---

## 🗑️ Delete Image

### **DELETE** `/api/v1/delete-image`

Delete an image by path.

**Headers:**
```
X-Dropship-Password: your_password_here
```

**Query Parameters:**
- `path`: Image path without extension (e.g., `images/product 1`)

### **Example: cURL**

```bash
curl -X DELETE "http://localhost:8000/api/v1/delete-image?path=images/product%201" \
  -H "X-Dropship-Password: your_password_here"
```

### **Example: Python**

```python
import requests

url = "http://localhost:8000/api/v1/delete-image"
headers = {"X-Dropship-Password": "your_password_here"}
params = {"path": "images/product 1"}

response = requests.delete(url, headers=headers, params=params)
print(response.json())
```

### **Response:**

```json
{
  "success": true,
  "message": "Image deleted successfully"
}
```

---

## 🔄 Bulk Upload Script

Upload all images from a directory:

```python
# scripts/bulk-upload-images.py
import os
import requests
from pathlib import Path

API_URL = "http://localhost:8000/api/v1/upload-image"
PASSWORD = "your_password_here"
IMAGES_DIR = "public/images"

def upload_all_images():
    headers = {"X-Dropship-Password": PASSWORD}
    
    # Get all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
    image_files = []
    
    for file_path in Path(IMAGES_DIR).iterdir():
        if file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)
    
    print(f"Found {len(image_files)} images to upload")
    
    # Upload each image
    for i, file_path in enumerate(image_files, 1):
        filename = file_path.name
        
        # Determine category
        if 'product' in filename.lower() and 'studio' not in filename.lower():
            category = 'product'
        elif 'studio' in filename.lower() and 'product' in filename.lower():
            category = 'studio-product'
        elif 'studio' in filename.lower():
            category = 'studio'
        else:
            category = 'other'
        
        print(f"[{i}/{len(image_files)}] Uploading {filename} ({category})...")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, f'image/{file_path.suffix[1:]}')}
                data = {'category': category}
                response = requests.post(API_URL, headers=headers, files=files, data=data)
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"  ✓ {result['action'].capitalize()}: {result['path']}")
                else:
                    print(f"  ✗ Error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    print(f"\n✅ Upload complete!")

if __name__ == "__main__":
    upload_all_images()
```

**Run:**
```bash
python scripts/bulk-upload-images.py
```

---

## 📊 Image Storage Details

### **MongoDB Document Structure:**

```javascript
{
  "_id": ObjectId("..."),
  "filename": "product 1.png",           // Original filename with extension
  "path": "images/product 1",            // Path WITHOUT extension
  "category": "product",                 // Auto-detected or specified
  "contentType": "image/png",            // MIME type
  "extension": "png",                    // Extension stored separately
  "data": "iVBORw0KGgoAAAANS...",       // Base64 encoded image
  "size": 245632,                        // Size in bytes
  "uploadedAt": ISODate("2025-10-26..."),
  "metadata": {
    "width": 1920,
    "height": 1080,
    "format": "PNG"
  }
}
```

### **Categories:**

- `product`: Product images
- `studio`: Studio main images
- `studio-product`: Studio product images
- `other`: Uncategorized

Categories are auto-detected from filename:
- Contains "product" (not "studio") → `product`
- Contains "studio" + "product" → `studio-product`
- Contains "studio" → `studio`
- Otherwise → `other`

---

## 🎨 Frontend Usage

The frontend will reference images **without extensions**:

```jsx
// React
<img src="/images/product 1" alt="Product 1" />

// HTML
<img src="/images/studio 1" alt="Studio 1" />

// CSS
background-image: url('/images/product 2');
```

The browser/server will automatically serve the correct file type based on the stored `contentType` and `extension`.

---

## ⚠️ Important Notes

### **Duplicate Handling:**
- If you upload an image with the same **path** (filename without extension), it will **update** the existing image
- Example: Uploading `product 1.png` again will replace the existing `images/product 1`

### **File Size Limits:**
- **Maximum:** 15MB per image
- **MongoDB document limit:** 16MB
- If images are larger, optimize them first:

```bash
# Using ImageMagick
convert input.png -quality 85 -resize 1920x1080 output.png

# Batch process
for file in *.png; do 
  convert "$file" -quality 85 -resize 1920x1080 "optimized/$file"
done
```

### **Supported Formats:**
- ✅ PNG
- ✅ JPG/JPEG
- ✅ GIF
- ✅ SVG
- ✅ WEBP
- ❌ BMP, TIFF (not supported)

### **Security:**
- All endpoints require `DROPSHIP_PASSWORD`
- Images are validated before storage
- Only image types are allowed
- File size is checked

---

## 🔧 Testing in Swagger UI

1. Go to `http://localhost:8000/docs`
2. Find `/api/v1/upload-image`
3. Click "Try it out"
4. Click "Add string item" under `X-Dropship-Password` header
5. Enter your password
6. Click "Choose File" under `file`
7. Select your image
8. (Optional) Enter category
9. Click "Execute"
10. See the response with image details

---

## 📝 Quick Reference

```bash
# Get single image (no auth)
curl http://localhost:8000/api/v1/get-image/product%201 -o product1.png

# Upload single image
curl -X POST "http://localhost:8000/api/v1/upload-image" \
  -H "X-Dropship-Password: PASSWORD" \
  -F "file=@image.png" \
  -F "category=product"

# Bulk upload images (same category)
curl -X POST "http://localhost:8000/api/v1/bulk-upload-images" \
  -H "X-Dropship-Password: PASSWORD" \
  -F "files=@image1.png" \
  -F "files=@image2.png" \
  -F "files=@image3.png" \
  -F "category=product"

# Download all images as ZIP
curl -X GET "http://localhost:8000/api/v1/download-all-images" \
  -o images.zip

# List all images
curl -X GET "http://localhost:8000/api/v1/list-images" \
  -H "X-Dropship-Password: PASSWORD"

# Delete image
curl -X DELETE "http://localhost:8000/api/v1/delete-image?path=images/product%201" \
  -H "X-Dropship-Password: PASSWORD"
```

---

## ✅ Upload Checklist

Before uploading your images:

- [ ] Images are optimized (< 1MB preferred)
- [ ] Filenames are descriptive (`product 1.png`, not `IMG_1234.png`)
- [ ] Images are in supported format (PNG, JPG, GIF, SVG, WEBP)
- [ ] You have the DROPSHIP_PASSWORD
- [ ] Backend server is running
- [ ] MongoDB is connected

Ready to upload? Use the bulk upload script or Swagger UI!

