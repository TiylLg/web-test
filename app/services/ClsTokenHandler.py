import time
from fastapi import HTTPException
import jwt
from app.config.Config import settings


class TokenHandler:
    def __init__(self):
        self.jwt_secret = settings.jwt_secret
        self.jwt_algorithm = settings.jwt_algorithm
        self.duration = 900  # 15 minutes

    def signJWT(self, email: str, session_id: str):
        payload = {
            "Email": email,
            "expires": time.time() + self.duration,
            "SessionID": session_id
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token

    def decodeJWT(self, token: str):
        try:
            decoded_token = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return decoded_token if decoded_token["expires"] >= time.time() else None
        except:
            return None


token_handler = TokenHandler()
