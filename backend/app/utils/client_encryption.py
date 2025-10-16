from cryptography.fernet import Fernet
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class ClientEncryption:
    def __init__(self):
        try:
            key = settings.ENCRYPTION_KEY.encode()
            self.cipher = Fernet(key)
        except Exception as e:
            logger.critical(f"Failed to initialize CredentialEncryption: {e}. Check your ENCRYPTION_KEY.")
            raise ValueError("Invalid ENCRYPTION_KEY in your configuration.")

    def encrypt_credential(self, credential: str) -> str:

        if not isinstance(credential, str) or not credential:
            raise ValueError("Credential to encrypt must be a non-empty string.")

        encrypted_bytes = self.cipher.encrypt(credential.encode())
        return encrypted_bytes.decode()

    def decrypt_credential(self, encrypted_credential: str) -> str:

        if not isinstance(encrypted_credential, str) or not encrypted_credential:
            raise ValueError("Encrypted credential must be a non-empty string.")

        decrypted_bytes = self.cipher.decrypt(encrypted_credential.encode())
        return decrypted_bytes.decode()