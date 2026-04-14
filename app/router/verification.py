import logging
from fastapi import APIRouter, status
from app.controller.verificationcontroller import VerificationController

log = logging.getLogger("asyncio")
router = APIRouter()


@router.post(
    "/send-verification",
    summary="Send Verification Code",
    description="Send verification code to email",
    status_code=status.HTTP_200_OK,
)
def send_verification_code(email: str):
    log.info(f"Sending verification code to {email}")
    
    verification_controller = VerificationController(email.lower())
    result = verification_controller.send_verification_code()
    
    log.info("Verification code sent successfully")
    return result


@router.post(
    "/verify-code",
    summary="Verify Code",
    description="Verify the provided verification code",
    status_code=status.HTTP_200_OK,
)
def verify_code(email: str, verification_code: str):
    log.info(f"Verifying code for {email}")
    
    verification_controller = VerificationController(email.lower())
    result = verification_controller.verify(verification_code)
    
    log.info("Code verified successfully")
    return result
