from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.aws.client import AWSClientProvider
from app.services.aws.guardduty import GuardDutyScanner
from app.services.email.ses_client import SESEmailService
from app.api.middleware.dependency import get_aws_client_provider
from pydantic import BaseModel, EmailStr
from app.database.models import ClientModel
import logging
import secrets

router = APIRouter()
logger = logging.getLogger(__name__)


class SendVerificationRequest(BaseModel):
    email: EmailStr
    company_name: str


class SendAlertRequest(BaseModel):
    email: EmailStr


@router.get("/email/send-alert", tags=["Email"])
async def send_alert_email(
        request: SendAlertRequest,
        client_provider: AWSClientProvider = Depends(get_aws_client_provider),
):
    try:
        scanner = GuardDutyScanner(client_provider)
        result = scanner.get_critical_findings_with_alerts(request.email)

        if not result:
            logger.error(f"Failed to send email alert to: {request.email}")
            return {"success": False}

        return {
            "success": True,
            "total_findings": result.get("total_critical", 0),
            "alerts_sent": result.get("alerts_sent", 0),
            "alerts_failed": result.get("alerts_failed", 0),
            "message": f"Sent {result.get('alerts_sent', 0)} alerts to {request.email}",
        }

    except Exception as e:
        logger.error(f"Error sending critical alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while sending alerts."
        )

@router.get("/email/send-verification", tags=["Email"])
async def send_verification_email(request: SendVerificationRequest,
                                  client_provider: AWSClientProvider = Depends(get_aws_client_provider)
                                  ):
    try:
        token = secrets.token_urlsafe(32)
        email_service = SESEmailService(client_provider)
        result = email_service.send_verification_email(request.email, token, request.company_name)
        if result:

            return {
                "success": True,
                "message": f"Verification email sent to {request.email}",
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send email"
            )
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        raise HTTPException(status_code=500, detail=str(e))




