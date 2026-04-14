from fastapi import HTTPException, status
import stripe
from app.config.Config import settings
from datetime import datetime, timedelta

stripe.api_key = settings.stripe_api_key

def create_customer(email: str) -> str:
    customer = stripe.Customer.create(email=email)
    return customer.id

def attach_payment_to_customer(payment_id: str, customer_id: str):
    response = stripe.PaymentMethod.attach(
        payment_method=payment_id,
        customer=customer_id,
    )
    print(response)

def charge_payment_method(amount: int, currency: str, customer_id: str, payment_id: str):
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,  # Amount in cents
            currency=currency,
            customer=customer_id,
            payment_method=payment_id,
            off_session=True,
            confirm=True,
            description="Haven Purchase",
            statement_descriptor="HAVEN PURCHASE",
        )
        if payment_intent.status == "succeeded":
            return True
        else:
            return False
    except Exception as e:
        raise e


def create_payment_intent(amount: int, currency: str, customer_id: str) -> dict:
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            customer=customer_id,
            automatic_payment_methods={
                "enabled": True,
                "allow_redirects": "never"
            },
            setup_future_usage="off_session",
            description="Haven Purchase",
            statement_descriptor="HAVEN PURCHASE",
        )
        return {
            "clientSecret": payment_intent.client_secret,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency,
        }
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the payment intent",
        )

def check_payment_status(client_secret):
    try:
        payment_intent_id = client_secret.split('_secret')[0]
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        print(payment_intent['status'])
        if payment_intent['status'] == 'succeeded':
            return True
        else:
            return False
    except Exception as e:
        print(f"Error retrieving PaymentIntent: {e}")
        return False

def get_strip_public_key() -> dict:
    return {
        'publishableKey': settings.stripe_public_key
    }

def retrieve_payment_method(payment_id: str):
    try:
        payment_method = stripe.PaymentMethod.retrieve(payment_id)
        return {
            "id": payment_method.id,
            "brand": payment_method.card.brand,
            "last4": payment_method.card.last4,
            "exp_month": payment_method.card.exp_month,
            "exp_year": payment_method.card.exp_year,
        }
    except stripe.error.StripeError as e:
        print(f"Failed to retrieve PaymentMethod {payment_id}: {e}")


def get_payment_history(client_id, years=3):
    start_date = int((datetime.now() - timedelta(days=365 * years)).timestamp())
    end_date = int(datetime.now().timestamp())

    payment_summary = []

    # Use the PaymentIntent API to fetch payment data
    payment_intents = stripe.PaymentIntent.list(
        customer=client_id,
        created={"gte": start_date, "lte": end_date},
        limit=100,
    )

    # Extract required details
    for pi in payment_intents.auto_paging_iter():
        try:
            if pi['status'] == 'succeeded':
                payment_data = {
                    "payment_time": datetime.fromtimestamp(pi['created']).strftime('%Y-%m-%d'),
                    "amount": pi['amount'] / 100,  # Stripe stores amounts in cents
                }
                payment_summary.append(payment_data)
        except KeyError as e:
            print(f"Skipping a PaymentIntent due to missing field: {e}")

    return payment_summary
