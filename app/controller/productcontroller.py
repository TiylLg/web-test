import logging
from typing import List, Dict, Optional

from fastapi import HTTPException, status

from app.config.Config import settings
from app.services.DBConn import mydb

log = logging.getLogger("asyncio")

class ProductController:
    def __init__(self):
        self.product_col = settings.product_col
        self.studio_col = settings.studio_col

    def get_products(self, studio: str) -> List[Dict]:
        """
        Get products by studio name from Product collection
        Always filters on studio field - no special handling for 'generic'
        """
        try:
            log.info(f"Fetching products for studio: {studio}")
            
            # Get database collection directly
            col = mydb[self.product_col]
            
            # Query for products matching the studio
            products = col.find(
                {"studio": studio},
                {"productName": 1, "price": 1, "details": 1, "studio": 1, "_id": 0}
            )
            
            # Convert MongoDB cursor to list
            product_list = []
            for product in products:
                product_data = {
                    "productName": product.get("productName", ""),
                    "price": product.get("price", 0.0)
                }
                # Include details if available
                if "details" in product:
                    product_data["details"] = product["details"]
                
                product_list.append(product_data)
            
            log.info(f"Found {len(product_list)} products for studio: {studio}")
            return product_list
            
        except Exception as e:
            log.error(f"Error fetching products for studio {studio}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch products: {str(e)}"
            )

    def get_studios(self) -> List[Dict]:
        """
        Get all studios from Studio collection
        Returns studio name and description
        """
        try:
            log.info("Fetching all studios from Studio collection")
            
            # Get database collection directly
            col = mydb[self.studio_col]
            
            # Query all studios
            studios = col.find(
                {},
                {"studio": 1, "description": 1, "_id": 0}
            )
            
            # Convert MongoDB cursor to list
            studio_list = []
            for studio in studios:
                studio_data = {
                    "studio": studio.get("studio", ""),
                    "description": studio.get("description", "")
                }
                studio_list.append(studio_data)
            
            log.info(f"Found {len(studio_list)} studios")
            return studio_list
            
        except Exception as e:
            log.error(f"Error fetching studios: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch studios: {str(e)}"
            )

    def get_studio_by_name(self, studio_name: str) -> Optional[Dict]:
        """
        Get specific studio information by name
        """
        try:
            log.info(f"Fetching studio info for: {studio_name}")
            
            # Get database collection directly
            col = mydb[self.studio_col]
            
            # Query for specific studio
            studio = col.find_one(
                {"studio": studio_name},
                {"studio": 1, "description": 1, "_id": 0}
            )
            
            if studio:
                studio_data = {
                    "studio": studio.get("studio", ""),
                    "description": studio.get("description", "")
                }
                log.info(f"Found studio: {studio_name}")
                return studio_data
            else:
                log.warning(f"Studio not found: {studio_name}")
                return None
                
        except Exception as e:
            log.error(f"Error fetching studio {studio_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch studio: {str(e)}"
            )

    def add_product(self, product_name: str, price: float, details: str, studio: str) -> Dict:
        """
        Add a new product to the Product collection
        Checks if product already exists by productName
        """
        try:
            log.info(f"Adding product: {product_name}")
            
            # Get database collection directly
            col = mydb[self.product_col]
            
            # Check if product with the same name already exists
            existing_product = col.find_one({"productName": product_name})
            if existing_product:
                log.warning(f"Product already exists: {product_name}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with name '{product_name}' already exists"
                )
            
            # Create product document
            product_doc = {
                "productName": product_name,
                "price": price,
                "details": details,
                "studio": studio
            }
            
            # Insert product
            result = col.insert_one(product_doc)
            
            if result.inserted_id:
                log.info(f"Successfully added product: {product_name}")
                return {
                    "message": "Product added successfully",
                    "productName": product_name,
                    "price": price,
                    "details": details,
                    "studio": studio
                }
            else:
                log.error(f"Failed to insert product: {product_name}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add product"
                )
                
        except HTTPException:
            # Re-raise HTTPException as-is
            raise
        except Exception as e:
            log.error(f"Error adding product {product_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add product: {str(e)}"
            )

    def delete_product(self, product_name: str) -> Dict:
        """
        Delete a product from the Product collection by productName
        """
        try:
            log.info(f"Deleting product: {product_name}")
            
            # Get database collection directly
            col = mydb[self.product_col]
            
            # Check if product exists
            existing_product = col.find_one({"productName": product_name})
            if not existing_product:
                log.warning(f"Product not found: {product_name}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with name '{product_name}' not found"
                )
            
            # Delete the product
            result = col.delete_one({"productName": product_name})
            
            if result.deleted_count > 0:
                log.info(f"Successfully deleted product: {product_name}")
                return {
                    "message": "Product deleted successfully",
                    "productName": product_name
                }
            else:
                log.error(f"Failed to delete product: {product_name}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete product"
                )
                
        except HTTPException:
            # Re-raise HTTPException as-is
            raise
        except Exception as e:
            log.error(f"Error deleting product {product_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete product: {str(e)}"
            )

    def add_studio(self, studio_name: str, description: str) -> Dict:
        """
        Add a new studio to the Studio collection
        Checks if studio already exists by studio name
        """
        try:
            log.info(f"Adding studio: {studio_name}")
            
            # Get database collection directly
            col = mydb[self.studio_col]
            
            # Check if studio with the same name already exists
            existing_studio = col.find_one({"studio": studio_name})
            if existing_studio:
                log.warning(f"Studio already exists: {studio_name}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Studio with name '{studio_name}' already exists"
                )
            
            # Create studio document
            studio_doc = {
                "studio": studio_name,
                "description": description
            }
            
            # Insert studio
            result = col.insert_one(studio_doc)
            
            if result.inserted_id:
                log.info(f"Successfully added studio: {studio_name}")
                return {
                    "message": "Studio added successfully",
                    "studio": studio_name,
                    "description": description
                }
            else:
                log.error(f"Failed to insert studio: {studio_name}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add studio"
                )
                
        except HTTPException:
            # Re-raise HTTPException as-is
            raise
        except Exception as e:
            log.error(f"Error adding studio {studio_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add studio: {str(e)}"
            )

    def delete_studio(self, studio_name: str) -> Dict:
        """
        Delete a studio from the Studio collection by studio name
        """
        try:
            log.info(f"Deleting studio: {studio_name}")
            
            # Get database collection directly
            col = mydb[self.studio_col]
            
            # Check if studio exists
            existing_studio = col.find_one({"studio": studio_name})
            if not existing_studio:
                log.warning(f"Studio not found: {studio_name}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Studio with name '{studio_name}' not found"
                )
            
            # Delete the studio
            result = col.delete_one({"studio": studio_name})
            
            if result.deleted_count > 0:
                log.info(f"Successfully deleted studio: {studio_name}")
                return {
                    "message": "Studio deleted successfully",
                    "studio": studio_name
                }
            else:
                log.error(f"Failed to delete studio: {studio_name}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete studio"
                )
                
        except HTTPException:
            # Re-raise HTTPException as-is
            raise
        except Exception as e:
            log.error(f"Error deleting studio {studio_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete studio: {str(e)}"
            )