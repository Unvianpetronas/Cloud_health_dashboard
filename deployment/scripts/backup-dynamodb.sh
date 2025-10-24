#!/bin/bash
set -e

S3_BUCKET="cloudhealth-dynamodb-backups-$(aws sts get-caller-identity --query Account --output text)"
BACKUP_DATE=$(date +%Y-%m-%d)
TABLES=("CloudHealthClients" "CloudHealthMetrics" "CloudHealthCosts" "SecurityFindings" "Recommendations")

echo "Backing up DynamoDB to S3: $S3_BUCKET"

for TABLE in "${TABLES[@]}"; do
    echo "Backing up $TABLE..."
    
    aws dynamodb scan --table-name "$TABLE" --output json > "/tmp/${TABLE}.json"
    gzip "/tmp/${TABLE}.json"
    
    aws s3 cp "/tmp/${TABLE}.json.gz" \
        "s3://${S3_BUCKET}/${TABLE}/${BACKUP_DATE}.json.gz"
    
    rm "/tmp/${TABLE}.json.gz"
    echo "✓ $TABLE backed up"
done

echo "Backup completed!"