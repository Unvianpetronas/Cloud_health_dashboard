from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.database.models import ClientModel
from app.api.middleware.dependency import get_current_client_id
from datetime import datetime, timedelta
from app.services.email.ses_client import SESEmailService
import logging
import secrets

router = APIRouter()
logger = logging.getLogger(__name__)


class SendVerificationRequest(BaseModel):
    aws_account_id: str


@router.post("/email/send-verification", tags=["Email"])
async def send_verification_email(
        request: SendVerificationRequest,
        current_aws_account_id: str = Depends(get_current_client_id)
):
    """
    Send email verification to authenticated user
    Generates token, stores to database, and sends email
    """
    try:
        # SECURITY CHECK: User can only send verification for their own account
        if request.aws_account_id != current_aws_account_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to send verification for this account"
            )

        client_model = ClientModel()

        # Get client by aws_account_id
        client = await client_model.get_client_by_aws_account_id(request.aws_account_id)

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        email = client.get('email')
        company_name = client.get('company_name', 'Your Company')

        if not email:
            raise HTTPException(
                status_code=400,
                detail="No email associated with this account"
            )

        # Check if already verified
        if client.get('email_verified', False):
            return {
                "success": True,
                "message": "Email already verified",
                "already_verified": True,
                "email": email
            }

        # GENERATE VERIFICATION TOKEN
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)

        # STORE TOKEN TO DATABASE
        client_model.table.update_item(
            Key={
                'pk': f"CLIENT#{request.aws_account_id}",
                'sk': 'METADATA'
            },
            UpdateExpression='SET email_verification_token = :token, email_verification_expires = :expires, updated_at = :updated',
            ExpressionAttributeValues={
                ':token': token,
                ':expires': expires_at.isoformat(),
                ':updated': datetime.now().isoformat()
            }
        )

        logger.info(f"Verification token generated and saved for {request.aws_account_id}")
        email_service = SESEmailService()
        result = await email_service.send_verification_email(
            recipient_email=email,
            verification_token=token,
            client_name=company_name
        )

        if result:
            logger.info(f"Verification email sent to {email}")
            return {
                "success": True,
                "message": f"Verification email sent to {email}",
                "email": email,
                "expires_in": "24 hours"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send verification email"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending verification email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email/verify", tags=["Email"])
async def verify_email_token(token: str = Query(..., description="Email verification token from email link")):
    """
    Verify email token when user clicks link in email
    PUBLIC ENDPOINT - no authentication required
    Checks token validity and marks email as verified
    """
    try:
        client_model = ClientModel()
        aws_account_id = await client_model.verify_email(token)

        if not aws_account_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired verification token. Please request a new verification email."
            )

        logger.info(f" Email verified successfully for client {aws_account_id}")

        return {
            "success": True,
            "message": "Email verified successfully! You can now enable notifications in your settings.",
            "aws_account_id": aws_account_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email/verification-status", tags=["Email"])
async def get_verification_status(
        current_aws_account_id: str = Depends(get_current_client_id)
):
    """
    Check if authenticated user's email is verified
    Returns current verification status
    """
    try:
        client_model = ClientModel()
        client = await client_model.get_client_by_aws_account_id(current_aws_account_id)

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        return {
            "success": True,
            "email": client.get('email'),
            "email_verified": client.get('email_verified', False),
            "aws_account_id": client.get('aws_account_id'),
            "company_name": client.get('company_name')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking verification status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email/resend-verification", tags=["Email"])
async def resend_verification_email(
        request: SendVerificationRequest,
        current_aws_account_id: str = Depends(get_current_client_id)
):
    """
    Resend verification email if previous one expired or was not received
    """
    try:
        if request.aws_account_id != current_aws_account_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        client_model = ClientModel()
        client = await client_model.get_client_by_aws_account_id(request.aws_account_id)

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Check if already verified
        if client.get('email_verified', False):
            return {
                "success": True,
                "message": "Email is already verified",
                "already_verified": True
            }

        email = client.get('email')
        company_name = client.get('company_name', 'Your Company')

        # Generate new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)

        # Update token in database
        client_model.table.update_item(
            Key={
                'pk': f"CLIENT#{request.aws_account_id}",
                'sk': 'METADATA'
            },
            UpdateExpression='SET email_verification_token = :token, email_verification_expires = :expires, updated_at = :updated',
            ExpressionAttributeValues={
                ':token': token,
                ':expires': expires_at.isoformat(),
                ':updated': datetime.now().isoformat()
            }
        )

        # Send new email
        email_service = SESEmailService()
        result = await email_service.send_verification_email(
            recipient_email=email,
            verification_token=token,
            client_name=company_name
        )

        if result:
            logger.info(f"Verification email resent to {email}")
            return {
                "success": True,
                "message": f"Verification email resent to {email}",
                "email": email
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to resend email")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending verification email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
