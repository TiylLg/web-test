from app.services.ClsPasswordGenerator import PasswordGenerator
from fastapi import HTTPException
import hashlib
from app.services.ClsTokenHandler import token_handler
from app.schema.AuthSchema import SignupSchema
from app.services import DBConn
from datetime import datetime
from app.config.Config import settings
import uuid


class AccountController:
    def __init__(self, email: str, password: str):
        self.client = PasswordGenerator(email, password)
        self.mycol = settings.auth_col

    def validate_signup(self, schema):
        email_list = DBConn.aggregate(
                        collection=self.mycol,
                        match_query={"Email": schema.email},
                        project_fields=['Email']
                    )
        if email_list:
            raise HTTPException(status_code=403, detail="Email already exist")


    def sign_up(self, schema: SignupSchema):
        self.validate_signup(schema)

        try:
            payload = {
                "Email": self.client.email,
                "Password": self.client.encoded_password,
                "Username": schema.user_name,
                "CreatedAt": datetime.now(),
                "SessionID": self.client.session_id,
            }

            DBConn.insert_doc(
                collection=self.mycol,
                payload=payload
            )

            token = token_handler.signJWT(self.client.email, self.client.session_id)
            return {'detail': 'Account created successfully', 'token': token}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")

    def log_in(self):
        user_data = DBConn.aggregate(
            collection=self.mycol,
            match_query={"Email": self.client.email},
            project_fields=['Email', 'Password', 'SessionID']
        )

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        if not self.client.verify_password(self.client.password, user_data['Password']):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Update session ID
        new_session_id = str(uuid.uuid4())
        DBConn.upsert_doc(
            collection=self.mycol,
            match_query={"Email": self.client.email},
            update_data={"SessionID": new_session_id, "LastLogin": datetime.now()}
        )

        token = token_handler.signJWT(self.client.email, new_session_id)
        return token

    def reset_password(self):
        user_data = DBConn.aggregate(
            collection=self.mycol,
            match_query={"Email": self.client.email},
            project_fields=['Email']
        )

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        DBConn.upsert_doc(
            collection=self.mycol,
            match_query={"Email": self.client.email},
            update_data={"Password": self.client.encoded_password, "UpdatedAt": datetime.now()}
        )

        return {'detail': 'Password reset successful'}

    def get_new_token(self):
        user_data = DBConn.aggregate(
            collection=self.mycol,
            match_query={"Email": self.client.email},
            project_fields=['Email', 'SessionID']
        )

        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")


        # Generate new session ID
        new_session_id = str(uuid.uuid4())
        DBConn.upsert_doc(
            collection=self.mycol,
            match_query={"Email": self.client.email},
            update_data={"SessionID": new_session_id}
        )

        token = token_handler.signJWT(self.client.email, new_session_id)
        return {'detail': token}

    def logout(self):
        DBConn.upsert_doc(
            collection=self.mycol,
            match_query={"Email": self.client.email},
            update_data={"SessionID": "", "LogoutAt": datetime.now()}
        )
        return {'detail': 'Logout successful'}
