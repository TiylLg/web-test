import logging
import os
from pydantic import Field
from pydantic_settings import BaseSettings


log = logging.getLogger("asyncio")


class Settings(BaseSettings):
    mongodb_host: str = Field(env="MONGODB_HOST")
    mongodb_port: int = Field(env="MONGODB_PORT")
    mongodb_username: str = Field(env="MONGODB_USERNAME")
    mongodb_password: str = Field(env="MONGODB_PASSWORD")

    mongodb_auth_source: str = Field(env="MONGODB_AUTH_SOURCE", default="admin")
    mongodb_database: str = Field(env="MONGODB_DATABASE", default="WebsiteDB")
    mongodb_auth_mechanism: str = Field(env="MONGODB_AUTH_MECHANISM", default="SCRAM-SHA-1")
    auth_db: str = Field(env="AUTH_DB", default="WebsiteDB")
    auth_col: str = Field(env="AUTH_COL", default="Account")
    verify_col: str = Field(env="VERIFY_COL", default="Verification")
    payment_col: str = Field(env="PAYMENT_COL", default="Payment")
    product_col: str = Field(env="PRODUCT_COL", default="Product")
    studio_col: str = Field(env="STUDIO_COL", default="Studio")
    order_col: str = Field(env="ORDER_COL", default="Order")
    order_history_col: str = Field(env="ORDER_HISTORY_COL", default="OrderHistory")
    mongodb_retry_writes: bool = Field(env="MONGODB_RETRY_WRITES", default=False)
    mongodb_ssl: bool = Field(env="MONGODB_SSL", default=True)
    mongodb_tlsallowinvalidhostnames: bool = Field(env="MONGODB_TLS_ALLOW_INVALID_HOSTNAME", default=True)

    jwt_secret: str = Field(env="JWT_SECRET", default="your-secret-key")
    jwt_algorithm: str = Field(env="JWT_ALGORITHM", default="HS256")
    
    # Stripe configuration
    stripe_api_key: str = Field(env="STRIPE_API_KEY", default="")
    stripe_public_key: str = Field(env="STRIPE_PUBLIC_KEY", default="")
    
    # PayPal configuration
    paypal_client_id: str = Field(env="PAYPAL_CLIENT_ID", default="")
    paypal_secret: str = Field(env="PAYPAL_SECRET", default="")
    paypal_mode: str = Field(env="PAYPAL_MODE", default="sandbox")  # "sandbox" or "live"
    
    # Dropship export password
    dropship_password: str = Field(env="DROPSHIP_PASSWORD")


settings = Settings()

module_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(module_dir)
