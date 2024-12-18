# Python standard library
from datetime import timedelta
import logging
from sentry_sdk import capture_exception

# Third-party imports
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Local application imports
from src.auth.services import (
    authenticate_user_token,
    create_access_token,
    check_user_password_is_correct,
    pwd_context
)
from src.dependencies import session_opener
from src.models import User
from src.schemas import UserAuthSchema

router = APIRouter()

@router.post("/api/v1/users/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), database: Session = Depends(session_opener)
):
    """login"""
    try:
        user = check_user_password_is_correct(database, form_data.username, form_data.password)
        TOKEN_EXPIRE_MINUTES = 30
        access_token = create_access_token(
            data={"sub": str(user.username)}, expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logging.error("Login error: %s", e)
        capture_exception(e)

@router.post("/api/v1/users/register")
def create_user(user: UserAuthSchema, database: Session = Depends(session_opener)):
    """create user"""
    try:
        hashed_password = pwd_context.hash(user.password)
        new_user = User(username=user.username, hashed_password=hashed_password)
        database.add(new_user)
        database.commit()
        database.refresh(new_user)
        return new_user
    except Exception as e:
        logging.error("User creation error: %s", e)
        capture_exception(e)

@router.get("/api/v1/users/me")
def read_users_me(user=Depends(authenticate_user_token)):
    try:
        return {"username": user.username}
    except Exception as e:
        logging.error("Read user error: %s", e)
        capture_exception(e)
