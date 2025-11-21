from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from app.database.models import ClientModel
from app.api.middleware.dependency import get_current_client_id
from app.services.email.ses_client import SESEmailService
from datetime import datetime, timedelta
import logging
import secrets

router = APIRouter()
logger = logging.getLogger(__name__)


class NotificationPreferences(BaseModel):
    critical_alerts: bool = True
    warning_alerts: bool = False
    cost_alerts: bool = True
    daily_summary: bool = False


class UpdateEmailRequest(BaseModel):
    email: EmailStr


@router.get("/settings/notifications", tags=["Settings"])
async def get_notification_preferences(
        current_aws_account_id: str = Depends(get_current_client_id)
):
    """
    Get current notification preferences for authenticated user
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
            "preferences": client.get('notification_preferences', {
                'critical_alerts': True,
                'warning_alerts': False,
                'cost_alerts': True,
                'daily_summary': False
            })
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching notification preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/notifications", tags=["Settings"])
async def update_notification_preferences(
        preferences: NotificationPreferences,
        current_aws_account_id: str = Depends(get_current_client_id)
):
    """
    Update notification preferences
    User must have verified email to enable daily_summary
    """
    try:
        client_model = ClientModel()

        # Get client info
        client = await client_model.get_client_by_aws_account_id(current_aws_account_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # CHECK: If trying to enable daily_summary, email must be verified
        if preferences.daily_summary and not client.get('email_verified', False):
            raise HTTPException(
                status_code=500,
                detail=f"Email verification required. Please verify your email before enabling notifications."
            )

        # UPDATE PREFERENCES IN DATABASE
        success = await client_model.update_notification_preferences(
            current_aws_account_id,  # Use aws_account_id
            preferences.dict()
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update notification preferences"
            )

        logger.info(f"Notification preferences updated for {current_aws_account_id}")

        return {
            "success": True,
            "message": "Notification preferences updated successfully",
            "preferences": preferences.dict(),
            "email_verified": client.get('email_verified', False)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/profile", tags=["Settings"])
async def get_user_profile(
        current_aws_account_id: str = Depends(get_current_client_id)
):
    """
    Get user profile information
    """
    try:
        client_model = ClientModel()
        client = await client_model.get_client_by_aws_account_id(current_aws_account_id)

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        return {
            "success": True,
            "profile": {
                "aws_account_id": client.get('aws_account_id'),
                "email": client.get('email'),
                "company_name": client.get('company_name'),
                "email_verified": client.get('email_verified', False),
                "status": client.get('status'),
                "created_at": client.get('created_at'),
                "aws_region": client.get('aws_region')
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/email", tags=["Settings"])
async def update_email(
        request: UpdateEmailRequest,
        current_aws_account_id: str = Depends(get_current_client_id)
):
    """
    Update user email address and send verification email
    Marks email as unverified until user clicks verification link
    """
    try:
        client_model = ClientModel()

        # Get current client
        client = await client_model.get_client_by_aws_account_id(current_aws_account_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Check if email is already in use by another account
        # (Optional: You can add this check if needed)

        # Generate verification token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)

        # Update email and reset verification status
        client_model.table.update_item(
            Key={
                'pk': f"CLIENT#{current_aws_account_id}",
                'sk': 'METADATA'
            },
            UpdateExpression='SET email = :email, email_verified = :verified, email_verification_token = :token, email_verification_expires = :expires, updated_at = :updated',
            ExpressionAttributeValues={
                ':email': request.email,
                ':verified': False,
                ':token': token,
                ':expires': expires_at.isoformat(),
                ':updated': datetime.now().isoformat()
            }
        )

        logger.info(f"Email updated for {current_aws_account_id}: {request.email}")

        # Send verification email
        email_service = SESEmailService()
        company_name = client.get('company_name', 'Your Company')

        try:
            result = await email_service.send_verification_email(
                recipient_email=request.email,
                verification_token=token,
                client_name=company_name
            )

            if result:
                logger.info(f"Verification email sent to {request.email}")
            else:
                logger.warning(f"Failed to send verification email to {request.email}")

        except Exception as email_error:
            logger.error(f"Error sending verification email: {email_error}")
            # Don't fail the request if email sending fails

        return {
            "success": True,
            "message": f"Email updated to {request.email}. Please check your inbox for verification link.",
            "email": request.email,
            "email_verified": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))