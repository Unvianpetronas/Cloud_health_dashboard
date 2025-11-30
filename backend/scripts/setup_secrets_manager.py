#!/usr/bin/env python3
"""
Setup script for AWS Secrets Manager with KMS encryption.

This script creates the necessary KMS key for Secrets Manager encryption.
Run this once during initial setup.

Usage:
    python scripts/setup_secrets_manager.py

Requirements:
    - AWS credentials configured (via ~/.aws/credentials or environment variables)
    - IAM permissions for KMS key creation
"""

import boto3
import sys
from botocore.exceptions import ClientError


def create_kms_key(region='ap-southeast-1'):
    """
    Create KMS key for Secrets Manager encryption.

    Args:
        region: AWS region (default: ap-southeast-1)

    Returns:
        str: KMS key ID if successful, None otherwise
    """
    kms = boto3.client('kms', region_name=region)

    try:
        # Create KMS key
        print(f"Creating KMS key in {region}...")
        response = kms.create_key(
            Description='Cloud Health Dashboard - Secrets Manager encryption key',
            KeyUsage='ENCRYPT_DECRYPT',
            Origin='AWS_KMS',
            MultiRegion=False,
            Tags=[
                {'TagKey': 'Application', 'TagValue': 'cloud-health-dashboard'},
                {'TagKey': 'Purpose', 'TagValue': 'secrets-encryption'},
                {'TagKey': 'ManagedBy', 'TagValue': 'setup-script'}
            ]
        )

        key_id = response['KeyMetadata']['KeyId']
        key_arn = response['KeyMetadata']['Arn']

        print(f"✅ KMS key created successfully!")
        print(f"   Key ID: {key_id}")
        print(f"   Key ARN: {key_arn}")

        # Create alias
        alias_name = 'alias/cloud-health-kms'
        print(f"\nCreating alias: {alias_name}")

        try:
            kms.create_alias(
                AliasName=alias_name,
                TargetKeyId=key_id
            )
            print(f"✅ Alias created successfully: {alias_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                print(f"⚠️  Alias already exists: {alias_name}")
                print(f"   Updating alias to point to new key...")
                kms.update_alias(
                    AliasName=alias_name,
                    TargetKeyId=key_id
                )
                print(f"✅ Alias updated successfully")
            else:
                raise

        # Enable automatic key rotation (security best practice)
        print("\nEnabling automatic key rotation...")
        kms.enable_key_rotation(KeyId=key_id)
        print("✅ Automatic key rotation enabled (365 days)")

        return key_id

    except ClientError as e:
        error_code = e.response['Error']['Code']

        if error_code == 'AccessDeniedException':
            print("❌ ERROR: Access denied. You need kms:CreateKey permission.")
            print("   Ask your AWS administrator to grant you KMS permissions.")
        elif error_code == 'LimitExceededException':
            print("❌ ERROR: KMS key limit exceeded for your account.")
            print("   You may need to delete unused keys or request a limit increase.")
        else:
            print(f"❌ ERROR: {e}")

        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def test_secrets_manager(region='ap-southeast-1'):
    """
    Test Secrets Manager setup by creating a test secret.

    Args:
        region: AWS region

    Returns:
        bool: True if test successful, False otherwise
    """
    sm = boto3.client('secretsmanager', region_name=region)
    test_secret_name = 'cloud-health/test-secret'

    try:
        print(f"\nTesting Secrets Manager...")
        print(f"Creating test secret: {test_secret_name}")

        sm.create_secret(
            Name=test_secret_name,
            Description='Test secret for Cloud Health Dashboard setup',
            SecretString='{"test": "value"}',
            KmsKeyId='alias/cloud-health-kms'
        )

        print("✅ Test secret created successfully")

        # Retrieve the secret
        print("Retrieving test secret...")
        response = sm.get_secret_value(SecretId=test_secret_name)
        print("✅ Test secret retrieved successfully")

        # Clean up
        print("Cleaning up test secret...")
        sm.delete_secret(
            SecretId=test_secret_name,
            ForceDeleteWithoutRecovery=True
        )
        print("✅ Test secret deleted")

        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']

        if error_code == 'ResourceExistsException':
            print(f"⚠️  Test secret already exists, cleaning up...")
            try:
                sm.delete_secret(
                    SecretId=test_secret_name,
                    ForceDeleteWithoutRecovery=True
                )
                print("✅ Cleaned up existing test secret")
                return True
            except:
                pass

        print(f"❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected test error: {e}")
        return False


def main():
    """Main setup function."""
    print("="*70)
    print("Cloud Health Dashboard - Secrets Manager Setup")
    print("="*70)

    # Get region from user or use default
    region = input("\nEnter AWS region (default: ap-southeast-1): ").strip()
    if not region:
        region = 'ap-southeast-1'

    print(f"\nUsing region: {region}")

    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"\n✅ AWS credentials found")
        print(f"   Account: {identity['Account']}")
        print(f"   User/Role: {identity['Arn']}")
    except Exception as e:
        print(f"\n❌ ERROR: Cannot access AWS credentials")
        print(f"   {e}")
        print("\nPlease configure AWS credentials:")
        print("   - Run: aws configure")
        print("   - Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        return 1

    # Create KMS key
    print("\n" + "="*70)
    print("Step 1: Creating KMS Key")
    print("="*70)

    key_id = create_kms_key(region)
    if not key_id:
        print("\n❌ Setup failed: Could not create KMS key")
        return 1

    # Test Secrets Manager
    print("\n" + "="*70)
    print("Step 2: Testing Secrets Manager")
    print("="*70)

    if not test_secrets_manager(region):
        print("\n⚠️  Warning: Secrets Manager test failed")
        print("   The KMS key was created, but there may be permission issues.")
        print("   Check IAM permissions for Secrets Manager.")

    # Success message
    print("\n" + "="*70)
    print("✅ Setup Complete!")
    print("="*70)
    print("\nSecrets Manager is now ready to use.")
    print("\nNext steps:")
    print("1. Restart your backend server")
    print("2. Secrets Manager will automatically encrypt credentials on new logins")
    print("3. Existing credentials in DynamoDB will be migrated on next access")
    print("\nSecurity recommendations:")
    print("- Keep KMS key alias: alias/cloud-health-kms")
    print("- Monitor KMS key usage in CloudWatch")
    print("- Review KMS key policy regularly")
    print("- Automatic key rotation is enabled (365 days)")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
