
TABLE_DEFINITIONS = [
    {
        "TableName": "CloudHealthClients",
        "KeySchema": [
            {"AttributeName": "pk", "KeyType": "HASH"},   # CLIENT#client-id
            {"AttributeName": "sk", "KeyType": "RANGE"}   # METADATA
        ],
        "AttributeDefinitions": [
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
            {"AttributeName": "aws_account_id", "AttributeType": "S"},
             {'AttributeName': 'email', 'AttributeType': 'S'}
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "AwsAccountIdIndex",
                "KeySchema": [
                    {"AttributeName": "aws_account_id", "KeyType": "HASH"}
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                'IndexName': 'EmailIndex',
                'KeySchema': [
                    {'AttributeName': 'email', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        "BillingMode": "PAY_PER_REQUEST"
    },

    {
        "TableName": "CloudHealthMetrics",
        "KeySchema": [
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
            {"AttributeName": "gsi1_pk", "AttributeType": "S"}
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "MetricNameIndex",
                "KeySchema": [
                    {"AttributeName": "gsi1_pk", "KeyType": "HASH"},
                    {"AttributeName": "sk", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },

    {
        "TableName": "CloudHealthCosts",
        "KeySchema": [
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"}
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },

    {
        "TableName": "SecurityFindings",
        "KeySchema": [
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"}
        ],
        "BillingMode": "PAY_PER_REQUEST"
    },

    {
        "TableName": "Recommendations",
        "KeySchema": [
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"}
        ],
        "BillingMode": "PAY_PER_REQUEST"
    }
]