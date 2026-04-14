from fastapi import HTTPException
from app.services import DBConn
from app.config.Config import settings
from datetime import datetime
import uuid
import random
import string


class VerificationController:
    def __init__(self, email: str):
        self.email = email
        self.verify_col = settings.verify_col

    def generate_verification_code(self) -> str:
        """Generate a 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))

    def send_verification_code(self):
        """Generate and store verification code"""
        verification_code = self.generate_verification_code()
        
        payload = {
            "Email": self.email,
            "VerificationCode": verification_code,
            "CreatedAt": datetime.now(),
            "IsUsed": False,
            "ExpiresAt": datetime.now().timestamp() + 300  # 5 minutes
        }

        DBConn.upsert_doc(
            collection=self.verify_col,
            match_query={"Email": self.email},
            update_data=payload
        )

        # In a real application, you would send this via email/SMS
        # For now, we'll return it in the response (not recommended for production)
        return {'detail': f'Verification code sent', 'code': verification_code}

    def verify(self, verification_code: str):
        """Verify the provided verification code"""
        verification_data = DBConn.aggregate(
            collection=self.verify_col,
            match_query={"Email": self.email},
            project_fields=['VerificationCode', 'IsUsed', 'ExpiresAt']
        )

        if not verification_data:
            raise HTTPException(status_code=404, detail="No verification code found for this email")

        if verification_data.get('IsUsed', False):
            raise HTTPException(status_code=400, detail="Verification code already used")

        if verification_data.get('ExpiresAt', 0) < datetime.now().timestamp():
            raise HTTPException(status_code=400, detail="Verification code expired")

        if verification_data['VerificationCode'] != verification_code:
            raise HTTPException(status_code=400, detail="Invalid verification code")

        # Mark as used
        DBConn.upsert_doc(
            collection=self.verify_col,
            match_query={"Email": self.email},
            update_data={"IsUsed": True, "VerifiedAt": datetime.now()}
        )

        return {'detail': 'Verification successful'}
