import jwt
from datetime import datetime, timedelta
from app.config import settings
from logging import getLogger
logger = getLogger(__name__)

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720  # 12 Hours
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None

        return payload
    except jwt.PyJWTError:
        return None


def verify_token(token: str):
    try:
        if jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]):
            return True
        else:
            logger.error(f"Invalid token: {token} ")
            return False
    except jwt.ExpiredSignatureError:
        logger.info(f"JWT token expired")
        return False


def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None

        return payload
    except jwt.PyJWTError:
        return None