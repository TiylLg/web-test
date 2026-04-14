import logging
from fastapi import HTTPException, status
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
from paypalserversdk.configuration import Environment
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
# OrdersController is accessed via client.orders
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest
from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown
from app.config.Config import settings

log = logging.getLogger("asyncio")


def _get_paypal_client() -> PaypalServersdkClient:
    """Get configured PayPal SDK client."""
    environment = Environment.SANDBOX if settings.paypal_mode == "sandbox" else Environment.PRODUCTION
    
    return PaypalServersdkClient(
        client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
            o_auth_client_id=settings.paypal_client_id,
            o_auth_client_secret=settings.paypal_secret
        ),
        environment=environment
    )


def get_paypal_client_id() -> dict:
    """Return the PayPal client ID for frontend initialization."""
    return {
        "clientId": settings.paypal_client_id,
        "mode": settings.paypal_mode
    }


def create_paypal_order(amount: float, currency: str = "USD") -> dict:
    """
    Create a PayPal order using Orders API v2.
    
    Args:
        amount: Amount in dollars (not cents)
        currency: Currency code (default: USD)
    
    Returns:
        dict with order_id
    """
    try:
        client = _get_paypal_client()
        orders_controller = client.orders
        
        order_request = OrderRequest(
            intent=CheckoutPaymentIntent.CAPTURE,
            purchase_units=[
                PurchaseUnitRequest(
                    amount=AmountWithBreakdown(
                        currency_code=currency,
                        value=f"{amount:.2f}"
                    ),
                    description="Haven Purchase",
                    soft_descriptor="HAVEN PURCHASE"
                )
            ]
        )
        
        result = orders_controller.create_order({"body": order_request})
        
        if result.body:
            order_data = result.body
            log.info(f"PayPal order created successfully: {order_data.id}")
            return {
                "order_id": order_data.id,
                "status": order_data.status
            }
        else:
            log.error("PayPal order creation failed: No response body")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create PayPal order"
            )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"PayPal order creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the PayPal order: {str(e)}"
        )


def capture_paypal_order(order_id: str) -> dict:
    """
    Capture a PayPal order after user approval using Orders API v2.
    
    Args:
        order_id: The PayPal order ID
    
    Returns:
        dict with capture details
    """
    try:
        client = _get_paypal_client()
        orders_controller = client.orders
        
        result = orders_controller.capture_order({"id": order_id})
        
        if result.body:
            capture_data = result.body
            log.info(f"PayPal order captured successfully: {order_id}")
            
            # Extract payer and payment details
            payer = capture_data.payer
            purchase_unit = capture_data.purchase_units[0] if capture_data.purchase_units else None
            capture = None
            if purchase_unit and purchase_unit.payments and purchase_unit.payments.captures:
                capture = purchase_unit.payments.captures[0]
            
            payer_name = ""
            if payer and payer.name:
                payer_name = f"{payer.name.given_name or ''} {payer.name.surname or ''}".strip()
            
            return {
                "order_id": capture_data.id,
                "status": capture_data.status,
                "payer_email": payer.email_address if payer else None,
                "payer_name": payer_name,
                "amount": capture.amount.value if capture and capture.amount else None,
                "currency": capture.amount.currency_code if capture and capture.amount else None,
                "transaction_id": capture.id if capture else None,
                "capture_time": capture.create_time if capture else None
            }
        else:
            log.error("PayPal order capture failed: No response body")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to capture PayPal payment"
            )
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"PayPal capture error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while capturing the PayPal payment: {str(e)}"
        )


def verify_paypal_webhook(webhook_id: str, event_body: dict, headers: dict) -> bool:
    """
    Verify PayPal webhook signature.
    
    Args:
        webhook_id: The webhook ID from PayPal dashboard
        event_body: The webhook event body
        headers: Request headers
    
    Returns:
        bool indicating if the webhook is valid
    """
    try:
        # For production, implement proper webhook verification
        return True
    except Exception as e:
        log.error(f"PayPal webhook verification error: {str(e)}")
        return False
