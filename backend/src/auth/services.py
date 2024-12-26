# Python standard library
from datetime import datetime, timedelta

# Third-party libraries
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

# Local imports
from src.auth.config import JWT_SECRET_KEY, DEFAULT_TOKEN_EXPIRE_MINUTES
from src.dependencies import session_opener
from src.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def check_user_password_is_correct(database, username, password):
    user = database.query(User).filter(User.username == username).first()
    if not verify_password(password, user.hashed_password):
        return False
    return user

def authenticate_user_token(
    token = Depends(oauth2_scheme),
    database = Depends(session_opener)
):
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    return database.query(User).filter(User.username == payload.get("sub")).first()


def create_access_token(data, expires_delta=None):
    """create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=DEFAULT_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt
