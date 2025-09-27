
import boto3
from app.config import settings
from botocore.exceptions import ClientError, NoCredentialsError

class TestLogin :
    def __init__(self):
        self.ACCESS_KEY = settings.YOUR_AWS_ACCESS_KEY_ID
        self.SECRET_KEY = settings.YOUR_AWS_SECRET_ACCESS_KEY
        self.REGION =  settings.YOUR_AWS_REGION
        if self.ACCESS_KEY and self.SECRET_KEY :
            self.client = boto3.client(
                'ec2',
                aws_access_key_id= self.ACCESS_KEY,
                aws_secret_access_key= self.SECRET_KEY,
                region_name= self.REGION
            )
        else:

            self.client = boto3.client('ec2', region_name=self.REGION)

    def test_connection(self):
        try:
            sts_client = boto3.client('sts',
                                      aws_access_key_id= self.ACCESS_KEY if self.ACCESS_KEY else None,
                                      aws_secret_access_key= self.SECRET_KEY if self.SECRET_KEY else None,
                                      region_name= self.REGION
                                      )
            identity = sts_client.get_caller_identity()
            print('connection successfully!')
            print(f"Account ID: {identity['Account']}")
            print(f"User ARN :{identity['Arn']}")
            return True
        except NoCredentialsError:
            print(" No credentials found. Run 'aws configure' or provide keys.")
            return False
        except ClientError as e:
            print(f" Connection failed: {e}")
            return False

    def get_ec2_instances(self):
        try:
            response = self.client.describe_instances()
            instances = []

            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'id': instance['InstanceId'],
                        'type': instance['InstanceType'],
                        'state': instance['State']['Name']
                    })
            return instances
        except NoCredentialsError:
            print(" No credentials found. Run 'aws configure' or provide keys.")
            return []

if __name__ == "__main__":
    aws = TestLogin()
    if aws.test_connection() :
        print("\n" + "=" * 50)

    instances = aws.get_ec2_instances()
    print(f"Found {len(instances)} instances")
