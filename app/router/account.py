import logging
from fastapi import APIRouter, Depends, status
from app.schema.AuthSchema import AuthSchema, SignupSchema, ResetPasswordSchema
from app.controller.accountcontroller import AccountController
from app.controller.verificationcontroller import VerificationController
from app.util.ClsJwtBearer import JWTBearer, get_token_user

log = logging.getLogger("asyncio")
router = APIRouter()


@router.post(
    "/signup",
    summary="Sign Up",
    description="Sign Up",
    status_code=status.HTTP_201_CREATED,
)
def sign_up(schema: SignupSchema):
    log.info("Starting Sign up")

    verification_controller = VerificationController(schema.email.lower())
    account_controller = AccountController(schema.email.lower(), schema.password)

    result = account_controller.sign_up(schema)

    log.info("Server.sign_up finished!")
    return result


@router.post(
    "/login",
    summary="Log in",
    description="Log in and retrieve a jwt token",
    status_code=status.HTTP_200_OK,
)
def get_token(schema: AuthSchema):
    log.info("getting token")

    account_controller = AccountController(schema.email.lower(), schema.password)
    token = account_controller.log_in()

    log.info("Server.get_token finished!")
    return {'detail': token}

@router.post(
    "/reset-password",
    dependencies=[Depends(JWTBearer())],
    summary="Reset Password",
    description="Reset password",
    status_code=status.HTTP_200_OK,
)
def reset_password(
        schema: ResetPasswordSchema,
        token=Depends((JWTBearer()))
):
    log.info("resetting password")
    email = get_token_user(token)

    account_controller = AccountController(email.lower(), schema.password)
    account_controller.reset_password()

    log.info("Server.reset_password finished!")
    return {'detail': 'Reset Successful'}

@router.post(
    "/verify",
    dependencies=[Depends(JWTBearer())],
    summary="verify token",
    description="verify token",
    status_code=status.HTTP_200_OK,
)
def verify_token(token=Depends((JWTBearer()))):
    log.info("token verified")
    email = get_token_user(token)
    return {'detail': 'Token verified', 'email': email}

@router.post(
    "/renew",
    dependencies=[Depends(JWTBearer())],
    summary="renew token",
    description="renew token",
    status_code=status.HTTP_200_OK,
)
def renew_token(token=Depends((JWTBearer()))):
    log.info("renewing token")
    email = get_token_user(token)
    account_controller = AccountController(email.lower(), '')
    token = account_controller.get_new_token()
    return token

@router.post(
    "/logout",
    dependencies=[Depends(JWTBearer())],
    summary="log out",
    description="log out",
    status_code=status.HTTP_200_OK,
)
def logout(token=Depends((JWTBearer()))):
    log.info("Logging out")
    email = get_token_user(token)
    account_controller = AccountController(email.lower(), '')
    account_controller.logout()
    log.info("Log out successful")
    return {'detail': 'Logout successful'}
