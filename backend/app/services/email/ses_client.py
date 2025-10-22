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


    async def send_daily_summary_email(self,
                                       recipient_email: str,
                                       client_name: str,
                                       summary_data: dict) -> bool:
        """
        Send daily security summary email

        Args:
            recipient_email: Recipient email address
            client_name: Company/client name
            summary_data: Dictionary with summary statistics:
                {
                    'total_findings': int,
                    'critical_count': int,
                    'high_count': int,
                    'medium_count': int,
                    'low_count': int,
                    'timestamp': str,
                    'period': str,
                    'aws_account_id': str (optional)
                }

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Extract data
            total = summary_data.get('total_findings', 0)
            critical = summary_data.get('critical_count', 0)
            high = summary_data.get('high_count', 0)
            medium = summary_data.get('medium_count', 0)
            low = summary_data.get('low_count', 0)
            period = summary_data.get('period', '24 hours')
            is_test = summary_data.get('is_test', False)

            # Determine overall status
            if critical > 0:
                status_emoji = "🔴"
                status_text = "Critical Issues Detected"
                status_color = "#ef4444"
            elif high > 0:
                status_emoji = "🟠"
                status_text = "High Priority Issues"
                status_color = "#f59e0b"
            elif medium > 0:
                status_emoji = "🟡"
                status_text = "Medium Priority Issues"
                status_color = "#eab308"
            elif total > 0:
                status_emoji = "🔵"
                status_text = "Low Priority Issues"
                status_color = "#3b82f6"
            else:
                status_emoji = "✅"
                status_text = "All Clear"
                status_color = "#10b981"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                        background-color: #0b1020;
                        margin: 0;
                        padding: 20px;
                        color: #e6e9f5;
                    }}
                    .container {{ 
                        max-width: 600px;
                        margin: 0 auto;
                        background: linear-gradient(135deg, #0e1430 0%, #111836 100%);
                        border-radius: 16px;
                        overflow: hidden;
                        border: 1px solid rgba(110, 168, 255, 0.2);
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                    }}
                    .header {{ 
                        background: linear-gradient(135deg, #1e3a8a, #3b82f6);
                        padding: 40px 30px;
                        text-align: center;
                    }}
                    .header h1 {{ 
                        color: white;
                        margin: 0;
                        font-size: 28px;
                        font-weight: 700;
                    }}
                    .header .icon {{
                        font-size: 56px;
                        margin-bottom: 15px;
                    }}
                    .header .subtitle {{
                        color: #dbeafe;
                        font-size: 14px;
                        margin-top: 10px;
                        opacity: 0.9;
                    }}
                    .content {{ 
                        padding: 40px 30px;
                    }}
                    .status-banner {{
                        background: rgba(59, 130, 246, 0.1);
                        border-left: 4px solid {status_color};
                        padding: 20px;
                        border-radius: 8px;
                        margin-bottom: 30px;
                        display: flex;
                        align-items: center;
                        gap: 15px;
                    }}
                    .status-banner .emoji {{
                        font-size: 40px;
                    }}
                    .status-banner .text {{
                        flex: 1;
                    }}
                    .status-banner .text h2 {{
                        margin: 0;
                        font-size: 20px;
                        color: #e6e9f5;
                    }}
                    .status-banner .text p {{
                        margin: 5px 0 0 0;
                        color: #8b93ad;
                        font-size: 14px;
                    }}
                    .stats-grid {{
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 15px;
                        margin: 30px 0;
                    }}
                    .stat-card {{
                        background: rgba(30, 41, 59, 0.5);
                        padding: 20px;
                        border-radius: 12px;
                        border: 1px solid rgba(110, 168, 255, 0.1);
                        text-align: center;
                    }}
                    .stat-card.critical {{
                        border-left: 3px solid #ef4444;
                    }}
                    .stat-card.high {{
                        border-left: 3px solid #f59e0b;
                    }}
                    .stat-card.medium {{
                        border-left: 3px solid #eab308;
                    }}
                    .stat-card.low {{
                        border-left: 3px solid #3b82f6;
                    }}
                    .stat-card .number {{
                        font-size: 36px;
                        font-weight: 700;
                        margin: 10px 0;
                    }}
                    .stat-card.critical .number {{ color: #ef4444; }}
                    .stat-card.high .number {{ color: #f59e0b; }}
                    .stat-card.medium .number {{ color: #eab308; }}
                    .stat-card.low .number {{ color: #3b82f6; }}
                    .stat-card .label {{
                        font-size: 12px;
                        color: #8b93ad;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        font-weight: 600;
                    }}
                    .total-box {{
                        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(96, 165, 250, 0.1));
                        border: 2px solid rgba(59, 130, 246, 0.3);
                        padding: 25px;
                        border-radius: 12px;
                        text-align: center;
                        margin: 20px 0;
                    }}
                    .total-box .number {{
                        font-size: 48px;
                        font-weight: 700;
                        color: #60a5fa;
                        margin: 10px 0;
                    }}
                    .total-box .label {{
                        font-size: 14px;
                        color: #b7c0d9;
                    }}
                    .button {{ 
                        display: inline-block;
                        padding: 16px 32px;
                        background: linear-gradient(135deg, #3b82f6, #60a5fa);
                        color: white;
                        text-decoration: none;
                        border-radius: 12px;
                        font-weight: 700;
                        font-size: 16px;
                        margin: 20px 0;
                        transition: transform 0.2s;
                    }}
                    .button:hover {{
                        background: linear-gradient(135deg, #2563eb, #3b82f6);
                        transform: translateY(-2px);
                    }}
                    .footer {{ 
                        text-align: center;
                        color: #8b93ad;
                        font-size: 13px;
                        padding: 30px;
                        border-top: 1px solid rgba(110, 168, 255, 0.1);
                    }}
                    .footer p {{
                        margin: 5px 0;
                    }}
                    .test-badge {{
                        background: #f59e0b;
                        color: white;
                        padding: 5px 15px;
                        border-radius: 20px;
                        font-size: 12px;
                        font-weight: 700;
                        display: inline-block;
                        margin-top: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="icon">☁️</div>
                        <h1>Daily Security Summary</h1>
                        <p class="subtitle">{client_name}</p>
                        <p class="subtitle">Last {period}</p>
                        {f'<span class="test-badge">TEST EMAIL</span>' if is_test else ''}
                    </div>
    
                    <div class="content">
                        <div class="status-banner">
                            <div class="emoji">{status_emoji}</div>
                            <div class="text">
                                <h2>{status_text}</h2>
                                <p>Security summary for the past {period}</p>
                            </div>
                        </div>
    
                        <div class="total-box">
                            <div class="label">Total Findings</div>
                            <div class="number">{total}</div>
                            <div class="label">Last {period}</div>
                        </div>
    
                        <div class="stats-grid">
                            <div class="stat-card critical">
                                <div class="label">🔴 Critical</div>
                                <div class="number">{critical}</div>
                            </div>
    
                            <div class="stat-card high">
                                <div class="label">🟠 High</div>
                                <div class="number">{high}</div>
                            </div>
    
                            <div class="stat-card medium">
                                <div class="label">🟡 Medium</div>
                                <div class="number">{medium}</div>
                            </div>
    
                            <div class="stat-card low">
                                <div class="label">🔵 Low</div>
                                <div class="number">{low}</div>
                            </div>
                        </div>
    
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="{self.frontend_url}/dashboard" class="button">
                                🔎 View Full Dashboard
                            </a>
                        </div>
    
                        <p style="font-size: 13px; color: #8b93ad; text-align: center; margin-top: 20px;">
                            💡 <strong>Tip:</strong> Check your dashboard regularly to stay on top of security issues
                        </p>
                    </div>
    
                    <div class="footer">
                        <p><strong>AWS Cloud Health Dashboard</strong></p>
                        <p>Real-time Security Monitoring</p>
                        <p style="margin-top: 15px;">
                            <a href="{self.frontend_url}/settings/notifications" style="color: #60a5fa; text-decoration: none;">
                                Manage notification preferences
                            </a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            AWS Cloud Health Dashboard - Daily Security Summary
            {client_name}
    
            {status_text}
            Last {period}
    
            TOTAL FINDINGS: {total}
    
            By Severity:
            🔴 Critical: {critical}
            🟠 High: {high}
            🟡 Medium: {medium}
            🔵 Low: {low}
    
            View your dashboard: {self.frontend_url}/dashboard
    
            © 2025 AWS Cloud Health Dashboard
            """

            # Send email
            response = self.ses.send_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [recipient_email]},
                Message={
                    'Subject': {
                        'Data': f'Daily Security Summary - {client_name}',
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

            logger.info(f"Daily summary email sent to {recipient_email}")
            logger.debug(f"SES Response: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}", exc_info=True)
            return False









