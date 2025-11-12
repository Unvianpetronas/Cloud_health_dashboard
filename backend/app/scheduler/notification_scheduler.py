import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database.models import ClientModel
from app.services.email.ses_client import SESEmailService
from app.services.aws.client import AWSClientProvider
from app.services.aws.guardduty import GuardDutyScanner
import logging

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """
    Handles scheduled email notifications
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.client_model = ClientModel()
        self.email_service = SESEmailService()
        logger.info("Notification scheduler initialized")

    async def send_daily_summaries(self):
        """
        Main job that runs every 24 hours
        Sends daily summary emails to all opted-in verified users
        """
        try:
            logger.info("=" * 60)
            logger.info("Starting daily summary email job...")
            logger.info(f"Current time: {datetime.now().isoformat()}")

            # GET ALL USERS WITH DAILY SUMMARIES ENABLED
            clients = await self.client_model.get_clients_with_notifications_enabled()

            if not clients:
                logger.info("No clients with daily summaries enabled")
                return

            logger.info(f"Found {len(clients)} clients to send daily summaries")

            # Track statistics
            total_sent = 0
            total_failed = 0

            # SEND EMAIL TO EACH CLIENT
            for client in clients:
                try:
                    await self._send_client_summary(client)
                    total_sent += 1

                except Exception as e:
                    logger.error(f"Failed to send summary to {client.get('email')}: {e}")
                    total_failed += 1
                    continue

            logger.info("=" * 60)
            logger.info(f"Daily summary job completed!")
            logger.info(f"Sent: {total_sent}, Failed: {total_failed}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error in daily summary job: {e}", exc_info=True)

    async def _send_client_summary(self, client: dict):
        """
        Send daily summary email to a single client

        Args:
            client: Client dictionary from database
        """
        try:
            email = client.get('email')
            aws_account_id = client.get('aws_account_id')
            company_name = client.get('company_name', 'Your Company')

            if not email or not aws_account_id:
                logger.warning(f"Missing email or account ID for client")
                return

            logger.info(f"Generating summary for {email} ({aws_account_id})")

            # GENERATE DAILY SUMMARY DATA
            summary_data = await self._generate_daily_summary(client)

            # SEND EMAIL
            success = await self.email_service.send_daily_summary_email(
                recipient_email=email,
                client_name=company_name,
                summary_data=summary_data
            )

            if success:
                logger.info(f"Daily summary sent successfully to {email}")
            else:
                logger.error(f"Failed to send daily summary to {email}")

        except Exception as e:
            logger.error(f"Error sending summary to client: {e}", exc_info=True)
            raise

    async def _generate_daily_summary(self, client: dict) -> dict:
        """
        Generate summary data for a client's last 24 hours

        Args:
            client: Client dictionary with AWS credentials

        Returns:
            Dictionary with summary statistics
        """
        try:
            aws_account_id = client.get('aws_account_id')

            # Get decrypted credentials from client
            aws_access_key = client.get('aws_access_key')
            aws_secret_key = client.get('aws_secret_key')
            aws_region = client.get('aws_region', 'us-east-1')

            if not aws_access_key or not aws_secret_key:
                logger.warning(f"Missing AWS credentials for {aws_account_id}")
                return self._get_empty_summary()

            # Create AWS client provider
            client_provider = AWSClientProvider(
                access_key=aws_access_key,
                secret_key=aws_secret_key,
                region=aws_region
            )

            # SCAN GUARDDUTY FOR FINDINGS (LAST 24 HOURS)
            scanner = GuardDutyScanner(client_provider)

            # Get findings from last 24 hours
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)

            # Get findings count by severity
            findings = scanner.get_findings_summary(
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat()
            )

            summary_data = {
                'total_findings': findings.get('total', 0),
                'critical_count': findings.get('critical', 0),
                'high_count': findings.get('high', 0),
                'medium_count': findings.get('medium', 0),
                'low_count': findings.get('low', 0),
                'timestamp': datetime.now().isoformat(),
                'period': '24 hours',
                'aws_account_id': aws_account_id
            }

            logger.info(f"Summary for {aws_account_id}: {summary_data['total_findings']} findings")
            return summary_data

        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            return self._get_empty_summary()

    def _get_empty_summary(self) -> dict:
        """Return empty summary data structure"""
        return {
            'total_findings': 0,
            'critical_count': 0,
            'high_count': 0,
            'medium_count': 0,
            'low_count': 0,
            'timestamp': datetime.now().isoformat(),
            'period': '24 hours',
            'error': True
        }

    def start(self, hour: int = 8, minute: int = 0):
        """
        Start the scheduler

        Args:
            hour: Hour to run (0-23), default 8 AM
            minute: Minute to run (0-59), default 0
        """
        # SCHEDULE DAILY JOB
        self.scheduler.add_job(
            self.send_daily_summaries,
            CronTrigger(hour=hour, minute=minute),  # Run every day at specified time
            id='daily_summary_job',
            name='Send daily summary emails',
            replace_existing=True,
            misfire_grace_time=3600  # Allow 1 hour grace period if job misses
        )

        self.scheduler.start()
        logger.info(f"Notification scheduler started - Daily emails at {hour:02d}:{minute:02d}")
        logger.info(f"Next run time: {self.scheduler.get_job('daily_summary_job').next_run_time}")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Notification scheduler stopped")

    async def send_test_summary(self, email: str):
        """
        Send a test summary email (for testing purposes)

        Args:
            email: Email address to send test to
        """
        try:
            logger.info(f"Sending test summary to {email}")

            # Create test data
            test_data = {
                'total_findings': 15,
                'critical_count': 2,
                'high_count': 5,
                'medium_count': 6,
                'low_count': 2,
                'timestamp': datetime.now().isoformat(),
                'period': '24 hours (TEST)',
                'is_test': True
            }

            success = await self.email_service.send_daily_summary_email(
                recipient_email=email,
                client_name="Test Company",
                summary_data=test_data
            )

            if success:
                logger.info(f"Test summary sent to {email}")
                return True
            else:
                logger.error(f"Failed to send test summary to {email}")
                return False

        except Exception as e:
            logger.error(f"Error sending test summary: {e}", exc_info=True)
            return False


notification_scheduler = NotificationScheduler()