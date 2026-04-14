from typing import List
import re
from pydantic import validator
from app.schema.base import CamelCaseModel


class AuthSchema(CamelCaseModel):
    email: str
    password: str

class ResetPasswordSchema(CamelCaseModel):
    password: str

    @validator("password")
    def validate_password(cls, value):
        if len(value) > 30:
            raise ValueError("Password must be cannot be more than 30 characters.")
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("Password must contain at least one letter and one number.")
        return value

class SignupSchema(CamelCaseModel):
    email: str
    password: str
    user_name: str


    @validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("Password must contain at least one letter and one number.")
        return value

    @validator("email")
    def validate_email(cls, value):
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, value):
            raise ValueError("Invalid email format.")
        return value
