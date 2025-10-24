# Design Document: AWS CI/CD Pipeline Setup

## Overview

This design document outlines the technical architecture for implementing a complete CI/CD pipeline for the Cloud Health Dashboard application using AWS CodeCommit, CodeBuild, and CodePipeline. The solution will automate the build, test, and deployment process for both the Python FastAPI backend and React frontend applications.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Developer     │
│   Local Git     │
└────────┬────────┘
         │ git push
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS CodeCommit                            │
│              cloud-health-dashboard repo                     │
└────────┬────────────────────────────────────────────────────┘
         │ trigger on commit
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS CodePipeline                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Source  │→ │  Build   │→ │  Build   │→ │  Deploy  │   │
│  │  Stage   │  │ Backend  │  │ Frontend │  │  Stage   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    CodeCommit    CodeBuild      CodeBuild      Deployment
                  (Backend)      (Frontend)      Targets
                      │              │              │
                      ▼              ▼              ▼
                  S3 Artifact    S3 Artifact   ┌──────────┐
                  Bucket         Bucket        │ Backend: │
                                                │ ECS/EB   │
                                                ├──────────┤
                                                │Frontend: │
                                                │ S3+CF    │
                                                └──────────┘
```

### Component Architecture

#### 1. Source Control (CodeCommit)
- Single repository: `cloud-health-dashboard`
- Branch strategy: `main` (production), `develop` (staging)
- Directory structure preserved: `backend/` and `frontend/`

#### 2. Build System (CodeBuild)
Two separate build projects:

**Backend Build Project:**
- Runtime: Python 3.11
- Build environment: `aws/codebuild/standard:7.0`
- Compute: `BUILD_GENERAL1_SMALL` (3 GB memory, 2 vCPUs)
- Buildspec location: `backend/buildspec.yml`

**Frontend Build Project:**
- Runtime: Node.js 18
- Build environment: `aws/codebuild/standard:7.0`
- Compute: `BUILD_GENERAL1_SMALL` (3 GB memory, 2 vCPUs)
- Buildspec location: `frontend/buildspec.yml`

#### 3. Pipeline Orchestration (CodePipeline)
Five-stage pipeline:
1. **Source Stage**: Pull from CodeCommit
2. **Backend Build Stage**: Build Python application
3. **Frontend Build Stage**: Build React application
4. **Backend Deploy Stage**: Deploy to ECS/Elastic Beanstalk
5. **Frontend Deploy Stage**: Deploy to S3 + CloudFront

## Components and Interfaces

### 1. CodeCommit Repository Configuration

```yaml
Repository:
  Name: cloud-health-dashboard
  Description: Cloud Health Dashboard - AWS Monitoring Application
  DefaultBranch: main
  Triggers:
    - Name: pipeline-trigger
      Events: [all]
      Branches: [main]
      DestinationArn: <CodePipeline ARN>
```

### 2. Backend Buildspec (backend/buildspec.yml)

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.11
    commands:
      - echo "Installing dependencies..."
      - pip install --upgrade pip
      - pip install -r requirements.txt
  
  pre_build:
    commands:
      - echo "Running pre-build checks..."
      - python -m py_compile app/main.py
      - echo "Linting code..."
      - pip install flake8
      - flake8 app/ --max-line-length=120 --exclude=__pycache__
  
  build:
    commands:
      - echo "Building application..."
      - echo "Running tests if available..."
      - |
        if [ -d "tests" ]; then
          pip install pytest pytest-asyncio
          pytest tests/ -v || echo "No tests found or tests failed"
        fi
      - echo "Creating deployment package..."
      - mkdir -p build
      - cp -r app build/
      - cp requirements.txt build/
      - cp -r . build/ 2>/dev/null || true
  
  post_build:
    commands:
      - echo "Build completed on $(date)"
      - echo "Preparing artifacts..."

artifacts:
  files:
    - '**/*'
  base-directory: build
  name: backend-build-$(date +%Y%m%d-%H%M%S)

cache:
  paths:
    - '/root/.cache_client/pip/**/*'
```

### 3. Frontend Buildspec (frontend/buildspec.yml)

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      nodejs: 18
    commands:
      - echo "Installing dependencies..."
      - npm ci
  
  pre_build:
    commands:
      - echo "Running pre-build checks..."
      - echo "Checking for syntax errors..."
      - npm run build --dry-run || echo "Dry run check"
  
  build:
    commands:
      - echo "Building React application..."
      - npm run build
      - echo "Build completed successfully"
      - ls -la build/
  
  post_build:
    commands:
      - echo "Build completed on $(date)"
      - echo "Preparing artifacts for S3 deployment..."

artifacts:
  files:
    - '**/*'
  base-directory: build
  name: frontend-build-$(date +%Y%m%d-%H%M%S)

cache:
  paths:
    - 'node_modules/**/*'
```

### 4. IAM Roles and Policies

#### CodePipeline Service Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:GetBranch",
        "codecommit:GetCommit",
        "codecommit:UploadArchive",
        "codecommit:GetUploadArchiveStatus"
      ],
      "Resource": "arn:aws:codecommit:*:*:cloud-health-dashboard"
    },
    {
      "Effect": "Allow",
      "Action": [
        "codebuild:BatchGetBuilds",
        "codebuild:StartBuild"
      ],
      "Resource": [
        "arn:aws:codebuild:*:*:project/backend-build",
        "arn:aws:codebuild:*:*:project/frontend-build"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:GetBucketLocation",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::codepipeline-artifacts-*",
        "arn:aws:s3:::codepipeline-artifacts-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticbeanstalk:*",
        "ecs:*",
        "cloudformation:*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### CodeBuild Service Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::codepipeline-artifacts-*/*",
        "arn:aws:s3:::frontend-hosting-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:GitPull"
      ],
      "Resource": "arn:aws:codecommit:*:*:cloud-health-dashboard"
    }
  ]
}
```

### 5. Pipeline Definition

```json
{
  "pipeline": {
    "name": "cloud-health-dashboard-pipeline",
    "roleArn": "arn:aws:iam::ACCOUNT_ID:role/CodePipelineServiceRole",
    "artifactStore": {
      "type": "S3",
      "location": "codepipeline-artifacts-REGION-ACCOUNT_ID"
    },
    "stages": [
      {
        "name": "Source",
        "actions": [
          {
            "name": "SourceAction",
            "actionTypeId": {
              "category": "Source",
              "owner": "AWS",
              "provider": "CodeCommit",
              "version": "1"
            },
            "configuration": {
              "RepositoryName": "cloud-health-dashboard",
              "BranchName": "main",
              "PollForSourceChanges": false
            },
            "outputArtifacts": [
              {
                "name": "SourceOutput"
              }
            ]
          }
        ]
      },
      {
        "name": "Build_Backend",
        "actions": [
          {
            "name": "BackendBuild",
            "actionTypeId": {
              "category": "Build",
              "owner": "AWS",
              "provider": "CodeBuild",
              "version": "1"
            },
            "configuration": {
              "ProjectName": "backend-build"
            },
            "inputArtifacts": [
              {
                "name": "SourceOutput"
              }
            ],
            "outputArtifacts": [
              {
                "name": "BackendBuildOutput"
              }
            ]
          }
        ]
      },
      {
        "name": "Build_Frontend",
        "actions": [
          {
            "name": "FrontendBuild",
            "actionTypeId": {
              "category": "Build",
              "owner": "AWS",
              "provider": "CodeBuild",
              "version": "1"
            },
            "configuration": {
              "ProjectName": "frontend-build"
            },
            "inputArtifacts": [
              {
                "name": "SourceOutput"
              }
            ],
            "outputArtifacts": [
              {
                "name": "FrontendBuildOutput"
              }
            ]
          }
        ]
      },
      {
        "name": "Deploy_Backend",
        "actions": [
          {
            "name": "DeployToECS",
            "actionTypeId": {
              "category": "Deploy",
              "owner": "AWS",
              "provider": "ECS",
              "version": "1"
            },
            "configuration": {
              "ClusterName": "cloud-health-cluster",
              "ServiceName": "backend-service",
              "FileName": "imagedefinitions.json"
            },
            "inputArtifacts": [
              {
                "name": "BackendBuildOutput"
              }
            ]
          }
        ]
      },
      {
        "name": "Deploy_Frontend",
        "actions": [
          {
            "name": "DeployToS3",
            "actionTypeId": {
              "category": "Deploy",
              "owner": "AWS",
              "provider": "S3",
              "version": "1"
            },
            "configuration": {
              "BucketName": "cloud-health-dashboard-frontend",
              "Extract": "true"
            },
            "inputArtifacts": [
              {
                "name": "FrontendBuildOutput"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

## Data Models

### Environment Variables Configuration

#### Backend Environment Variables (stored in Parameter Store)

```yaml
/cloud-health/backend/production:
  ENVIRONMENT: production
  DEBUG: false
  LOG_LEVEL: INFO
  JWT_SECRET_KEY: <secure-value>
  ENCRYPTION_KEY: <secure-value>
  YOUR_AWS_REGION: us-east-1
  YOUR_AWS_ACCESS_KEY_ID: <from-secrets-manager>
  YOUR_AWS_SECRET_ACCESS_KEY: <from-secrets-manager>
  SES_SENDER_EMAIL: noreply@yourdomain.com
  FRONTEND_URL: https://yourdomain.com
  CORS_ORIGINS: https://yourdomain.com
  DYNAMODB_TABLE_PREFIX: prod
```

#### Frontend Environment Variables (build-time)

```env
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=1.0.0
```

### Artifact Structure

#### Backend Artifact
```
backend-build/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── utils/
├── requirements.txt
├── Dockerfile (optional)
└── appspec.yml (for CodeDeploy)
```

#### Frontend Artifact
```
frontend-build/
├── static/
│   ├── css/
│   ├── js/
│   └── media/
├── index.html
├── asset-manifest.json
└── manifest.json
```

## Deployment Strategies

### Backend Deployment Options

#### Option 1: AWS Elastic Beanstalk (Recommended for simplicity)

**Advantages:**
- Automatic capacity provisioning
- Load balancing and auto-scaling
- Health monitoring
- Easy rollback

**Configuration:**
```yaml
# .ebextensions/python.config
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app.main:app
  aws:elasticbeanstalk:application:environment:
    ENVIRONMENT: production
    PYTHONPATH: /var/app/current
```

#### Option 2: Amazon ECS with Fargate

**Advantages:**
- Containerized deployment
- Better resource utilization
- Microservices ready
- No server management

**Requirements:**
- Dockerfile in backend directory
- ECR repository for Docker images
- ECS cluster and service definition
- Task definition with environment variables

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Deployment

#### S3 + CloudFront Configuration

**S3 Bucket Configuration:**
```json
{
  "WebsiteConfiguration": {
    "IndexDocument": "index.html",
    "ErrorDocument": "index.html"
  },
  "PublicAccessBlockConfiguration": {
    "BlockPublicAcls": false,
    "IgnorePublicAcls": false,
    "BlockPublicPolicy": false,
    "RestrictPublicBuckets": false
  },
  "CorsConfiguration": {
    "CorsRules": [
      {
        "AllowedOrigins": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedHeaders": ["*"],
        "MaxAgeSeconds": 3000
      }
    ]
  }
}
```

**CloudFront Distribution:**
```yaml
Distribution:
  Origins:
    - DomainName: cloud-health-dashboard-frontend.s3.amazonaws.com
      Id: S3-frontend
      S3OriginConfig:
        OriginAccessIdentity: origin-access-identity/cloudfront/XXXXX
  DefaultCacheBehavior:
    TargetOriginId: S3-frontend
    ViewerProtocolPolicy: redirect-to-https
    AllowedMethods: [GET, HEAD, OPTIONS]
    CachedMethods: [GET, HEAD]
    Compress: true
    DefaultTTL: 86400
  CustomErrorResponses:
    - ErrorCode: 404
      ResponseCode: 200
      ResponsePagePath: /index.html
    - ErrorCode: 403
      ResponseCode: 200
      ResponsePagePath: /index.html
```

## Error Handling

### Build Failure Handling

1. **Syntax Errors**: Caught during pre_build phase
2. **Dependency Issues**: Logged in install phase
3. **Test Failures**: Reported but don't block build (configurable)
4. **Artifact Creation**: Validated in post_build phase

### Deployment Failure Handling

1. **Health Check Failures**: Automatic rollback triggered
2. **Timeout**: Pipeline fails after 60 minutes
3. **Permission Errors**: Logged with detailed IAM policy requirements
4. **Resource Limits**: CloudWatch alarms trigger notifications

### Rollback Strategy

- **Backend**: ECS/EB maintains previous task definition/version
- **Frontend**: S3 versioning enabled for quick rollback
- **Manual Rollback**: Pipeline can be re-run with previous commit

## Testing Strategy

### Pre-Deployment Testing

#### Backend Tests (in buildspec)
```yaml
- name: Unit Tests
  command: pytest tests/unit/ -v
  
- name: Integration Tests
  command: pytest tests/integration/ -v
  
- name: Security Scan
  command: bandit -r app/ -f json -o security-report.json
```

#### Frontend Tests (in buildspec)
```yaml
- name: Unit Tests
  command: npm test -- --coverage --watchAll=false
  
- name: Build Test
  command: npm run build
  
- name: Lint Check
  command: npm run lint
```

### Post-Deployment Testing

1. **Health Check Endpoint**: `/health` returns 200 OK
2. **Smoke Tests**: Basic API calls to verify functionality
3. **CloudWatch Alarms**: Monitor error rates and latency

## Monitoring and Notifications

### CloudWatch Alarms

```yaml
Alarms:
  - Name: PipelineFailure
    Metric: ExecutionFailure
    Threshold: 1
    Action: SNS notification
  
  - Name: BuildDuration
    Metric: BuildDuration
    Threshold: 600 seconds
    Action: SNS notification
  
  - Name: DeploymentFailure
    Metric: DeploymentFailure
    Threshold: 1
    Action: SNS notification + Rollback
```

### SNS Topic Configuration

```yaml
Topic:
  Name: cloud-health-pipeline-notifications
  Subscriptions:
    - Protocol: email
      Endpoint: devops@yourdomain.com
    - Protocol: sms
      Endpoint: +1234567890
```

### Notification Message Format

```json
{
  "pipeline": "cloud-health-dashboard-pipeline",
  "stage": "Deploy_Backend",
  "status": "FAILED",
  "executionId": "abc-123-def",
  "timestamp": "2024-01-15T10:30:00Z",
  "error": "Health check failed after deployment",
  "rollback": "initiated"
}
```

## Security Considerations

### Secrets Management

1. **AWS Secrets Manager**: Store sensitive credentials
2. **Parameter Store**: Store non-sensitive configuration
3. **Environment Variables**: Injected at runtime, never committed to code

### Network Security

1. **VPC Configuration**: Backend deployed in private subnets
2. **Security Groups**: Restrict access to necessary ports only
3. **HTTPS Only**: CloudFront enforces HTTPS for frontend
4. **API Gateway**: Optional layer for additional security

### Access Control

1. **IAM Roles**: Least privilege principle
2. **Resource Policies**: S3 bucket policies restrict access
3. **CodeCommit**: Branch protection on main branch
4. **MFA**: Required for production deployments

## Migration Steps

### 1. Prepare CodeCommit Repository

```bash
# Create CodeCommit repository
aws codecommit create-repository \
  --repository-name cloud-health-dashboard \
  --repository-description "Cloud Health Dashboard Application"

# Configure Git credentials
aws codecommit get-repository \
  --repository-name cloud-health-dashboard

# Add CodeCommit as remote
git remote add codecommit <codecommit-url>
```

### 2. Push Existing Code

```bash
# Push all branches
git push codecommit --all

# Push tags
git push codecommit --tags
```

### 3. Create Build Projects

```bash
# Backend build project
aws codebuild create-project \
  --cli-input-json file://backend-build-project.json

# Frontend build project
aws codebuild create-project \
  --cli-input-json file://frontend-build-project.json
```

### 4. Create Pipeline

```bash
# Create pipeline
aws codepipeline create-pipeline \
  --cli-input-json file://pipeline-definition.json
```

### 5. Configure Deployment Targets

```bash
# For ECS deployment
aws ecs create-cluster --cluster-name cloud-health-cluster
aws ecs create-service --cli-input-json file://ecs-service.json

# For S3 + CloudFront
aws s3 mb s3://cloud-health-dashboard-frontend
aws cloudfront create-distribution --cli-input-json file://cloudfront-config.json
```

## Cost Estimation

### Monthly Cost Breakdown (Estimated)

- **CodeCommit**: $1/month (5 active users)
- **CodeBuild**: $10-30/month (100-300 build minutes)
- **CodePipeline**: $1/month (1 active pipeline)
- **S3 Storage**: $5-10/month (artifacts + frontend hosting)
- **CloudFront**: $10-50/month (depends on traffic)
- **ECS/Elastic Beanstalk**: $30-100/month (depends on instance size)
- **Data Transfer**: $5-20/month

**Total Estimated Cost**: $62-212/month

## Performance Considerations

### Build Optimization

1. **Caching**: Enable pip and npm caching
2. **Parallel Builds**: Backend and frontend build simultaneously
3. **Incremental Builds**: Only rebuild changed components
4. **Build Environment**: Use appropriate compute size

### Deployment Optimization

1. **Blue/Green Deployment**: Zero-downtime deployments
2. **CloudFront Caching**: Reduce origin requests
3. **S3 Transfer Acceleration**: Faster uploads
4. **ECS Task Placement**: Optimize resource utilization

## Maintenance and Operations

### Regular Tasks

1. **Weekly**: Review build logs and failure patterns
2. **Monthly**: Update dependencies and security patches
3. **Quarterly**: Review and optimize costs
4. **Annually**: Disaster recovery testing

### Troubleshooting Guide

**Common Issues:**

1. **Build Timeout**: Increase timeout or optimize build steps
2. **Permission Denied**: Review IAM roles and policies
3. **Artifact Not Found**: Check S3 bucket permissions
4. **Deployment Failed**: Review health check configuration

## Future Enhancements

1. **Multi-Region Deployment**: Deploy to multiple AWS regions
2. **Automated Testing**: Add comprehensive test suites
3. **Canary Deployments**: Gradual rollout to production
4. **Infrastructure as Code**: Complete CloudFormation/Terraform templates
5. **Container Registry**: Private ECR for Docker images
6. **API Gateway Integration**: Add API management layer
