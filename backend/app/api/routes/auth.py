from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
import logging

from app.config import settings
from app.database.models import ClientModel
from app.services.aws.iam import verify_aws_credentials
from app.utils.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token
)

logger = logging.getLogger(__name__)
router = APIRouter()


class AuthRequest(BaseModel):
    aws_access_key: str = Field(..., min_length=16, max_length=128)
    aws_secret_key: str = Field(..., min_length=16, max_length=128)
    aws_region: str = Field(default="us-east-1")
    email: Optional[EmailStr] = Field(None)
    company_name: Optional[str] = Field(None)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    client_id: str
    aws_account_id: str
    is_new_account: bool
    email: Optional[str] = None
    company_name: Optional[str] = None


@router.post("/auth/login", response_model=TokenResponse)
async def authenticate(request: AuthRequest):
    """
    🔐 Universal Authentication Endpoint

    - Verifies AWS credentials with real AWS STS
    - Auto-creates account if doesn't exist
    - Returns JWT tokens for API access
    """
    client_model = ClientModel()

    try:
        logger.info("Verifying AWS credentials...")

        identity = await verify_aws_credentials(
            access_key=request.aws_access_key,
            secret_key=request.aws_secret_key
        )

        if not identity:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid AWS credentials"
            )

        aws_account_id = identity['Account']
        aws_user_arn = identity['Arn']

        logger.info(f"AWS verified: {aws_account_id}")
        existing_client = await client_model.get_client_by_aws_account_id(aws_account_id)

        if existing_client:
            # Existing account - login
            client_id = existing_client['client_id']

            # Update credentials (supports key rotation)
            await client_model.update_credentials(
                client_id=client_id,
                aws_access_key=request.aws_access_key,
                aws_secret_key=request.aws_secret_key,
                aws_region=request.aws_region
            )

            # Check status
            if existing_client.get('status') != 'active':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account is {existing_client.get('status')}"
                )

            logger.info(f"👤 Login: {client_id}")
            is_new = False
            client_email = existing_client.get('email')
            client_company = existing_client.get('company_name')

        else:
            # New account - auto-create
            logger.info(f"Creating account for AWS {aws_account_id}")

            client_email = request.email or f"aws-{aws_account_id}@cloudhealth.local"

            if request.company_name:
                client_company = request.company_name
            else:
                # Extract name from ARN
                if ':user/' in aws_user_arn:
                    user_name = aws_user_arn.split(':user/')[-1]
                    client_company = f"{user_name}'s AWS Account"
                else:
                    client_company = f"AWS Account {aws_account_id}"

            # Create new client
            client_id = await client_model.create_client(
                email=client_email,
                company_name=client_company,
                aws_account_id=aws_account_id,
                aws_access_key=request.aws_access_key,
                aws_secret_key=request.aws_secret_key,
                aws_region=request.aws_region
            )

            if not client_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create account"
                )

            logger.info(f"Account created: {client_id}")
            is_new = True
        token_data = {
            "sub": client_id,
            "aws_account_id": aws_account_id
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": client_id})

        logger.info(f"Tokens generated for {client_id}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=60 * 60,  # 60 minutes in seconds
            client_id=client_id,
            aws_account_id=aws_account_id,
            is_new_account=is_new,
            email=client_email if request.email else None,
            company_name=client_company
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(request: dict):
    """Refresh access token using refresh token"""
    client_model = ClientModel()
    refresh_token_str = request.get('refresh_token')

    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required"
        )

    try:
        payload = decode_refresh_token(refresh_token_str)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        client_id = payload.get("sub")

        # Get client from database
        client = await client_model.get_client(client_id)

        if not client or client.get('status') != 'active':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Client not found or inactive"
            )

        aws_account_id = client.get('aws_account_id', 'unknown')

        token_data = {
            "sub": client_id,
            "aws_account_id": aws_account_id
        }

        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"sub": client_id})

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=60 * 60,
            client_id=client_id,
            aws_account_id=aws_account_id,
            is_new_account=False,
            email=client.get('email'),
            company_name=client.get('company_name')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )