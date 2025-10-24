from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.encryption import decrypt_credentials
from app.utils.jwt_handler import decode_access_token
from app.services.aws.client import AWSClientProvider
import logging
logger = logging.getLogger(__name__)

# Dòng này định nghĩa cách FastAPI sẽ tìm token: trong header "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_aws_client_provider(token: str = Depends(oauth2_scheme)) -> AWSClientProvider:
    """
    Đây là một dependency:
    1. Yêu cầu và xác thực JWT token.
    2. Nếu hợp lệ, nó tạo và trả về một instance của AWSClientProvider đã được xác thực.
    Bất kỳ endpoint nào "phụ thuộc" vào hàm này sẽ được bảo vệ.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    aws_account_id = payload.get("aws_account_id") or payload.get("sub")
    if aws_account_id is None:
        raise credentials_exception
    try:
        # Import here to avoid circular imports
        from app.database.models import ClientModel

        # Fetch client from database
        client_model = ClientModel()
        client = await client_model.get_client_by_aws_account_id(aws_account_id)

        if not client:
            logger.warning(f"Client not found: {aws_account_id}")
            raise credentials_exception

        # Check status
        if client.get('status') != 'active':
            logger.warning(f"Client inactive: {aws_account_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {client.get('status')}"
            )

        # Create AWS client provider with decrypted credentials
        return AWSClientProvider(
            access_key=client['aws_access_key'],
            secret_key=client['aws_secret_key'],
            region=client.get('aws_region', 'us-east-1')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in auth dependency: {e}", exc_info=True)
        raise credentials_exception


def get_current_client_id(token: str = Depends(oauth2_scheme)) -> str:
    """
    New dependency - extracts aws_account_id from JWT
    Used for database operations and user identification
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Extract aws_account_id from token
    aws_account_id = payload.get("aws_account_id") or payload.get("sub")

    if not aws_account_id:
        logger.error(f"No aws_account_id found in token payload: {payload}")
        raise credentials_exception

    return aws_account_id

