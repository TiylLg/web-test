import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, status, HTTPException, Header, File, UploadFile

from app.config.Config import settings
from app.controller.imagecontroller import ImageController

log = logging.getLogger("asyncio")
router = APIRouter(tags=["images"])


@router.post(
    "/upload-image",
    summary="Upload image to MongoDB",
    description="Upload an image file to MongoDB Images collection (requires dropship password), allowed categories: product, studio, detail",
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
        file: UploadFile = File(...),
        category: Optional[str] = None,
        password: str = Header(..., alias="X-Dropship-Password")
):
    """
    Upload an image to MongoDB.
    
    Authentication: Uses password header (X-Dropship-Password) instead of JWT.
    
    Args:
        file: Image file to upload (png, jpg, jpeg, gif, svg, webp)
        category: Optional category override (product, studio, studio-product, other)
        password: Password from X-Dropship-Password header
        
    Returns:
        Upload result with image details
    """
    log.info(f"upload-image endpoint called for file: {file.filename}")
    
    # Validate password
    if password != settings.dropship_password:
        log.warning(f"Invalid dropship password attempt for image upload")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Validate category
    allowed_categories = ["product", "studio", "detail"]
    if category and category not in allowed_categories:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category. Allowed categories: {', '.join(allowed_categories)}"
        )
    
    # Use ImageController to handle the upload
    controller = ImageController()
    return await controller.upload_image(file, category)


@router.post(
    "/bulk-upload-images",
    summary="Bulk upload images from ZIP file to MongoDB",
    description="Upload a ZIP file containing multiple images with the same category. Allowed categories: product, studio",
    status_code=status.HTTP_201_CREATED,
)
async def bulk_upload_images(
        zip_file: UploadFile = File(...),
        category: str = "product",
        password: str = Header(..., alias="X-Dropship-Password")
):
    """
    Bulk upload images from a ZIP file to MongoDB with the same category.
    
    Authentication: Uses password header (X-Dropship-Password) instead of JWT.
    
    Args:
        zip_file: ZIP file containing image files (png, jpg, jpeg, gif, svg, webp)
        category: Category for all images (product, studio)
        password: Password from X-Dropship-Password header
        
    Returns:
        Bulk upload results with success/failure details for each image
    """
    log.info(f"bulk-upload-images endpoint called with ZIP file: {zip_file.filename}, category: {category}")
    
    # Validate password
    if password != settings.dropship_password:
        log.warning(f"Invalid dropship password attempt for bulk image upload")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Validate category
    allowed_categories = ["product", "studio"]
    if category not in allowed_categories:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category. Allowed categories: {', '.join(allowed_categories)}"
        )
    
    # Validate file is a ZIP
    if not zip_file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a ZIP file")
    
    # Use ImageController to handle bulk upload from ZIP
    controller = ImageController()
    return await controller.bulk_upload_from_zip(zip_file, category)


@router.get(
    "/list-images",
    summary="List all images",
    description="Get list of all images stored in MongoDB",
    status_code=status.HTTP_200_OK,
)
async def list_images(
        password: str = Header(..., alias="X-Dropship-Password")
):
    """
    List all images stored in MongoDB.
    
    Authentication: Uses password header (X-Dropship-Password) instead of JWT.
    
    Args:
        password: Password from X-Dropship-Password header
        
    Returns:
        List of image metadata (without base64 data for efficiency)
    """
    log.info("list-images endpoint called")
    
    # Validate password
    if password != settings.dropship_password:
        log.warning(f"Invalid dropship password attempt for list images")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Use ImageController to get images
    controller = ImageController()
    images = controller.get_all_images()
    
    # Return without base64 data (too large for listing)
    images_summary = []
    for img in images:
        summary = {
            "filename": img.get("filename"),
            "path": img.get("path"),
            "category": img.get("category"),
            "contentType": img.get("contentType"),
            "extension": img.get("extension"),
            "size": img.get("size"),
            "uploadedAt": img.get("uploadedAt"),
            "metadata": img.get("metadata")
        }
        images_summary.append(summary)
    
    return {"images": images_summary, "count": len(images_summary)}


@router.delete(
    "/delete-image",
    summary="Delete image from MongoDB",
    description="Delete an image by path",
    status_code=status.HTTP_200_OK,
)
async def delete_image(
        path: str,
        password: str = Header(..., alias="X-Dropship-Password")
):
    """
    Delete an image from MongoDB.
    
    Authentication: Uses password header (X-Dropship-Password) instead of JWT.
    
    Args:
        path: Image path (e.g., "images/product 1")
        password: Password from X-Dropship-Password header
        
    Returns:
        Deletion result
    """
    log.info(f"delete-image endpoint called for path: {path}")
    
    # Validate password
    if password != settings.dropship_password:
        log.warning(f"Invalid dropship password attempt for delete image")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Use ImageController to delete image
    controller = ImageController()
    return controller.delete_image(path)


@router.get(
    "/get-image/{path:path}",
    summary="Get single image by path",
    description="Get a single image from MongoDB by path (no extension needed). Returns image binary with proper content-type.",
    responses={
        200: {
            "content": {
                "image/png": {},
                "image/jpeg": {},
                "image/gif": {},
                "image/svg+xml": {},
                "image/webp": {}
            },
            "description": "Returns the image binary",
        },
        404: {
            "description": "Image not found"
        }
    }
)
async def get_image(path: str):
    """
    Get a single image by path.
    
    No authentication required - images are public.
    
    Args:
        path: Image path without extension (e.g., "product 1" or "images/product 1")
    
    Returns:
        Image binary with proper content-type and caching headers
        
    Examples:
        - GET /api/v1/get-image/product 1
        - GET /api/v1/get-image/images/product 1
        - GET /api/v1/get-image/studio 1
    """
    log.info(f"get-image endpoint called for path: {path}")
    
    # Use ImageController to retrieve and return image
    controller = ImageController()
    return controller.get_single_image(path)


@router.get(
    "/download-all-images",
    summary="Download all images as ZIP",
    description="Download all images from MongoDB as a ZIP file (no authentication required for frontend)",
    responses={
        200: {
            "content": {"application/zip": {}},
            "description": "Returns a ZIP file with all images",
        }
    }
)
async def download_all_images():
    """
    Download all images as a ZIP file.
    
    No authentication required - this is for frontend to download images on startup.
    
    Returns:
        ZIP file with all images
    """
    log.info("download-all-images endpoint called")
    
    # Use ImageController to create and return ZIP
    controller = ImageController()
    return controller.download_all_images_as_zip()


@router.post(
    "/upload-detail-images",
    summary="Upload detail images for a product from ZIP file",
    description="Upload a ZIP file containing detail images for a specific product. Each file will be stored with category='detail'.",
    status_code=status.HTTP_201_CREATED,
)
async def upload_detail_images(
        product_name: str,
        zip_file: UploadFile = File(...),
        password: str = Header(..., alias="X-Dropship-Password")
):
    """
    Upload detail images for a product from a ZIP file.
    
    Authentication: Uses password header (X-Dropship-Password) instead of JWT.
    
    Args:
        product_name: The product name (used as filename for all images)
        zip_file: ZIP file containing detail images
        password: Password from X-Dropship-Password header
        
    Returns:
        Upload results with details for each image
        
    Each image from the ZIP will be stored with:
    - filename: product_name
    - category: "detail"
    - path: images/detail/{actual_filename_from_zip}
    """
    log.info(f"upload-detail-images endpoint called for product: {product_name}")
    
    # Validate password
    if password != settings.dropship_password:
        log.warning(f"Invalid dropship password attempt for detail image upload")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Validate file is a ZIP
    if not zip_file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a ZIP file")
    
    # Use ImageController to handle detail images upload
    controller = ImageController()
    return await controller.upload_detail_images_from_zip(product_name, zip_file)


@router.get(
    "/get-detail-images",
    summary="Get detail image paths for a product",
    description="Get list of detail image paths for a specific product",
    status_code=status.HTTP_200_OK,
)
async def get_detail_images(product_name: str):
    """
    Get detail image paths for a product.
    
    No authentication required - images are public.
    
    Args:
        product_name: The product name to get detail images for
        
    Returns:
        List of image paths
        
    Example:
        GET /api/v1/get-detail-images?product_name=product 1
        Returns: ["images/detail/image1", "images/detail/image2", ...]
    """
    log.info(f"get-detail-images endpoint called for product: {product_name}")
    
    # Use ImageController to get detail images
    controller = ImageController()
    return controller.get_detail_images(product_name)

