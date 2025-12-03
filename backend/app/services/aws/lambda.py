from typing import Dict
from client import AWSClientProvider
from base_scanner import BaseAWSScanner
import logging
logger = logging.getLogger(__name__)

class LambdaScanner(BaseAWSScanner):
    def __init__(self):
        self.client_provider = AWSClientProvider()
        self.client = self.client_provider.get_client("lambda")

    def list_lambda_functions_in_region(self) -> Dict:
        """
        List all lambda functions.
        """
        try:
             paginator = self.client.get_paginator("list_functions")
             results = []
             count = 0
             for page in paginator.paginate():
                for func in page["Functions"]:
                    count += 1
                    results.append({
                        "name": func["FunctionName"],
                        "runtime": func["Runtime"],
                        "code_size": func["CodeSize"],
                        "memory_size": func["MemorySize"],
                        "last_modified": func["LastModified"],
                        "arn": func["FunctionArn"]
                    })
                return {
                    "total": count,
                    "functions": results
                }
        except Exception as e:
            logger.error(f"Error listing lambda functions: {e}")
            return []