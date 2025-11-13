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
    """
    Decode and validate an access token.

    Args:
        token: JWT access token string

    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            logger.warning("Token type mismatch: expected 'access'")
            return None

        return payload
    except jwt.ExpiredSignatureError:
        logger.info("Access token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid access token")
        return None
    except Exception as e:
        logger.error(f"Error decoding access token: {e}")
        return None


def verify_token(token: str):
    """
    Verify if a token is valid (for any token type).

    Args:
        token: JWT token string

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except jwt.ExpiredSignatureError:
        logger.info("JWT token expired")
        return False
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token")
        return False
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return False


def decode_refresh_token(token: str):
    """
    Decode and validate a refresh token.

    Args:
        token: JWT refresh token string

    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            logger.warning("Token type mismatch: expected 'refresh'")
            return None

        return payload
    except jwt.ExpiredSignatureError:
        logger.info("Refresh token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid refresh token")
        return None
    except Exception as e:
        logger.error(f"Error decoding refresh token: {e}")
        return None