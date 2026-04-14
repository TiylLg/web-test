from pydantic import BaseModel, Field


class AddProductRequest(BaseModel):
    productName: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price", gt=0)
    details: str = Field(..., description="Product details")
    studio: str = Field(..., description="Studio name")


class DeleteProductRequest(BaseModel):
    productName: str = Field(..., description="Product name to delete")


class AddStudioRequest(BaseModel):
    studio: str = Field(..., description="Studio name")
    description: str = Field(..., description="Studio description")


class DeleteStudioRequest(BaseModel):
    studio: str = Field(..., description="Studio name to delete")

