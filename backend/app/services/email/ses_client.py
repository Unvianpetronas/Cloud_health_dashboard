import boto3
from botocore.exceptions import ClientError
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SESEmailService:


    def __init__(self):
        try:
            if settings.YOUR_AWS_ACCESS_KEY_ID and settings.YOUR_AWS_SECRET_ACCESS_KEY:
                self.ses = boto3.client(
                    'ses',
                    region_name=settings.YOUR_AWS_REGION,
                    aws_access_key_id=settings.YOUR_AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.YOUR_AWS_SECRET_ACCESS_KEY
                )
                logger.info("SES client initialized with explicit credentials")
            else:
                # Use default credentials (IAM role if on EC2)
                self.ses = boto3.client('ses', region_name=settings.YOUR_AWS_REGION)
                logger.info("SES client initialized with default credentials")

            self.sender_email = settings.SES_SENDER_EMAIL
            self.frontend_url = settings.FRONTEND_URL

            logger.info(f"Email service ready. Sender: {self.sender_email}")

        except Exception as e:
            logger.error(f"Failed to initialize SES client: {e}")
            raise

    async def send_verification_email(self,
                                      recipient_email: str,
                                      verification_token: str,
                                      client_name: str) -> bool:
        try:
            verification_link = f"{self.frontend_url}/verify-email?token={verification_token}"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ 
                        font-family: Arial, sans-serif;
                        background-color: #0b1020;
                        margin: 0;
                        padding: 20px;
                        color: #e6e9f5;
                    }}
                    .container {{ 
                        max-width: 600px;
                        margin: 0 auto;
                        background: linear-gradient(135deg, #0e1430 0%, #111836 100%);
                        padding: 40px;
                        border-radius: 16px;
                        border: 1px solid rgba(110, 168, 255, 0.2);
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                    }}
                    .header {{ 
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .header h1 {{ 
                        color: #60a5fa;
                        margin: 0;
                        font-size: 28px;
                    }}
                    .icon {{
                        font-size: 48px;
                        margin-bottom: 15px;
                    }}
                    .content p {{
                        color: #b7c0d9;
                        font-size: 16px;
                        line-height: 1.6;
                    }}
                    .button {{ 
                        display: inline-block;
                        padding: 16px 40px;
                        background: linear-gradient(135deg, #3b82f6, #60a5fa);
                        color: white;
                        text-decoration: none;
                        border-radius: 12px;
                        font-weight: 700;
                        font-size: 16px;
                        margin: 20px 0;
                    }}
                    .button:hover {{
                        background: linear-gradient(135deg, #2563eb, #3b82f6);
                    }}
                    .footer {{ 
                        text-align: center;
                        color: #8b93ad;
                        font-size: 13px;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid rgba(110, 168, 255, 0.1);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="icon">☁️</div>
                        <h1>AWS Cloud Health Dashboard</h1>
                    </div>

                    <div class="content">
                        <h2 style="color: #e6e9f5;">Welcome, {client_name}! </h2>
                        <p>Thank you for using AWS Cloud Health Dashboard. Please verify your email address to receive critical alerts and notifications.</p>

                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_link}" class="button">
                                ✅ Verify Email Address
                            </a>
                        </div>

                        <p style="font-size: 14px; color: #8b93ad;">
                            Or copy and paste this link into your browser:<br>
                            <code style="color: #60a5fa;">{verification_link}</code>
                        </p>

                        <p style="font-size: 13px; color: #ef4444;">
                            🔒 This link expires in 24 hours. If you didn't request this, you can safely ignore it.
                        </p>
                    </div>

                    <div class="footer">
                        <p><strong>AWS Cloud Health Dashboard</strong></p>
                        <p>© 2025 All rights reserved</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            AWS Cloud Health Dashboard - Email Verification

            Welcome, {client_name}!

            Please verify your email address by clicking the link below:
            {verification_link}

            This link expires in 24 hours.

            If you didn't request this, please ignore this email.

            © 2025 AWS Cloud Health Dashboard
            """

            response = self.ses.send_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [recipient_email]},
                Message={
                    'Subject': {
                        'Data': '✅ Verify Your Email - AWS Cloud Health Dashboard',
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        },
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )

            logger.info(f"Verification email sent to {recipient_email}")
            logger.debug(f"SES Response: {response}")
            return True

        except ClientError as e:
            logger.error(f"Failed to send verification email: {e}")
            logger.error(f"Error code: {e.response['Error']['Code']}")
            logger.error(f"Error message: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False

    async def send_critical_alert(self,
                                  recipient_email: str,
                                  alert_data: dict) -> bool:
        """
        Send critical GuardDuty security alert

        Args:
            recipient_email: Recipient email
            alert_data: Alert details dict with keys:
                - severity: HIGH, MEDIUM, LOW
                - title: Alert title
                - description: Alert description
                - service: AWS service name
                - resource_id: Resource ID
                - region: AWS region
                - timestamp: Timestamp
                - finding_id: Finding ID

        Returns:
            True if sent successfully
        """
        try:
            severity = alert_data.get('severity', 'HIGH')
            severity_colors = {
                'HIGH': '#ef4444',
                'MEDIUM': '#f59e0b',
                'LOW': '#3b82f6'
            }
            severity_color = severity_colors.get(severity, '#ef4444')

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ 
                        font-family: Arial, sans-serif;
                        background-color: #0b1020;
                        margin: 0;
                        padding: 20px;
                        color: #e6e9f5;
                    }}
                    .container {{ 
                        max-width: 600px;
                        margin: 0 auto;
                        background: linear-gradient(135deg, #0e1430 0%, #111836 100%);
                        padding: 0;
                        border-radius: 16px;
                        border: 2px solid {severity_color};
                        box-shadow: 0 20px 60px rgba(239, 68, 68, 0.3);
                        overflow: hidden;
                    }}
                    .header {{ 
                        background: linear-gradient(135deg, #dc2626, #ef4444);
                        padding: 35px 30px;
                        text-align: center;
                    }}
                    .header h1 {{ 
                        color: white;
                        margin: 0;
                        font-size: 26px;
                    }}
                    .icon {{
                        font-size: 52px;
                        margin-bottom: 12px;
                    }}
                    .content {{ 
                        padding: 35px;
                    }}
                    .severity-badge {{
                        display: inline-block;
                        padding: 10px 20px;
                        background: {severity_color};
                        color: white;
                        border-radius: 8px;
                        font-weight: 700;
                        font-size: 14px;
                        margin-bottom: 20px;
                    }}
                    .alert-title {{
                        color: #ef4444;
                        font-size: 22px;
                        font-weight: 700;
                        margin: 20px 0 15px 0;
                    }}
                    .detail-box {{
                        background: rgba(239, 68, 68, 0.1);
                        border-left: 4px solid #ef4444;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .detail-box h3 {{
                        color: #e6e9f5;
                        font-size: 16px;
                        margin: 0 0 12px 0;
                    }}
                    .detail-box p {{
                        color: #b7c0d9;
                        margin: 0;
                        line-height: 1.6;
                    }}
                    .detail-box ul {{
                        margin: 10px 0 0 0;
                        padding-left: 20px;
                        color: #b7c0d9;
                    }}
                    .button {{ 
                        display: inline-block;
                        padding: 16px 40px;
                        background: linear-gradient(135deg, #ef4444, #dc2626);
                        color: white;
                        text-decoration: none;
                        border-radius: 12px;
                        font-weight: 700;
                        font-size: 16px;
                        margin: 20px 0;
                    }}
                    .footer {{ 
                        text-align: center;
                        color: #8b93ad;
                        font-size: 13px;
                        padding: 25px;
                        border-top: 1px solid rgba(110, 168, 255, 0.1);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="icon">🚨</div>
                        <h1>CRITICAL SECURITY ALERT</h1>
                    </div>

                    <div class="content">
                        <div class="severity-badge">⚠️ SEVERITY: {severity}</div>

                        <h2 class="alert-title">{alert_data.get('title', 'Security Issue Detected')}</h2>

                        <div class="detail-box">
                            <h3>📋 Description</h3>
                            <p>{alert_data.get('description', 'A security issue has been detected.')}</p>
                        </div>

                        <div class="detail-box">
                            <h3>🔍 Details</h3>
                            <ul>
                                <li><strong>Service:</strong> {alert_data.get('service', 'Unknown')}</li>
                                <li><strong>Resource:</strong> {alert_data.get('resource_id', 'N/A')}</li>
                                <li><strong>Region:</strong> {alert_data.get('region', 'N/A')}</li>
                                <li><strong>Time:</strong> {alert_data.get('timestamp', 'N/A')}</li>
                            </ul>
                        </div>

                        <div style="text-align: center;">
                            <a href="{self.frontend_url}/dashboard?alert={alert_data.get('finding_id', '')}" class="button">
                                🔎 View in Dashboard
                            </a>
                        </div>
                    </div>

                    <div class="footer">
                        <p><strong>AWS Cloud Health Dashboard</strong></p>
                        <p>Real-time Security Monitoring</p>
                    </div>
                </div>
            </body>
            </html>
            """

            response = self.ses.send_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [recipient_email]},
                Message={
                    'Subject': {
                        'Data': f'🚨 CRITICAL ALERT: {alert_data.get("title", "Security Issue")}',
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )

            logger.info(f"Critical alert sent to {recipient_email}")
            return True

        except ClientError as e:
            logger.error(f"Failed to send critical alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False


