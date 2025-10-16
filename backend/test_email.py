

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.email.ses_client import email_service


async def test_verification_email():
    """Test sending a verification email"""

    print("Testing Verification Email...")

    success = await email_service.send_verification_email(
        recipient_email="tuanmarcus2005@gmail.com",  #
        verification_token="test-token-abc123",
        client_name="Test Company"
    )

    if success:
        print("Email sent successfully!")
        print("Check your inbox")
    else:
        print("Failed to send email")
        print("Check that SES is set up correctly")


async def test_critical_alert():
    """Test sending a critical alert"""

    print("\nTesting Critical Alert Email...")

    success = await email_service.send_critical_alert(
        recipient_email="tuanmarcus2005@gmail.com",
        alert_data={
            'severity': 'HIGH',
            'title': 'Unauthorized EC2 Access Detected',
            'description': 'An EC2 instance is being accessed from an unusual IP address',
            'service': 'EC2',
            'resource_id': 'i-test123456',
            'region': 'ap-southeast-1',
            'timestamp': '2025-10-13T10:30:00Z',
            'finding_id': 'finding-test-789'
        }
    )

    if success:
        print("Alert sent successfully!")
        print("Check your inbox")
    else:
        print("Failed to send alert")


async def main():
    print("=" * 60)
    print("Email Service Test")
    print("=" * 60)

    await test_verification_email()
    await test_critical_alert()

    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())