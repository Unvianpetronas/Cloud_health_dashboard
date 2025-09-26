from cryptography.fernet import Fernet
from app.config import settings

# Tạo Fernet instance với key từ config
fernet = Fernet(settings.ENCRYPTION_KEY.encode())

def encrypt_credentials(access_key: str, secret_key: str) -> str:
    """Mã hóa AWS credentials"""
    credentials_str = f"{access_key}:{secret_key}"
    encrypted_creds = fernet.encrypt(credentials_str.encode())
    return encrypted_creds.decode()

def decrypt_credentials(encrypted_creds: str) -> tuple[str, str]:
    """Giải mã AWS credentials"""
    try:
        decrypted = fernet.decrypt(encrypted_creds.encode()).decode()
        access_key, secret_key = decrypted.split(":", 1)
        return access_key, secret_key
    except Exception:
        raise ValueError("Invalid encrypted credentials")