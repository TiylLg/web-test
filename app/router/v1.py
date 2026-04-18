from fastapi import APIRouter
from . import(
    account,
    verification,
    payment,
    products,
    health,
    images
)

router = APIRouter(prefix='/v1')

router.include_router(
    account.router,
    tags=['Account Management']
)

# router.include_router(
#     health.router,
#     tags=['Health']
# )

router.include_router(
    verification.router,
    tags=['Verification']
)

router.include_router(
    payment.router,
    tags=['Payment Management']
)

# router.include_router(
#     products.router,
#     tags=['Products & Studios']
# )

# router.include_router(
#     images.router
# )