import logging
import os
from datetime import datetime
from importlib import import_module
from typing import List

from fastapi import APIRouter, Depends, status, HTTPException, Header

from app.config.Config import module_dir, settings
from app.controller.accountcontroller import AccountController
from app.controller.ordercontroller import OrderController
from app.controller.dropshipcontroller import DropshipController
from app.schema.OrderSchema import OrderDetail, ShippingAddress, AddOrderRequest
from app.services import DBConn
from app.services.stripeservice import (
    get_strip_public_key,
    create_customer,
    create_payment_intent,
    attach_payment_to_customer,
    charge_payment_method,
    retrieve_payment_method,
    get_payment_history
)
from app.services.paypalservice import (
    get_paypal_client_id,
    create_paypal_order,
    capture_paypal_order
)
from app.util.ClsJwtBearer import JWTBearer, get_token_user

log = logging.getLogger("asyncio")
router = APIRouter()


@router.get(
    "/get-public-key",
    dependencies=[Depends(JWTBearer())],
    summary="get-public-key",
    description="get-public-key",
    status_code=status.HTTP_200_OK,
)
async def get_public_key():
    return get_strip_public_key()


# ===================== PayPal Endpoints =====================

@router.get(
    "/paypal/client-id",
    dependencies=[Depends(JWTBearer())],
    summary="Get PayPal client ID",
    description="Get PayPal client ID for frontend initialization",
    status_code=status.HTTP_200_OK,
)
async def get_paypal_client():
    return get_paypal_client_id()


@router.post(
    "/paypal/create-order",
    dependencies=[Depends(JWTBearer())],
    summary="Create PayPal order",
    description="Create a PayPal order for checkout",
    status_code=status.HTTP_200_OK,
)
async def paypal_create_order(
        amount: float,
        currency: str = "USD",
        token=Depends((JWTBearer()))
):
    log.info(f"Creating PayPal order for amount: {amount} {currency}")
    return create_paypal_order(amount, currency)


@router.post(
    "/paypal/capture-order",
    dependencies=[Depends(JWTBearer())],
    summary="Capture PayPal order",
    description="Capture/execute a PayPal payment after user approval",
    status_code=status.HTTP_200_OK,
)
async def paypal_capture_order(
        order_id: str,
        token=Depends((JWTBearer()))
):
    log.info(f"Capturing PayPal order: {order_id}")
    return capture_paypal_order(order_id)

@router.post(
    "/create-payment-intent",
    dependencies=[Depends(JWTBearer())],
    summary="charge payment method",
    description="charge payment method",
    status_code=status.HTTP_200_OK,
)
async def payment_intent(
        amount: int,
        currency: str = "usd",
        token=Depends((JWTBearer()))
):
    log.info("create-payment-intent")

    email = get_token_user(token)
    
    # Get or create payment record
    payment_record = DBConn.aggregate(
        collection=settings.payment_col,
        match_query={"email": email},
        project_fields=["email", "stripeId", "stripeSecret"]
    )
    
    if not payment_record:
        # Create new customer and payment record
        stripe_customer_id = create_customer(email)
        payment_data = {
            "email": email,
            "stripeId": stripe_customer_id,
            "stripeSecret": "",
            "paymentMethod": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        DBConn.insert_doc(
            collection=settings.payment_col,
            payload=payment_data
        )
        customer_id = stripe_customer_id
    else:
        customer_id = payment_record["stripeId"]
    
    # Create payment intent
    response = create_payment_intent(amount, currency, customer_id)
    
    # Store payment intent in Payment collection
    DBConn.upsert_doc(
        collection=settings.payment_col,
        match_query={"email": email},
        update_data={
            "stripeSecret": response["clientSecret"],
            "updated_at": datetime.now()
        }
    )

    log.info("create-payment-intent complete")

    return response

@router.post(
    "/save-payment-method",
    dependencies=[Depends(JWTBearer())],
    summary="save payment method",
    description="save payment method",
    status_code=status.HTTP_200_OK,
)
async def save_payment_method(
        paymentMethodId: str,
        token=Depends((JWTBearer()))
):
    log.info("save payment method")
    email = get_token_user(token)
    
    # Get payment record
    payment_record = DBConn.aggregate(
        collection=settings.payment_col,
        match_query={"email": email},
        project_fields=["email", "stripeId", "paymentMethod"]
    )
    
    if not payment_record:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    customer_id = payment_record["stripeId"]
    
    # Attach payment method to Stripe customer
    attach_payment_to_customer(paymentMethodId, customer_id)
    
    # Get payment method details
    pm_details = retrieve_payment_method(paymentMethodId)
    
    # Add to payment methods list in Payment collection
    current_methods = payment_record.get("paymentMethod", [])
    
    # Check if payment method already exists
    if not any(method.get("payment_method_id") == paymentMethodId for method in current_methods):
        current_methods.append({
            "payment_method_id": paymentMethodId,
            "brand": pm_details["brand"],
            "last4": pm_details["last4"],
            "exp_month": pm_details["exp_month"],
            "exp_year": pm_details["exp_year"],
            "created_at": datetime.now()
        })
        
        DBConn.upsert_doc(
            collection=settings.payment_col,
            match_query={"email": email},
            update_data={
                "paymentMethod": current_methods,
                "updated_at": datetime.now()
            }
        )
    
    log.info("save payment method complete")

@router.delete(
    "/delete-payment-method",
    dependencies=[Depends(JWTBearer())],
    summary="delete payment method",
    description="delete payment method",
    status_code=status.HTTP_200_OK,
)
async def delete_payment_method(
        paymentMethodId: str,
        token=Depends((JWTBearer()))
):
    log.info("delete payment method")
    email = get_token_user(token)
    
    # Get payment record
    payment_record = DBConn.aggregate(
        collection=settings.payment_col,
        match_query={"email": email},
        project_fields=["email", "paymentMethod"]
    )
    
    if payment_record:
        # Remove from payment methods list
        current_methods = payment_record.get("paymentMethod", [])
        updated_methods = [
            method for method in current_methods 
            if method.get("payment_method_id") != paymentMethodId
        ]
        
        DBConn.upsert_doc(
            collection=settings.payment_col,
            match_query={"email": email},
            update_data={
                "paymentMethod": updated_methods,
                "updated_at": datetime.now()
            }
        )
    
    log.info("delete payment method complete")

@router.post(
    "/charge-stored-method",
    dependencies=[Depends(JWTBearer())],
    summary="charge stored method",
    description="charge stored method",
    status_code=status.HTTP_200_OK,
)
async def charge_payment(
        paymentMethodId: str,
        amount: int,
        currency: str = "usd",
        token=Depends((JWTBearer()))
):
    log.info("charge payment method")
    email = get_token_user(token)
    
    # Get payment record
    payment_record = DBConn.aggregate(
        collection=settings.payment_col,
        match_query={"email": email},
        project_fields=["email", "stripeId", "paymentMethod"]
    )
    
    if not payment_record:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    customer_id = payment_record["stripeId"]
    
    # Check if payment method exists in our records
    payment_methods = payment_record.get("paymentMethod", [])
    if not any(method.get("payment_method_id") == paymentMethodId for method in payment_methods):
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    # Charge the payment method (no credit storage, on-demand payment)
    success = charge_payment_method(amount, currency, customer_id, paymentMethodId)
    
    log.info("charge payment method complete")
    return {"success": success, "amount": amount, "currency": currency}

@router.get(
    "/get-payment-methods",
    dependencies=[Depends(JWTBearer())],
    summary="fetch stored method",
    description="fetch stored method",
    status_code=status.HTTP_200_OK,
)
async def get_payment_methods(
        token=Depends((JWTBearer()))
):
    log.info("get payment method")
    email = get_token_user(token)
    
    # Get payment methods from Payment collection
    payment_record = DBConn.aggregate(
        collection=settings.payment_col,
        match_query={"email": email},
        project_fields=["email", "paymentMethod"]
    )
    
    if not payment_record:
        return {"payment_methods": []}
    
    payment_methods = payment_record.get("paymentMethod", [])
    
    log.info("get payment method complete")
    return {"payment_methods": payment_methods}

@router.get(
    "/get-payment-history",
    dependencies=[Depends(JWTBearer())],
    summary="fetch payment history",
    description="fetch payment history",
    status_code=status.HTTP_200_OK,
)
async def get_payment_history_endpoint(
        token=Depends((JWTBearer()))
):
    log.info("get payment history")
    email = get_token_user(token)
    
    # Get customer ID from Payment collection
    payment_record = DBConn.aggregate(
        collection=settings.payment_col,
        match_query={"email": email},
        project_fields=["email", "stripeId"]
    )
    
    if not payment_record:
        return {"payment_history": []}
    
    customer_id = payment_record["stripeId"]
    response = get_payment_history(customer_id)
    
    log.info("get payment history complete")
    return {"payment_history": response}

@router.post(
    "/add-order",
    dependencies=[Depends(JWTBearer())],
    summary="add order to history",
    description="add order to order history collection",
    status_code=status.HTTP_200_OK,
)
async def add_order(
        order_data: AddOrderRequest,
        token=Depends((JWTBearer()))
):
    log.info("add-order endpoint called")
    email = get_token_user(token)
    
    # Use OrderController to handle the business logic
    controller = OrderController(email)
    return controller.add_order(order_data)

@router.get(
    "/get-order-history",
    dependencies=[Depends(JWTBearer())],
    summary="get order history",
    description="get all historical orders for the user",
    status_code=status.HTTP_200_OK,
)
async def get_order_history(
        token=Depends((JWTBearer()))
):
    log.info("get-order-history endpoint called")
    email = get_token_user(token)
    
    # Use OrderController to handle the business logic
    controller = OrderController(email)
    return controller.get_order_history()


@router.get(
    "/export-orders",
    summary="Export orders for dropship distributor",
    description="Export all orders for a specific date in CSV format for dropship processing",
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "Returns a CSV file with order data",
        }
    }
)
async def export_orders_for_dropship(
        date: str,
        password: str = Header(..., alias="X-Dropship-Password")
):
    """
    Export orders for a specific date in CSV format for dropship distributor.
    
    Authentication: Uses password header (X-Dropship-Password) instead of JWT.
    
    Args:
        date: Date in YYYY-MM-DD format
        password: Password from X-Dropship-Password header
        
    Returns:
        CSV file download with order data
    """
    log.info(f"export-orders endpoint called for date: {date}")
    
    # Validate password
    if password != settings.dropship_password:
        log.warning(f"Invalid dropship password attempt")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Use DropshipController to handle the business logic
    controller = DropshipController()
    return controller.export_orders_for_date(date)
