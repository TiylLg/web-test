from fastapi import HTTPException, UploadFile
from fastapi.responses import Response
from app.services import DBConn
from app.config.Config import settings
from datetime import datetime
from PIL import Image
import io
import base64
import zipfile
import logging

log = logging.getLogger("asyncio")


class ImageController:
    def __init__(self):
        self.images_col = "Images"
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
        self.max_file_size = 15 * 1024 * 1024  # 15MB (MongoDB limit is 16MB)

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return ''

    def _get_filename_without_extension(self, filename: str) -> str:
        """Remove extension from filename"""
        if '.' in filename:
            return filename.rsplit('.', 1)[0]
        return filename

    def _validate_image(self, file_content: bytes, filename: str) -> dict:
        """Validate image file and extract metadata"""
        extension = self._get_file_extension(filename)
        
        # Check extension
        if extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(self.allowed_extensions)}"
            )
        
        # Check file size
        if len(file_content) > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {self.max_file_size / 1024 / 1024}MB"
            )
        
        # Try to open image to verify it's valid (except SVG)
        metadata = {}
        if extension != 'svg':
            try:
                img = Image.open(io.BytesIO(file_content))
                metadata['width'] = img.width
                metadata['height'] = img.height
                metadata['format'] = img.format
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
        
        return metadata

    def _determine_category(self, filename: str) -> str:
        """Determine image category based on filename"""
        filename_lower = filename.lower()
        
        if 'product' in filename_lower and 'studio' not in filename_lower:
            return 'product'
        elif 'studio' in filename_lower and 'product' in filename_lower:
            return 'studio-product'
        elif 'studio' in filename_lower:
            return 'studio'
        else:
            return 'other'

    async def upload_image(self, file: UploadFile, category: str = None):
        """
        Upload an image to MongoDB
        
        Args:
            file: UploadFile from FastAPI
            category: Optional category override
            
        Returns:
            dict: Upload result with image details
            
        Raises:
            HTTPException: If upload fails or validation fails
        """
        log.info(f"ImageController: Uploading image: {file.filename}")
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Validate image
            metadata = self._validate_image(file_content, file.filename)
            
            # Get content type
            extension = self._get_file_extension(file.filename)
            content_type_map = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'svg': 'image/svg+xml',
                'webp': 'image/webp'
            }
            content_type = content_type_map.get(extension, 'application/octet-stream')
            
            # Encode to base64
            base64_data = base64.b64encode(file_content).decode('utf-8')
            
            # Get filename without extension for path
            filename_no_ext = self._get_filename_without_extension(file.filename)
            
            # Determine category
            if category is None:
                category = self._determine_category(file.filename)
            
            # Check if image already exists (by path)
            existing_image = DBConn.aggregate(
                collection=self.images_col,
                match_query={"path": f"images/{filename_no_ext}"},
                project_fields=["path"]
            )
            
            # Create document
            image_document = {
                "filename": file.filename,
                "path": f"images/{filename_no_ext}",  # No extension in path
                "category": category,
                "contentType": content_type,
                "extension": extension,  # Store extension separately
                "data": base64_data,
                "size": len(file_content),
                "uploadedAt": datetime.now(),
                "metadata": metadata
            }
            
            if existing_image:
                # Update existing image
                log.info(f"Updating existing image: {filename_no_ext}")
                DBConn.upsert_doc(
                    collection=self.images_col,
                    match_query={"path": f"images/{filename_no_ext}"},
                    update_data={
                        "filename": file.filename,
                        "category": category,
                        "contentType": content_type,
                        "extension": extension,
                        "data": base64_data,
                        "size": len(file_content),
                        "uploadedAt": datetime.now(),
                        "metadata": metadata
                    }
                )
                action = "updated"
            else:
                # Insert new image
                log.info(f"Inserting new image: {filename_no_ext}")
                DBConn.insert_doc(
                    collection=self.images_col,
                    payload=image_document
                )
                action = "uploaded"
            
            log.info(f"Image {action} successfully: {file.filename} ({len(file_content) / 1024:.2f} KB)")
            
            return {
                "success": True,
                "action": action,
                "filename": file.filename,
                "path": f"images/{filename_no_ext}",
                "category": category,
                "size": len(file_content),
                "contentType": content_type,
                "metadata": metadata
            }
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error uploading image {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

    def get_all_images(self):
        """
        Get all images from MongoDB
        
        Returns:
            list: List of all image documents
        """
        log.info("ImageController: Getting all images")
        
        try:
            images = DBConn.find_docs(
                collection=self.images_col,
                query={}
            )
            
            log.info(f"Found {len(images)} images in database")
            return images
            
        except Exception as e:
            log.error(f"Error getting images: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get images: {str(e)}")

    def delete_image(self, path: str):
        """
        Delete an image from MongoDB
        
        Args:
            path: Image path (without extension)
            
        Returns:
            dict: Deletion result
        """
        log.info(f"ImageController: Deleting image: {path}")
        
        try:
            result = DBConn.delete_doc(
                collection=self.images_col,
                delete_query={"path": path}
            )
            
            if result.deleted_count > 0:
                log.info(f"Image deleted successfully: {path}")
                return {"success": True, "message": "Image deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="Image not found")
                
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error deleting image {path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

    def get_single_image(self, path: str):
        """
        Get a single image by path and return as binary
        
        Args:
            path: Image path without extension (e.g., "images/product 1")
            
        Returns:
            Response: Image binary with proper content-type and caching headers
            
        Raises:
            HTTPException: If image not found or retrieval fails
        """
        log.info(f"ImageController: Retrieving image: {path}")
        
        try:
            # Normalize path (remove leading slash if present)
            normalized_path = path.lstrip('/')
            
            # Add "images/" prefix if not present
            if not normalized_path.startswith('images/'):
                normalized_path = f"images/{normalized_path}"
            
            # Find image in MongoDB
            image = DBConn.find_doc(
                collection=self.images_col,
                find_query={"path": normalized_path}
            )
            
            if not image:
                log.warning(f"Image not found: {normalized_path}")
                raise HTTPException(status_code=404, detail=f"Image not found: {path}")
            
            # Get image data
            base64_data = image.get('data')
            content_type = image.get('contentType', 'image/png')
            filename = image.get('filename', 'image')
            
            if not base64_data:
                log.error(f"Image has no data: {normalized_path}")
                raise HTTPException(status_code=500, detail="Image data is missing")
            
            # Decode base64 to binary
            try:
                image_binary = base64.b64decode(base64_data)
            except Exception as e:
                log.error(f"Failed to decode Base64 for {normalized_path}: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to decode image data")
            
            log.info(f"Serving image: {normalized_path} ({len(image_binary) / 1024:.2f} KB)")
            
            # Return image with caching headers
            return Response(
                content=image_binary,
                media_type=content_type,
                headers={
                    # Cache for 1 year (images rarely change)
                    "Cache-Control": "public, max-age=31536000, immutable",
                    # ETag for cache validation
                    "ETag": f'"{str(image.get("_id"))}"',
                    # Allow CORS (for development)
                    "Access-Control-Allow-Origin": "*",
                    # Filename hint for downloads
                    "Content-Disposition": f'inline; filename="{filename}"'
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error retrieving image {path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")

    def download_all_images_as_zip(self):
        """
        Download all images from MongoDB as a ZIP file
        
        Returns:
            Response: ZIP file with all images
            
        Raises:
            HTTPException: If download fails
        """
        log.info("ImageController: Creating ZIP file with all images")
        
        try:
            # Get all images from MongoDB
            images = DBConn.find_docs(
                collection=self.images_col,
                query={}
            )
            
            if not images:
                raise HTTPException(status_code=404, detail="No images found")
            
            log.info(f"Found {len(images)} images to zip")
            
            # Create ZIP file in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for image in images:
                    try:
                        # Get image data
                        filename = image.get('filename')
                        extension = image.get('extension', 'png')
                        base64_data = image.get('data')
                        
                        if not base64_data or not filename:
                            log.warning(f"Skipping image with missing data: {filename}")
                            continue
                        
                        # Decode base64 to binary
                        image_binary = base64.b64decode(base64_data)
                        
                        # Add to ZIP with original filename
                        zip_file.writestr(filename, image_binary)
                        log.info(f"Added to ZIP: {filename}")
                        
                    except Exception as e:
                        log.error(f"Error processing image {filename}: {str(e)}")
                        continue
            
            # Get ZIP content
            zip_buffer.seek(0)
            zip_content = zip_buffer.getvalue()
            
            log.info(f"ZIP file created successfully with {len(images)} images ({len(zip_content) / 1024 / 1024:.2f} MB)")
            
            # Return ZIP file as response
            return Response(
                content=zip_content,
                media_type="application/zip",
                headers={
                    "Content-Disposition": "attachment; filename=images.zip"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error creating ZIP file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create ZIP file: {str(e)}")

    async def bulk_upload_from_zip(self, zip_file: UploadFile, category: str):
        """
        Extract ZIP file and upload all images with the specified category
        
        Args:
            zip_file: ZIP file containing images
            category: Category for all images (product or studio)
            
        Returns:
            dict: Bulk upload results
        """
        log.info(f"ImageController: Bulk uploading from ZIP: {zip_file.filename}, category: {category}")
        
        try:
            # Read ZIP content
            zip_content = await zip_file.read()
            zip_buffer = io.BytesIO(zip_content)
            
            results = []
            successful = 0
            failed = 0
            
            with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                log.info(f"Found {len(file_list)} files in ZIP")
                
                for filename in file_list:
                    # Skip directories and hidden files
                    if filename.endswith('/') or filename.startswith('.') or '/' in filename and filename.split('/')[-1].startswith('.'):
                        continue
                    
                    # Get just the filename (remove path)
                    base_filename = filename.split('/')[-1]
                    
                    # Check if it's an image file
                    extension = self._get_file_extension(base_filename)
                    if extension not in self.allowed_extensions:
                        log.warning(f"Skipping non-image file: {base_filename}")
                        continue
                    
                    try:
                        # Read file from ZIP
                        file_data = zip_ref.read(filename)
                        
                        # Create UploadFile-like object
                        file_obj = io.BytesIO(file_data)
                        
                        # Validate it's a valid image
                        try:
                            img = Image.open(file_obj)
                            img.verify()
                            file_obj.seek(0)  # Reset after verify
                        except Exception as e:
                            results.append({
                                "filename": base_filename,
                                "status": "failed",
                                "error": f"Invalid image file: {str(e)}"
                            })
                            failed += 1
                            continue
                        
                        # Upload the image
                        result = self._upload_image_data(base_filename, file_data, category)
                        results.append({
                            "filename": base_filename,
                            "status": "success",
                            "action": result.get("action"),
                            "path": result.get("path"),
                            "size": result.get("size")
                        })
                        successful += 1
                        log.info(f"Successfully uploaded from ZIP: {base_filename}")
                        
                    except Exception as e:
                        results.append({
                            "filename": base_filename,
                            "status": "failed",
                            "error": str(e)
                        })
                        failed += 1
                        log.error(f"Failed to upload {base_filename}: {str(e)}")
            
            log.info(f"Bulk ZIP upload complete: {successful} successful, {failed} failed")
            
            return {
                "success": failed == 0,
                "total": successful + failed,
                "successful": successful,
                "failed": failed,
                "category": category,
                "results": results
            }
            
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file")
        except Exception as e:
            log.error(f"Error processing ZIP file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process ZIP file: {str(e)}")

    def _upload_image_data(self, filename: str, file_data: bytes, category: str = None):
        """
        Upload image data to MongoDB (helper method for bulk upload)
        
        Args:
            filename: Original filename
            file_data: Image binary data
            category: Image category
            
        Returns:
            dict: Upload result
        """
        # Get extension
        extension = self._get_file_extension(filename)
        
        # Auto-detect category if not provided
        if not category:
            category = self._auto_detect_category(filename)
        
        # Generate path (without extension)
        filename_without_ext = self._get_filename_without_extension(filename)
        image_path = f"images/{filename_without_ext}"
        
        # Encode to base64
        base64_data = base64.b64encode(file_data).decode('utf-8')
        
        # Get image metadata
        img = Image.open(io.BytesIO(file_data))
        width, height = img.size
        img_format = img.format
        
        # Get content type
        content_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
            'webp': 'image/webp'
        }
        content_type = content_type_map.get(extension, 'image/png')
        
        # Check if image already exists
        existing_image = DBConn.find_doc(
            collection=self.images_col,
            find_query={"path": image_path},
            include_id=False
        )
        
        # Prepare document
        image_doc = {
            "filename": filename,
            "path": image_path,
            "category": category,
            "contentType": content_type,
            "extension": extension,
            "data": base64_data,
            "size": len(file_data),
            "uploadedAt": datetime.utcnow(),
            "metadata": {
                "width": width,
                "height": height,
                "format": img_format
            }
        }
        
        if existing_image:
            # Update existing image
            DBConn.upsert_doc(
                collection=self.images_col,
                match_query={"path": image_path},
                update_data=image_doc
            )
            action = "updated"
        else:
            # Insert new image
            DBConn.insert_doc(
                collection=self.images_col,
                payload=image_doc
            )
            action = "uploaded"
        
        return {
            "success": True,
            "action": action,
            "filename": filename,
            "path": image_path,
            "category": category,
            "size": len(file_data),
            "contentType": content_type
        }

    async def upload_detail_images_from_zip(self, product_name: str, zip_file: UploadFile):
        """
        Upload detail images for a product from ZIP file
        
        Args:
            product_name: Product name (used as filename for all images)
            zip_file: ZIP file containing detail images
            
        Returns:
            dict: Upload results
        """
        log.info(f"ImageController: Uploading detail images for product: {product_name}")
        
        try:
            # Read ZIP content
            zip_content = await zip_file.read()
            zip_buffer = io.BytesIO(zip_content)
            
            results = []
            successful = 0
            failed = 0
            
            with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                log.info(f"Found {len(file_list)} files in ZIP for product: {product_name}")
                
                for filename in file_list:
                    # Skip directories and hidden files
                    if filename.endswith('/') or filename.startswith('.') or '/' in filename and filename.split('/')[-1].startswith('.'):
                        continue
                    
                    # Get just the filename (remove path)
                    base_filename = filename.split('/')[-1]
                    
                    # Check if it's an image file
                    extension = self._get_file_extension(base_filename)
                    if extension not in self.allowed_extensions:
                        log.warning(f"Skipping non-image file: {base_filename}")
                        continue
                    
                    try:
                        # Read file from ZIP
                        file_data = zip_ref.read(filename)
                        
                        # Validate it's a valid image
                        try:
                            img = Image.open(io.BytesIO(file_data))
                            img.verify()
                        except Exception as e:
                            results.append({
                                "filename": base_filename,
                                "status": "failed",
                                "error": f"Invalid image file: {str(e)}"
                            })
                            failed += 1
                            continue
                        
                        # Generate path: images/detail/{actual_filename_without_extension}
                        filename_without_ext = self._get_filename_without_extension(base_filename)
                        image_path = f"images/detail/{filename_without_ext}"
                        
                        # Encode to base64
                        base64_data = base64.b64encode(file_data).decode('utf-8')
                        
                        # Get image metadata
                        img = Image.open(io.BytesIO(file_data))
                        width, height = img.size
                        img_format = img.format
                        
                        # Get content type
                        content_type_map = {
                            'png': 'image/png',
                            'jpg': 'image/jpeg',
                            'jpeg': 'image/jpeg',
                            'gif': 'image/gif',
                            'svg': 'image/svg+xml',
                            'webp': 'image/webp'
                        }
                        content_type = content_type_map.get(extension, 'image/png')
                        
                        # Prepare document
                        image_doc = {
                            "filename": product_name,  # Use product name as filename
                            "path": image_path,
                            "category": "detail",
                            "contentType": content_type,
                            "extension": extension,
                            "data": base64_data,
                            "size": len(file_data),
                            "uploadedAt": datetime.utcnow(),
                            "metadata": {
                                "width": width,
                                "height": height,
                                "format": img_format,
                                "originalFilename": base_filename
                            }
                        }
                        
                        # Check if already exists
                        existing_image = DBConn.find_doc(
                            collection=self.images_col,
                            find_query={"path": image_path},
                            include_id=False
                        )
                        
                        if existing_image:
                            # Update existing
                            DBConn.upsert_doc(
                                collection=self.images_col,
                                match_query={"path": image_path},
                                update_data=image_doc
                            )
                            action = "updated"
                        else:
                            # Insert new
                            DBConn.insert_doc(
                                collection=self.images_col,
                                payload=image_doc
                            )
                            action = "uploaded"
                        
                        results.append({
                            "filename": base_filename,
                            "status": "success",
                            "action": action,
                            "path": image_path,
                            "size": len(file_data)
                        })
                        successful += 1
                        log.info(f"Successfully uploaded detail image: {base_filename} -> {image_path}")
                        
                    except Exception as e:
                        results.append({
                            "filename": base_filename,
                            "status": "failed",
                            "error": str(e)
                        })
                        failed += 1
                        log.error(f"Failed to upload detail image {base_filename}: {str(e)}")
            
            log.info(f"Detail images upload complete for {product_name}: {successful} successful, {failed} failed")
            
            return {
                "success": failed == 0,
                "product_name": product_name,
                "total": successful + failed,
                "successful": successful,
                "failed": failed,
                "results": results
            }
            
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file")
        except Exception as e:
            log.error(f"Error processing detail images ZIP: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process ZIP file: {str(e)}")

    def get_detail_images(self, product_name: str):
        """
        Get detail image paths for a product
        
        Args:
            product_name: Product name
            
        Returns:
            dict: List of image paths
        """
        log.info(f"ImageController: Getting detail images for product: {product_name}")
        
        try:
            # Find all images with filename=product_name and category=detail
            images = DBConn.find_docs(
                collection=self.images_col,
                query={
                    "filename": product_name,
                    "category": "detail"
                },
                include_id=False
            )
            
            # Extract paths
            paths = [img.get("path") for img in images if img.get("path")]
            
            log.info(f"Found {len(paths)} detail images for product: {product_name}")
            
            return {
                "product_name": product_name,
                "count": len(paths),
                "paths": paths
            }
            
        except Exception as e:
            log.error(f"Error getting detail images for {product_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get detail images: {str(e)}")

