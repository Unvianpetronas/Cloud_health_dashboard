# Implementation Plan

- [ ] 1. Prepare backend requirements.txt file
  - Create comprehensive requirements.txt in backend directory with all dependencies
  - Include FastAPI, uvicorn, pydantic-settings, boto3, python-dotenv, and other dependencies
  - Pin versions for reproducible builds
  - _Requirements: 2.1_

- [ ] 2. Create buildspec files for CodeBuild projects
- [ ] 2.1 Create backend buildspec.yml
  - Create buildspec.yml in backend directory with Python 3.11 configuration
  - Add install phase for pip dependencies
  - Add pre_build phase for linting and syntax checks
  - Add build phase for running tests
  - Configure artifacts output
  - Add caching for pip packages
  - _Requirements: 9.1, 9.3, 9.5_

- [ ] 2.2 Create frontend buildspec.yml
  - Create buildspec.yml in frontend directory with Node.js 18 configuration
  - Add install phase for npm dependencies
  - Add pre_build phase for syntax checks
  - Add build phase for React production build
  - Configure artifacts output from build directory
  - Add caching for node_modules
  - _Requirements: 9.2, 9.4, 9.5_

- [ ] 3. Set up AWS CodeCommit repository in ap-southeast-1
  - Create CodeCommit repository named "cloud-health-dashboard" in Singapore region
  - Configure Git credentials for HTTPS access
  - Add CodeCommit as remote to local repository
  - Push existing code and branches to CodeCommit
  - Verify all files are pushed correctly
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 4. Create IAM roles and policies for CI/CD
- [ ] 4.1 Create CodePipeline service role
  - Create IAM role with trust policy for CodePipeline service
  - Attach policy for CodeCommit access
  - Attach policy for CodeBuild access
  - Attach policy for S3 artifacts access
  - Attach policy for ECS/Elastic Beanstalk deployment
  - _Requirements: 7.1, 7.3_

- [ ] 4.2 Create CodeBuild service roles
  - Create IAM role for backend CodeBuild project
  - Create IAM role for frontend CodeBuild project
  - Attach policies for CloudWatch Logs
  - Attach policies for S3 artifacts access
  - Attach policies for CodeCommit access
  - Attach policies for ECR (if using Docker)
  - _Requirements: 7.2, 7.3_

- [ ] 4.3 Create deployment service role
  - Create IAM role for ECS task execution or Elastic Beanstalk
  - Attach policies for DynamoDB access
  - Attach policies for SES access
  - Attach policies for EC2, GuardDuty, CloudWatch, Cost Explorer access
  - Attach policies for Secrets Manager and Parameter Store access
  - _Requirements: 7.4, 7.5_

- [ ] 5. Create S3 bucket for pipeline artifacts in ap-southeast-1
  - Create S3 bucket for CodePipeline artifacts storage in Singapore region
  - Enable versioning on the bucket
  - Configure bucket policy for CodePipeline and CodeBuild access
  - Set up lifecycle policies for artifact retention (30 days)
  - Enable encryption at rest
  - _Requirements: 4.3_

- [ ] 6. Set up backend CodeBuild project
  - Create CodeBuild project named "cloud-health-backend-build" in ap-southeast-1
  - Configure Python 3.11 runtime with aws/codebuild/standard:7.0 image
  - Set compute type to BUILD_GENERAL1_SMALL
  - Link buildspec.yml from backend/buildspec.yml
  - Configure artifact output to S3
  - Set up CloudWatch Logs group for build logging
  - Configure environment variables for build
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 7. Set up frontend CodeBuild project
  - Create CodeBuild project named "cloud-health-frontend-build" in ap-southeast-1
  - Configure Node.js 18 runtime with aws/codebuild/standard:7.0 image
  - Set compute type to BUILD_GENERAL1_SMALL
  - Link buildspec.yml from frontend/buildspec.yml
  - Configure artifact output to S3
  - Set up CloudWatch Logs group for build logging
  - Add environment variable for REACT_APP_API_BASE_URL
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 8. Store secrets in AWS Secrets Manager
  - Create secret for JWT_SECRET_KEY in ap-southeast-1
  - Create secret for ENCRYPTION_KEY
  - Create secret for YOUR_AWS_ACCESS_KEY_ID
  - Create secret for YOUR_AWS_SECRET_ACCESS_KEY
  - Tag secrets appropriately for environment
  - _Requirements: 5.3, 7.4_

- [ ] 9. Store configuration in AWS Systems Manager Parameter Store
  - Create parameter for ENVIRONMENT (production)
  - Create parameter for DEBUG (false)
  - Create parameter for LOG_LEVEL (INFO)
  - Create parameter for AWS_REGION (ap-southeast-1)
  - Create parameter for SES_SENDER_EMAIL
  - Create parameter for FRONTEND_URL (https://cloudhealths.id.vn)
  - Create parameter for CORS_ORIGINS
  - Create parameter for METRICS_COLLECTION_INTERVAL
  - _Requirements: 5.3, 7.4_

- [ ] 10. Set up backend deployment infrastructure (ECS Fargate)
- [ ] 10.1 Create Dockerfile for backend
  - Create Dockerfile in backend directory
  - Use python:3.11-slim as base image
  - Copy application code and install dependencies
  - Expose port 8000
  - Set CMD to run uvicorn server
  - _Requirements: 5.1_

- [ ] 10.2 Create ECR repository
  - Create ECR repository named "cloud-health-backend" in ap-southeast-1
  - Configure lifecycle policy to keep last 10 images
  - Enable scan on push for security
  - _Requirements: 5.1_

- [ ] 10.3 Create ECS cluster and task definition
  - Create ECS cluster named "cloud-health-cluster" in ap-southeast-1
  - Create task definition for backend with Fargate launch type
  - Configure task with 512 CPU and 1024 memory
  - Add container definition pointing to ECR image
  - Configure environment variables from Secrets Manager and Parameter Store
  - Set up CloudWatch Logs for container logs
  - _Requirements: 5.1, 5.2, 5.3_

- [ ] 10.4 Create ECS service with load balancer
  - Create Application Load Balancer in public subnets
  - Create target group for backend service on port 8000
  - Configure health check path to /health
  - Create ECS service with 2 desired tasks
  - Configure service to use load balancer
  - Enable auto-scaling based on CPU utilization
  - _Requirements: 5.1, 5.4, 5.5_

- [ ] 10.5 Update backend buildspec for Docker
  - Add Docker build commands to buildspec.yml
  - Add Docker push to ECR commands
  - Create imagedefinitions.json for ECS deployment
  - Configure CodeBuild project with Docker privileged mode
  - _Requirements: 2.3, 5.1_

- [ ] 11. Set up frontend deployment infrastructure (S3 + CloudFront)
- [ ] 11.1 Create S3 bucket for frontend hosting
  - Create S3 bucket named "cloud-health-dashboard-frontend" in ap-southeast-1
  - Configure bucket for static website hosting
  - Set index document to index.html
  - Set error document to index.html (for React Router)
  - Enable versioning for rollback capability
  - _Requirements: 6.1, 6.4_

- [ ] 11.2 Configure S3 bucket policy and CORS
  - Create bucket policy to allow CloudFront access
  - Configure CORS rules for API communication
  - Set appropriate cache-control headers
  - Block public access (CloudFront will serve content)
  - _Requirements: 6.4, 6.5_

- [ ] 11.3 Create CloudFront distribution
  - Create CloudFront distribution with S3 origin
  - Configure Origin Access Identity for S3 access
  - Set default root object to index.html
  - Configure custom error responses (404 → 200 → /index.html)
  - Enable compression
  - Set viewer protocol policy to redirect-to-https
  - Configure caching behavior with appropriate TTLs
  - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [ ] 11.4 Configure custom domain with Route 53
  - Create or update Route 53 hosted zone for cloudhealths.id.vn
  - Request ACM certificate for cloudhealths.id.vn in us-east-1 (for CloudFront)
  - Validate certificate via DNS
  - Add custom domain to CloudFront distribution
  - Create Route 53 alias record pointing to CloudFront
  - _Requirements: 6.5_

- [ ] 12. Create AWS CodePipeline
- [ ] 12.1 Create pipeline structure
  - Create pipeline named "cloud-health-dashboard-pipeline" in ap-southeast-1
  - Configure artifact store to use S3 bucket
  - Assign CodePipeline service role
  - _Requirements: 4.1, 4.2_

- [ ] 12.2 Add source stage
  - Add source action for CodeCommit
  - Configure repository name "cloud-health-dashboard"
  - Set branch name to "main"
  - Configure CloudWatch Events trigger (not polling)
  - Set output artifact name to "SourceOutput"
  - _Requirements: 4.1, 4.3_

- [ ] 12.3 Add backend build stage
  - Add build action using backend CodeBuild project
  - Set input artifact to "SourceOutput"
  - Set output artifact to "BackendBuildOutput"
  - Configure to run in parallel with frontend build
  - _Requirements: 4.2, 4.4_

- [ ] 12.4 Add frontend build stage
  - Add build action using frontend CodeBuild project
  - Set input artifact to "SourceOutput"
  - Set output artifact to "FrontendBuildOutput"
  - Configure to run in parallel with backend build
  - _Requirements: 4.2, 4.4_

- [ ] 12.5 Add backend deployment stage
  - Add deploy action for ECS
  - Configure cluster name "cloud-health-cluster"
  - Configure service name "backend-service"
  - Set input artifact to "BackendBuildOutput"
  - Configure to use imagedefinitions.json
  - _Requirements: 4.4, 5.1_

- [ ] 12.6 Add frontend deployment stage
  - Add deploy action for S3
  - Configure bucket name "cloud-health-dashboard-frontend"
  - Set extract to true
  - Set input artifact to "FrontendBuildOutput"
  - _Requirements: 4.4, 6.1_

- [ ] 12.7 Add CloudFront invalidation step
  - Add custom action or Lambda function to invalidate CloudFront cache
  - Configure to run after S3 deployment
  - Invalidate /* path
  - _Requirements: 6.2_

- [ ] 13. Set up monitoring and notifications
- [ ] 13.1 Create SNS topic for notifications
  - Create SNS topic named "cloud-health-pipeline-notifications" in ap-southeast-1
  - Subscribe email addresses for DevOps team
  - Configure topic policy for CloudWatch Events
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 13.2 Create CloudWatch Events rules
  - Create rule for pipeline execution state changes
  - Create rule for pipeline stage state changes
  - Configure rules to publish to SNS topic
  - Add filters for FAILED and SUCCEEDED states
  - _Requirements: 8.1, 8.2, 8.4, 8.5_

- [ ] 13.3 Create CloudWatch alarms
  - Create alarm for pipeline execution failures
  - Create alarm for build duration exceeding threshold
  - Create alarm for deployment failures
  - Configure alarms to publish to SNS topic
  - _Requirements: 8.1, 8.2, 8.3_

- [ ] 13.4 Set up application monitoring
  - Create CloudWatch dashboard for application metrics
  - Add ECS service metrics (CPU, memory, task count)
  - Add ALB metrics (request count, latency, errors)
  - Add CloudFront metrics (requests, error rate)
  - Create alarms for application health
  - _Requirements: 5.4_

- [ ] 14. Create infrastructure-as-code templates
- [ ] 14.1 Create CloudFormation template for networking
  - Create VPC with public and private subnets in 2 AZs
  - Create Internet Gateway and NAT Gateways
  - Create route tables for public and private subnets
  - Create security groups for ALB and ECS tasks
  - Export VPC and subnet IDs for other stacks
  - _Requirements: 10.1, 10.2_

- [ ] 14.2 Create CloudFormation template for CI/CD resources
  - Create template for CodeCommit repository
  - Create template for CodeBuild projects
  - Create template for CodePipeline
  - Create template for IAM roles and policies
  - Create template for S3 artifacts bucket
  - Add parameters for customization
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 14.3 Create CloudFormation template for backend infrastructure
  - Create template for ECR repository
  - Create template for ECS cluster
  - Create template for ECS task definition
  - Create template for ECS service
  - Create template for Application Load Balancer
  - Create template for auto-scaling policies
  - _Requirements: 10.1, 10.2, 10.4_

- [ ] 14.4 Create CloudFormation template for frontend infrastructure
  - Create template for S3 bucket
  - Create template for CloudFront distribution
  - Create template for Route 53 records
  - Create template for ACM certificate
  - _Requirements: 10.1, 10.2, 10.4_

- [ ] 14.5 Create master CloudFormation template
  - Create nested stack template that orchestrates all stacks
  - Add parameters for environment, region, domain
  - Add outputs with important resource identifiers
  - Document deployment order and dependencies
  - _Requirements: 10.2, 10.5_

- [ ] 15. Test the complete CI/CD pipeline
- [ ] 15.1 Test backend build and deployment
  - Make a test commit to backend code
  - Verify pipeline triggers automatically
  - Verify backend build completes successfully
  - Verify Docker image is pushed to ECR
  - Verify ECS service updates with new task definition
  - Verify health check passes
  - Test backend API endpoints
  - _Requirements: 4.1, 4.5, 5.4_

- [ ] 15.2 Test frontend build and deployment
  - Make a test commit to frontend code
  - Verify pipeline triggers automatically
  - Verify frontend build completes successfully
  - Verify files are uploaded to S3
  - Verify CloudFront cache is invalidated
  - Test frontend application loads correctly
  - Verify API calls work from frontend
  - _Requirements: 4.1, 4.5, 6.1, 6.2_

- [ ] 15.3 Test rollback procedures
  - Trigger a failed deployment
  - Verify ECS maintains previous task definition
  - Test manual rollback to previous version
  - Verify S3 versioning allows frontend rollback
  - Document rollback steps
  - _Requirements: 5.5_

- [ ] 15.4 Test notifications
  - Verify email notifications for successful deployments
  - Verify email notifications for failed deployments
  - Verify CloudWatch alarms trigger correctly
  - Test SNS topic subscriptions
  - _Requirements: 8.1, 8.2, 8.5_

- [ ] 16. Document the CI/CD setup and usage
- [ ] 16.1 Create deployment documentation
  - Document complete architecture with diagrams
  - Document all AWS resources created
  - Document environment variables and secrets
  - Document IAM roles and permissions
  - Create troubleshooting guide
  - _Requirements: 7.4, 10.5_

- [ ] 16.2 Create operational runbook
  - Document how to trigger manual pipeline executions
  - Document how to view build logs
  - Document how to access ECS task logs
  - Document how to update environment variables
  - Document how to perform rollbacks
  - Document how to scale ECS service
  - Document how to invalidate CloudFront cache manually
  - _Requirements: 10.5_

- [ ] 16.3 Create developer guide
  - Document Git workflow and branching strategy
  - Document how to test locally before pushing
  - Document how to add new environment variables
  - Document how to update dependencies
  - Document how to add new API routes
  - _Requirements: 10.5_
