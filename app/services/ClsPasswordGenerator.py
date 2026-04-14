import hashlib
import uuid


class PasswordGenerator:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.encoded_password = self.encode_password(password)
        self.session_id = str(uuid.uuid4())

    def encode_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.encode_password(password) == hashed_password
