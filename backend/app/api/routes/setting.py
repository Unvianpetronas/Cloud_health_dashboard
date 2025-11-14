from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict
import logging
from app.database.models import ClientModel
from app.api.middleware.dependency import get_current_client_id

logger = logging.getLogger(__name__)
router = APIRouter()


class NotificationSettings(BaseModel):
    email: bool = True
    push: bool = False
    critical: bool = True
    warning: bool = True
    info: bool = False


class DashboardSettings(BaseModel):
    autoRefresh: bool = True
    refreshInterval: int = 300  # seconds
    theme: str = "dark"
    defaultTimeRange: str = "24h"


class SecuritySettings(BaseModel):
    sessionTimeout: int = 3600  # seconds
    requireReauth: bool = False


class SettingsUpdateRequest(BaseModel):
    notifications: Optional[NotificationSettings] = None
    dashboard: Optional[DashboardSettings] = None
    security: Optional[SecuritySettings] = None


class SettingsResponse(BaseModel):
    success: bool
    message: str
    settings: Dict


@router.get("/settings")
async def get_settings(aws_account_id: str = Depends(get_current_client_id)):
    """
    Get user settings from database.

    Returns current settings or default settings if none exist.
    """
    try:
        client_model = ClientModel()
        client = await client_model.get_client(aws_account_id)

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Get settings from client data or return defaults
        settings = client.get('settings', {
            'notifications': {
                'email': True,
                'push': False,
                'critical': True,
                'warning': True,
                'info': False
            },
            'dashboard': {
                'autoRefresh': True,
                'refreshInterval': 300,
                'theme': 'dark',
                'defaultTimeRange': '24h'
            },
            'security': {
                'sessionTimeout': 3600,
                'requireReauth': False
            }
        })

        logger.info(f"Retrieved settings for client {aws_account_id[:8]}...")

        return {
            "success": True,
            "settings": settings
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve settings"
        )


@router.put("/settings")
async def update_settings(
    settings_data: SettingsUpdateRequest,
    aws_account_id: str = Depends(get_current_client_id)
):
    """
    Update user settings in database.

    Validates and saves user preferences for notifications, dashboard, and security.
    """
    try:
        client_model = ClientModel()
        client = await client_model.get_client(aws_account_id)

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Get existing settings or defaults
        current_settings = client.get('settings', {
            'notifications': {},
            'dashboard': {},
            'security': {}
        })

        # Update only provided fields
        if settings_data.notifications:
            current_settings['notifications'] = settings_data.notifications.dict()

        if settings_data.dashboard:
            dashboard_dict = settings_data.dashboard.dict()
            # Validate refresh interval (1 min to 30 min)
            if not (60 <= dashboard_dict['refreshInterval'] <= 1800):
                raise HTTPException(
                    status_code=400,
                    detail="Refresh interval must be between 60 and 1800 seconds"
                )
            current_settings['dashboard'] = dashboard_dict

        if settings_data.security:
            security_dict = settings_data.security.dict()
            # Validate session timeout (30 min to 4 hours)
            if not (1800 <= security_dict['sessionTimeout'] <= 14400):
                raise HTTPException(
                    status_code=400,
                    detail="Session timeout must be between 1800 and 14400 seconds"
                )
            current_settings['security'] = security_dict

        # Save settings to database
        success = await client_model.update_settings(aws_account_id, current_settings)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to save settings"
            )

        logger.info(f"Updated settings for client {aws_account_id[:8]}...")

        return {
            "success": True,
            "message": "Settings saved successfully",
            "settings": current_settings
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to update settings"
        )


@router.post("/settings/test-email")
async def send_test_email(aws_account_id: str = Depends(get_current_client_id)):
    """
    Send a test email to verify email notification settings.
    """
    try:
        from app.services.email.ses_client import SESEmailService

        client_model = ClientModel()
        client = await client_model.get_client(aws_account_id)

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        email = client.get('email')
        if not email:
            raise HTTPException(
                status_code=400,
                detail="No email address associated with this account"
            )

        if not client.get('email_verified'):
            raise HTTPException(
                status_code=400,
                detail="Email address not verified. Please verify your email first."
            )

        # Send test email
        await SESEmailService.send_test_notification(
            recipient_email=email,
            client_name=client.get('company_name', 'User'),
            aws_account_id=aws_account_id
        )

        logger.info(f"Test email sent to {email}")

        return {
            "success": True,
            "message": f"Test email sent successfully to {email}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to send test email"
        )
