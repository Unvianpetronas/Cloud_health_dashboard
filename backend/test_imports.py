import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.config import settings
    print(f" Import successful!")
    print(f"App Name: {settings.APP_NAME}")
    print(f"AWS Region: {settings.AWS_REGION}")
    print(f"Metrics Table: {settings.METRICS_TABLE}")
except ImportError as e:
    print(f" Import failed: {e}")