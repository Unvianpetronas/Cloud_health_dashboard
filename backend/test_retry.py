from app.services.aws.ec2 import EC2Scanner
from app.services.aws.client import AWSClientProvider

provider = AWSClientProvider('INVALID', 'CREDENTIALS', 'us-east-1')
scanner = EC2Scanner(provider)

try:
    # This will fail and retry 3 times
    result = scanner.scan_all_regions()
except Exception as e:
    print(f"Failed after retries (expected): {e}")
    # Check logs - should show 3 retry attempts

# Run: python test_retry.py
# Should see log messages about retrying