import logging
from typing import Optional

from fastapi import APIRouter, Depends, status, Query, Header, HTTPException

from app.config.Config import settings
from app.controller.productcontroller import ProductController
from app.schema.ProductSchema import AddProductRequest, DeleteProductRequest, AddStudioRequest, DeleteStudioRequest

log = logging.getLogger("asyncio")
router = APIRouter()

@router.get(
    "/get-products",
    summary="Get products by studio",
    description="Get products filtered by studio name",
    status_code=status.HTTP_200_OK,
)
async def get_products(studio: str = Query(..., description="Studio name")):
    """
    Get products by studio name from Product collection
    Filters on studio field - works for any studio including 'generic'
    """
    log.info(f"Getting products for studio: {studio}")
    
    product_controller = ProductController()
    products = product_controller.get_products(studio)
    
    log.info(f"Returning {len(products)} products for studio: {studio}")
    return {"products": products}

@router.get(
    "/get-studios",
    summary="Get all studios",
    description="Get list of all available studios",
    status_code=status.HTTP_200_OK,
)
async def get_studios():
    """
    Get all available studios from Studio collection
    Returns studio names and descriptions
    """
    log.info("Getting all studios")
    
    product_controller = ProductController()
    studios = product_controller.get_studios()
    
    log.info(f"Returning {len(studios)} studios")
    return {"studios": studios}

@router.get(
    "/get-studio",
    summary="Get studio information",
    description="Get specific studio information including description",
    status_code=status.HTTP_200_OK,
)
async def get_studio(studio: str = Query(..., description="Studio name")):
    """
    Get specific studio information by name
    Returns studio name and description
    """
    log.info(f"Getting studio info for: {studio}")
    
    product_controller = ProductController()
    studio_info = product_controller.get_studio_by_name(studio)
    
    if studio_info:
        log.info(f"Returning studio info for: {studio}")
        return {"studio": studio_info}
    else:
        log.warning(f"Studio not found: {studio}")
        return {"studio": None}


@router.post(
    "/add-product",
    summary="Add a new product",
    description="Add a new product to the Product collection (requires dropship password)",
    status_code=status.HTTP_201_CREATED,
)
async def add_product(
    request: AddProductRequest,
    password: str = Header(..., alias="X-Dropship-Password")
):
    """
    Add a new product to the Product collection.
    
    Authentication: Uses password header (X-Dropship-Password) instead of JWT.
    
    Args:
        request: Product details (productName, price, details, studio)
        password: Password from X-Dropship-Password header
        
    Returns:
        Success message with product details
        
    Raises:
        401: Invalid password
        409: Product already exists
    """
    log.info(f"add-product endpoint called for: {request.productName}")
    
    # Validate password
    if password != settings.dropship_password:
        log.warning(f"Invalid dropship password attempt for add-product")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Use ProductController to add the product
    product_controller = ProductController()
    result = product_controller.add_product(
        product_name=request.productName,
        price=request.price,
        details=request.details,
        studio=request.studio
    )
    
    log.info(f"Product added successfully: {request.productName}")
    return result


@router.delete(
    "/delete-product",
    summary="Delete a product",
    description="Delete a product from the Product collection (requires dropship password)",
    status_code=status.HTTP_200_OK,
)
async def delete_product(
    request: DeleteProductRequest,
    password: str = Header(..., alias="X-Dropship-Password")
):
    """
    Delete a product from the Product collection by productName.
    
    Authentication: Uses password header (X-Dropship-Password) instead of JWT.
    
    Args:
        request: Product name to delete
        password: Password from X-Dropship-Password header
        
    Returns:
        Success message with deleted product name
        
    Raises:
        401: Invalid password
        404: Product not found
    """
    log.info(f"delete-product endpoint called for: {request.productName}")
    
    # Validate password
    if password != settings.dropship_password:
        log.warning(f"Invalid dropship password attempt for delete-product")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Use ProductController to delete the product
    product_controller = ProductController()
    result = product_controller.delete_product(product_name=request.productName)
    
    log.info(f"Product deleted successfully: {request.productName}")
    return result


@router.post(
    "/add-studio",
    summary="Add a new studio",
    description="Add a new studio to the Studio collection (requires dropship password)",
    status_code=status.HTTP_201_CREATED,
)
async def add_studio(
    request: AddStudioRequest,
    password: str = Header(..., alias="X-Dropship-Password")
):
    """
    Add a new studio to the Studio collection.
    
    Authentication: Uses password header (X-Dropship-Password) instead of JWT.
    
    Args:
        request: Studio details (studio, description)
        password: Password from X-Dropship-Password header
        
    Returns:
        Success message with studio details
        
    Raises:
        401: Invalid password
        409: Studio already exists
    """
    log.info(f"add-studio endpoint called for: {request.studio}")
    
    # Validate password
    if password != settings.dropship_password:
        log.warning(f"Invalid dropship password attempt for add-studio")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Use ProductController to add the studio
    product_controller = ProductController()
    result = product_controller.add_studio(
        studio_name=request.studio,
        description=request.description
    )
    
    log.info(f"Studio added successfully: {request.studio}")
    return result


@router.delete(
    "/delete-studio",
    summary="Delete a studio",
    description="Delete a studio from the Studio collection (requires dropship password)",
    status_code=status.HTTP_200_OK,
)
async def delete_studio(
    request: DeleteStudioRequest,
    password: str = Header(..., alias="X-Dropship-Password")
):
    """
    Delete a studio from the Studio collection by studio name.
    
    Authentication: Uses password header (X-Dropship-Password) instead of JWT.
    
    Args:
        request: Studio name to delete
        password: Password from X-Dropship-Password header
        
    Returns:
        Success message with deleted studio name
        
    Raises:
        401: Invalid password
        404: Studio not found
    """
    log.info(f"delete-studio endpoint called for: {request.studio}")
    
    # Validate password
    if password != settings.dropship_password:
        log.warning(f"Invalid dropship password attempt for delete-studio")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Use ProductController to delete the studio
    product_controller = ProductController()
    result = product_controller.delete_studio(studio_name=request.studio)
    
    log.info(f"Studio deleted successfully: {request.studio}")
    return result
