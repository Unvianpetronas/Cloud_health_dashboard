from cryptography.fernet import Fernet
from app.config import settings
import base64
import logging

logger = logging.getLogger(__name__)

def get_fernet():
    try:
        key = settings.ENCRYPTION_KEY
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key)
    except Exception as e:
        logger.error(f"Invalid ENCRYPTION_KEY: {e}")
        raise ValueError(f"Invalid ENCRYPTION_KEY: {e}")

try:
    fernet = get_fernet()
except Exception as e:
    logger.error(f"Failed to initialize encryption: {e}")
    raise

def encrypt_credentials(access_key: str, secret_key: str) -> str:
    try:
        credentials_str = f"{access_key}:{secret_key}"
        encrypted_creds = fernet.encrypt(credentials_str.encode())
        return base64.b64encode(encrypted_creds).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise ValueError(f"Encryption failed: {e}")

def decrypt_credentials(encrypted_creds: str) -> tuple[str, str]:
    try:
        encrypted_bytes = base64.b64decode(encrypted_creds.encode())
        decrypted = fernet.decrypt(encrypted_bytes).decode()
        access_key, secret_key = decrypted.split(":", 1)
        return access_key, secret_key
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError("Invalid or corrupted encrypted credentials")