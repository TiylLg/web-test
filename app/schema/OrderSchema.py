from typing import List
from pydantic import BaseModel


class OrderDetail(BaseModel):
    productName: str
    quantity: int
    price: float


class ShippingAddress(BaseModel):
    fullName: str
    addressLine1: str
    addressLine2: str = ""
    city: str
    state: str
    zipCode: str
    country: str
    phone: str


class AddOrderRequest(BaseModel):
    date: str
    status: str = "preparing"
    detail: List[OrderDetail]
    shippingAddress: ShippingAddress

