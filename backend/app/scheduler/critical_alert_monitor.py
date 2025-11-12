from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database.models import ClientModel
from app.services.email.ses_client import SESEmailService
from app.services.aws.client import AWSClientProvider
from app.services.aws.guardduty import GuardDutyScanner
import logging

logger = logging.getLogger(__name__)


class CriticalAlertMonitor:
    """
    Monitors GuardDuty for critical findings and sends immediate alerts
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.client_model = ClientModel()
        self.email_service = SESEmailService()
        self.sent_alerts = set()  # Track sent alerts to avoid duplicates
        logger.info("Critical alert monitor initialized")

    async def scan_for_critical_findings(self):
        """
        Main monitoring job - runs every X minutes
        Scans all active clients for NEW critical findings
        """
        try:
            logger.info("Scanning for critical findings...")

            # Get all active clients
            clients = await self.client_model.get_all_active_clients()

            if not clients:
                return

            total_alerts_sent = 0

            for client in clients:
                try:
                    # Check if user has critical alerts enabled
                    notification_prefs = client.get('notification_preferences', {})
                    if not notification_prefs.get('critical_alerts', False):
                        continue

                    # Check if email verified
                    if not client.get('email_verified', False):
                        continue

                    # Scan this client's GuardDuty
                    alerts_sent = await self._scan_client_guardduty(client)
                    total_alerts_sent += alerts_sent

                except Exception as e:
                    logger.error(f"Error scanning client {client.get('aws_account_id')}: {e}")
                    continue

            if total_alerts_sent > 0:
                logger.info(f"Sent {total_alerts_sent} critical alert(s)")

        except Exception as e:
            logger.error(f"Error in critical alert monitoring: {e}", exc_info=True)

    async def _scan_client_guardduty(self, client: dict) -> int:
        """
        Scan a single client's GuardDuty for critical findings

        Args:
            client: Client dictionary from database

        Returns:
            Number of alerts sent
        """
        try:
            aws_account_id = client.get('aws_account_id')
            email = client.get('email')
            company_name = client.get('company_name', 'Your Company')

            # Get AWS credentials
            aws_access_key = client.get('aws_access_key')
            aws_secret_key = client.get('aws_secret_key')
            aws_region = client.get('aws_region', 'us-east-1')

            if not aws_access_key or not aws_secret_key:
                return 0

            # Create AWS client
            client_provider = AWSClientProvider(
                access_key=aws_access_key,
                secret_key=aws_secret_key,
                region=aws_region
            )

            # Scan GuardDuty for CRITICAL findings in last 15 minutes
            scanner = GuardDutyScanner(client_provider)

            # Get recent critical findings
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=15)  # Last 15 minutes

            critical_findings = scanner.get_critical_findings(
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat()
            )

            if not critical_findings:
                return 0

            # Send alert for each NEW critical finding
            alerts_sent = 0
            for finding in critical_findings:
                finding_id = finding.get('Id')

                # Check if we already sent alert for this finding
                alert_key = f"{aws_account_id}:{finding_id}"
                if alert_key in self.sent_alerts:
                    continue  # Skip, already sent

                # Send alert email
                alert_data = self._format_finding_data(finding)

                success = await self.email_service.send_critical_alert(
                    recipient_email=email,
                    alert_data=alert_data
                )

                if success:
                    logger.info(f"Critical alert sent to {email} for finding {finding_id}")
                    self.sent_alerts.add(alert_key)
                    alerts_sent += 1

                    # Clean old alerts from memory (keep last 1000)
                    if len(self.sent_alerts) > 1000:
                        # Remove oldest half
                        to_remove = list(self.sent_alerts)[:500]
                        for key in to_remove:
                            self.sent_alerts.discard(key)

            return alerts_sent

        except Exception as e:
            logger.error(f"Error scanning GuardDuty: {e}", exc_info=True)
            return 0

    def _format_finding_data(self, finding: dict) -> dict:
        """
        Format GuardDuty finding into alert data structure

        Args:
            finding: Raw GuardDuty finding

        Returns:
            Formatted alert data for email template
        """
        return {
            'severity': self._get_severity_label(finding.get('severity',7.0)),
            'title': finding.get('Title', 'Security Issue Detected'),
            'description': finding.get('Description', 'A critical security issue was detected'),
            'service': finding.get('Service', {}).get('ServiceName', 'Unknown'),
            'resource_id': self._extract_resource_id(finding),
            'region': finding.get('Region', 'N/A'),
            'timestamp': finding.get('UpdatedAt', finding.get('CreatedAt', 'N/A')),
            'finding_id': finding.get('Id', 'N/A'),
            'account_id': finding.get('AccountId', 'N/A')
        }

    def _extract_resource_id(self, finding: dict) -> str:
        """Extract resource ID from finding"""
        resource = finding.get('Resource', {})

        # Try different resource types
        if 'InstanceDetails' in resource:
            return resource['InstanceDetails'].get('InstanceId', 'N/A')
        elif 'AccessKeyDetails' in resource:
            return resource['AccessKeyDetails'].get('AccessKeyId', 'N/A')
        elif 'S3BucketDetails' in resource:
            buckets = resource.get('S3BucketDetails', [])
            if buckets:
                return buckets[0].get('Name', 'N/A')

        return 'N/A'

    def _get_severity_label(self, severity) -> str:
        """Convert numeric GuardDuty severity to string label"""
        if isinstance(severity, str):
            return severity.upper()

        if severity >= 7.0:
            return 'CRITICAL'
        elif severity >= 4.0:
            return 'HIGH'
        elif severity >= 2.0:
            return 'MEDIUM'
        else:
            return 'LOW'

    def start(self, interval_minutes: int = 10):
        """
        Start the critical alert monitor

        Args:
            interval_minutes: How often to scan (default: every 10 minutes)
        """
        # Schedule monitoring job
        self.scheduler.add_job(
            self.scan_for_critical_findings,
            IntervalTrigger(minutes=interval_minutes),
            id='critical_alert_monitor',
            name='Monitor for critical GuardDuty findings',
            replace_existing=True,
            misfire_grace_time=300  # 5 minutes grace
        )

        self.scheduler.start()
        logger.info(f"Critical alert monitor started - Scanning every {interval_minutes} minutes")

    def stop(self):
        """Stop the monitor"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Critical alert monitor stopped")

    async def send_test_alert(self, email: str):
        """Send a test critical alert"""
        try:
            test_data = {
                'severity': 'CRITICAL',
                'title': 'TEST: Unauthorized EC2 Access Detected',
                'description': 'This is a TEST alert. An EC2 instance is being accessed from an unusual IP address.',
                'service': 'EC2',
                'resource_id': 'i-test123456789',
                'region': 'us-east-1',
                'timestamp': datetime.now().isoformat(),
                'finding_id': 'test-finding-12345',
                'is_test': True
            }

            success = await self.email_service.send_critical_alert(
                recipient_email=email,
                alert_data=test_data
            )

            return success

        except Exception as e:
            logger.error(f"Error sending test alert: {e}")
            return False


# Global instance
critical_alert_monitor = CriticalAlertMonitor()