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
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

                    body {{ 
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(180deg, #030712 0%, #0f172a 50%, #020617 100%);
                        margin: 0;
                        padding: 40px 20px;
                        color: #e2e8f0;
                        min-height: 100vh;
                    }}

                    .wrapper {{
                        max-width: 600px;
                        margin: 0 auto;
                    }}

                    .container {{ 
                        background: linear-gradient(145deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%);
                        padding: 0;
                        border-radius: 24px;
                        border: 1px solid rgba(56, 189, 248, 0.15);
                        box-shadow: 
                            0 0 0 1px rgba(56, 189, 248, 0.05),
                            0 25px 50px -12px rgba(0, 0, 0, 0.7),
                            0 0 100px rgba(56, 189, 248, 0.1);
                        overflow: hidden;
                        position: relative;
                    }}

                    /* Futuristic top accent bar */
                    .accent-bar {{
                        height: 4px;
                        background: linear-gradient(90deg, 
                            #0ea5e9 0%, 
                            #38bdf8 25%, 
                            #818cf8 50%, 
                            #38bdf8 75%, 
                            #0ea5e9 100%);
                        background-size: 200% 100%;
                    }}

                    .inner-content {{
                        padding: 48px 40px;
                    }}

                    .header {{ 
                        text-align: center;
                        margin-bottom: 40px;
                    }}

                    .logo-container {{
                        display: inline-block;
                        padding: 20px;
                        background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(129, 140, 248, 0.1) 100%);
                        border-radius: 20px;
                        border: 1px solid rgba(56, 189, 248, 0.2);
                        margin-bottom: 24px;
                    }}

                    .logo-icon {{
                        font-size: 48px;
                        display: block;
                    }}

                    .brand-name {{
                        color: #f8fafc;
                        margin: 0 0 8px 0;
                        font-size: 26px;
                        font-weight: 700;
                        letter-spacing: -0.5px;
                    }}

                    .brand-tagline {{
                        color: #38bdf8;
                        font-size: 13px;
                        font-weight: 500;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        margin: 0;
                    }}

                    .greeting {{
                        color: #f1f5f9;
                        font-size: 22px;
                        font-weight: 600;
                        margin: 0 0 16px 0;
                    }}

                    .content p {{
                        color: #94a3b8;
                        font-size: 15px;
                        line-height: 1.7;
                        margin: 0 0 16px 0;
                    }}

                    .cta-section {{
                        text-align: center;
                        margin: 40px 0;
                        padding: 32px;
                        background: linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(129, 140, 248, 0.05) 100%);
                        border-radius: 16px;
                        border: 1px solid rgba(56, 189, 248, 0.1);
                    }}

                    .button {{ 
                        display: inline-block;
                        padding: 18px 48px;
                        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
                        color: #ffffff !important;
                        text-decoration: none;
                        border-radius: 14px;
                        font-weight: 600;
                        font-size: 15px;
                        letter-spacing: 0.3px;
                        box-shadow: 
                            0 4px 14px rgba(14, 165, 233, 0.4),
                            0 0 40px rgba(14, 165, 233, 0.2);
                        transition: all 0.3s ease;
                    }}

                    .button:hover {{
                        background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
                        box-shadow: 
                            0 6px 20px rgba(14, 165, 233, 0.5),
                            0 0 60px rgba(14, 165, 233, 0.3);
                    }}

                    .link-fallback {{
                        margin-top: 24px;
                        padding: 16px;
                        background: rgba(15, 23, 42, 0.6);
                        border-radius: 10px;
                        border: 1px solid rgba(71, 85, 105, 0.3);
                    }}

                    .link-fallback p {{
                        font-size: 12px;
                        color: #64748b;
                        margin: 0 0 8px 0;
                    }}

                    .link-fallback code {{
                        color: #38bdf8;
                        font-size: 11px;
                        word-break: break-all;
                        font-family: 'SF Mono', Monaco, 'Courier New', monospace;
                    }}

                    .security-notice {{
                        display: flex;
                        align-items: flex-start;
                        gap: 12px;
                        padding: 16px;
                        background: rgba(239, 68, 68, 0.08);
                        border-radius: 12px;
                        border: 1px solid rgba(239, 68, 68, 0.15);
                        margin-top: 24px;
                    }}

                    .security-notice .icon {{
                        font-size: 18px;
                        flex-shrink: 0;
                    }}

                    .security-notice p {{
                        font-size: 13px;
                        color: #fca5a5;
                        margin: 0;
                        line-height: 1.5;
                    }}

                    .features {{
                        display: table;
                        width: 100%;
                        margin: 32px 0;
                        border-spacing: 12px;
                    }}

                    .feature {{
                        display: table-cell;
                        width: 33.33%;
                        text-align: center;
                        padding: 20px 12px;
                        background: rgba(30, 41, 59, 0.5);
                        border-radius: 12px;
                        border: 1px solid rgba(71, 85, 105, 0.2);
                    }}

                    .feature-icon {{
                        font-size: 24px;
                        margin-bottom: 8px;
                    }}

                    .feature-text {{
                        font-size: 11px;
                        color: #64748b;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        margin: 0;
                    }}

                    .divider {{
                        height: 1px;
                        background: linear-gradient(90deg, 
                            transparent 0%, 
                            rgba(56, 189, 248, 0.3) 50%, 
                            transparent 100%);
                        margin: 32px 0;
                    }}

                    .footer {{ 
                        text-align: center;
                        padding: 32px 40px;
                        background: rgba(2, 6, 23, 0.5);
                        border-top: 1px solid rgba(71, 85, 105, 0.2);
                    }}

                    .footer-brand {{
                        font-size: 14px;
                        font-weight: 600;
                        color: #e2e8f0;
                        margin: 0 0 8px 0;
                    }}

                    .footer-links {{
                        margin: 16px 0;
                    }}

                    .footer-links a {{
                        color: #64748b;
                        text-decoration: none;
                        font-size: 12px;
                        margin: 0 12px;
                    }}

                    .footer-links a:hover {{
                        color: #38bdf8;
                    }}

                    .footer-copy {{
                        color: #475569;
                        font-size: 11px;
                        margin: 16px 0 0 0;
                    }}

                    /* Responsive */
                    @media only screen and (max-width: 600px) {{
                        .inner-content {{
                            padding: 32px 24px;
                        }}
                        .brand-name {{
                            font-size: 22px;
                        }}
                        .button {{
                            padding: 16px 32px;
                            font-size: 14px;
                        }}
                        .feature {{
                            display: block;
                            width: 100%;
                            margin-bottom: 12px;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="wrapper">
                    <div class="container">
                        <div class="accent-bar"></div>

                        <div class="inner-content">
                            <div class="header">
                                <div class="logo-container">
                                    <span class="logo-icon">☁️</span>
                                </div>
                                <h1 class="brand-name">AWS Cloud Health Dashboard</h1>
                                <p class="brand-tagline">Infrastructure Monitoring</p>
                            </div>

                            <div class="content">
                                <h2 class="greeting">Welcome aboard, {client_name}! 👋</h2>
                                <p>You're one step away from unlocking powerful cloud infrastructure monitoring. Verify your email to start receiving real-time security alerts, cost insights, and performance notifications.</p>

                                <div class="cta-section">
                                    <a href="{verification_link}" class="button">
                                        Verify Email Address →
                                    </a>

                                    <div class="link-fallback">
                                        <p>Button not working? Copy this link:</p>
                                        <code>{verification_link}</code>
                                    </div>
                                </div>

                                <div class="features">
                                    <div class="feature">
                                        <div class="feature-icon">🛡️</div>
                                        <p class="feature-text">Security Alerts</p>
                                    </div>
                                    <div class="feature">
                                        <div class="feature-icon">💰</div>
                                        <p class="feature-text">Cost Tracking</p>
                                    </div>
                                    <div class="feature">
                                        <div class="feature-icon">📊</div>
                                        <p class="feature-text">Real-time Metrics</p>
                                    </div>
                                </div>

                                <div class="security-notice">
                                    <span class="icon">🔐</span>
                                    <p><strong>Security Notice:</strong> This verification link expires in 24 hours. If you didn't create an account, please ignore this email—no action is required.</p>
                                </div>
                            </div>
                        </div>

                        <div class="footer">
                            <p class="footer-brand">☁️ AWS Cloud Health Dashboard</p>
                            <div class="footer-links">
                                <a href="#">Documentation</a>
                                <a href="#">Support</a>
                                <a href="#">Privacy</a>
                            </div>
                            <p class="footer-copy">© 2025 Cloud Health Dashboard. All rights reserved.<br>Securing your cloud infrastructure, one metric at a time.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            ═══════════════════════════════════════════
            AWS CLOUD HEALTH DASHBOARD
            Infrastructure Monitoring Platform
            ═══════════════════════════════════════════

            Welcome aboard, {client_name}! 👋

            You're one step away from unlocking powerful cloud 
            infrastructure monitoring.

            ▶ VERIFY YOUR EMAIL
            {verification_link}

            ───────────────────────────────────────────
            WHAT YOU'LL GET:
            ───────────────────────────────────────────
            🛡️  Real-time Security Alerts
            💰  Cost Tracking & Optimization
            📊  Performance Metrics & Insights

            ───────────────────────────────────────────
            🔐 SECURITY NOTICE
            ───────────────────────────────────────────
            This link expires in 24 hours.
            If you didn't request this, please ignore.

            ═══════════════════════════════════════════
            © 2025 AWS Cloud Health Dashboard
            Securing your cloud, one metric at a time.
            ═══════════════════════════════════════════
            """

            response = self.ses.send_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [recipient_email]},
                Message={
                    'Subject': {
                        'Data': '🚀 Verify Your Email — AWS Cloud Health Dashboard',
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

    async def send_test_notification(self,
                                     recipient_email: str,
                                     client_name: str,
                                     aws_account_id: str) -> bool:
        """
        Send a test email to verify email notification settings

        Args:
            recipient_email: Email address to send to
            client_name: Name of the client/company
            aws_account_id: AWS account ID

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # HTML email template
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                        border-radius: 10px 10px 0 0;
                    }}
                    .content {{
                        background: #f9f9f9;
                        padding: 30px;
                        border-radius: 0 0 10px 10px;
                    }}
                    .test-badge {{
                        display: inline-block;
                        background: #10b981;
                        color: white;
                        padding: 5px 15px;
                        border-radius: 20px;
                        font-size: 14px;
                        margin: 10px 0;
                    }}
                    .info-box {{
                        background: white;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 15px 0;
                        border-left: 4px solid #667eea;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 12px 24px;
                        background: #667eea;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin-top: 15px;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #ddd;
                        color: #666;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎉 Test Email Successful!</h1>
                    <div class="test-badge">✓ Email Notifications Working</div>
                </div>

                <div class="content">
                    <h2>Hello, {client_name}!</h2>

                    <p>This is a test email to confirm that your email notification settings are working correctly.</p>

                    <div class="info-box">
                        <strong>📧 Email Configuration</strong><br>
                        Recipient: {recipient_email}<br>
                        AWS Account: {aws_account_id}<br>
                        Status: <span style="color: #10b981;">✓ Active</span>
                    </div>

                    <p>You will receive notifications for:</p>
                    <ul>
                        <li>🔴 Critical security alerts</li>
                        <li>🟡 Warning notifications</li>
                        <li>📊 Daily summary reports (if enabled)</li>
                        <li>💰 Cost optimization recommendations</li>
                    </ul>

                    <p>If you received this email, your notification system is set up correctly!</p>

                    <center>
                        <a href="{self.frontend_url}/settings" class="button">Manage Settings</a>
                    </center>
                </div>

                <div class="footer">
                    <p>© 2025 AWS Cloud Health Dashboard</p>
                    <p>This is an automated test email from your cloud monitoring system.</p>
                </div>
            </body>
            </html>
            """

            # Plain text version
            text_body = f"""
            Test Email - AWS Cloud Health Dashboard

            Hello, {client_name}!

            This is a test email to confirm that your email notification settings are working correctly.

            Email Configuration:
            - Recipient: {recipient_email}
            - AWS Account: {aws_account_id}
            - Status: Active

            You will receive notifications for:
            - Critical security alerts
            - Warning notifications
            - Daily summary reports (if enabled)
            - Cost optimization recommendations

            If you received this email, your notification system is set up correctly!

            Manage your settings: {self.frontend_url}/settings

            © 2025 AWS Cloud Health Dashboard
            """

            # Send email
            response = self.ses.send_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [recipient_email]},
                Message={
                    'Subject': {
                        'Data': '✓ Test Email - Your Notifications Are Working!',
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

            logger.info(f"Test email sent to {recipient_email}")
            logger.debug(f"SES Response: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send test email: {e}", exc_info=True)
            return False









