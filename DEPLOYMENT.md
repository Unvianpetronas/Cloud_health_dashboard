# 🚀 CI/CD Deployment Guide

Complete guide for deploying Cloud Health Dashboard using AWS CodePipeline and CodeBuild.

## 📋 Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [AWS Infrastructure Setup](#aws-infrastructure-setup)
3. [CI/CD Pipeline Setup](#cicd-pipeline-setup)
4. [Deployment Process](#deployment-process)
5. [Troubleshooting](#troubleshooting)

---

## 🏠 Local Development Setup

### **1. Install Docker & Docker Compose**

```bash
# Check installation
docker --version
docker-compose --version
```

### **2. Create Environment File**

```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

### **3. Start Local Development**

```bash
# Start all services (Frontend, Backend, Nginx)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### **4. Access Application**

- **Application**: http://localhost
- **Backend API**: http://localhost/api/
- **Health Check**: http://localhost/health

---

## ☁️ AWS Infrastructure Setup

### **Step 1: Create ECR Repositories**

```bash
# Create ECR repositories for Docker images
aws ecr create-repository --repository-name cloud-health-frontend --region us-east-1
aws ecr create-repository --repository-name cloud-health-backend --region us-east-1
aws ecr create-repository --repository-name cloud-health-nginx --region us-east-1

# Get ECR URI (save this!)
aws ecr describe-repositories --region us-east-1 --query 'repositories[*].[repositoryName,repositoryUri]' --output table
```

**Example output:**
```
123456789012.dkr.ecr.us-east-1.amazonaws.com/cloud-health-frontend
123456789012.dkr.ecr.us-east-1.amazonaws.com/cloud-health-backend
123456789012.dkr.ecr.us-east-1.amazonaws.com/cloud-health-nginx
```

### **Step 2: Create EC2 Instance**

```bash
# Launch EC2 instance (Amazon Linux 2)
# Instance type: t3.medium or larger
# Security Group: Allow ports 80, 443, 22
```

**IAM Role for EC2:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": "*"
    }
  ]
}
```

### **Step 3: Install CodeDeploy Agent on EC2**

SSH into your EC2 instance:

```bash
#!/bin/bash
sudo yum update -y
sudo yum install ruby wget -y

# Download and install CodeDeploy agent
cd /home/ec2-user
wget https://aws-codedeploy-us-east-1.s3.us-east-1.amazonaws.com/latest/install
chmod +x ./install
sudo ./install auto

# Verify installation
sudo service codedeploy-agent status

# Install Docker
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

### **Step 4: Create CodeBuild Project**

**Go to AWS CodeBuild Console:**

1. Click "Create build project"
2. **Project name**: `cloud-health-dashboard-build`
3. **Source**: GitHub or CodeCommit
4. **Environment**:
   - Image: `aws/codebuild/standard:7.0`
   - Privileged mode: ✅ (Required for Docker)
5. **Buildspec**: Use `buildspec.yml` in repository
6. **Environment variables**:
   ```
   ECR_REGISTRY = 123456789012.dkr.ecr.us-east-1.amazonaws.com
   ECR_FRONTEND_REPO = cloud-health-frontend
   ECR_BACKEND_REPO = cloud-health-backend
   ECR_NGINX_REPO = cloud-health-nginx
   AWS_DEFAULT_REGION = us-east-1
   ```

**IAM Role for CodeBuild:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "*"
    }
  ]
}
```

### **Step 5: Create CodeDeploy Application**

```bash
# Create application
aws deploy create-application \
  --application-name cloud-health-dashboard \
  --compute-platform Server

# Create deployment group
aws deploy create-deployment-group \
  --application-name cloud-health-dashboard \
  --deployment-group-name production \
  --service-role-arn arn:aws:iam::123456789012:role/CodeDeployServiceRole \
  --ec2-tag-filters Key=Name,Value=cloud-health-ec2,Type=KEY_AND_VALUE
```

### **Step 6: Create CodePipeline**

**Go to AWS CodePipeline Console:**

1. Click "Create pipeline"
2. **Pipeline name**: `cloud-health-dashboard-pipeline`

**Source Stage:**
- Provider: GitHub / CodeCommit
- Repository: Your repository
- Branch: `main` or `claude/aws-architecture-analyzer-01XtjGNVcrudk2u4ensT8E1Y`
- Detection: CloudWatch Events (automatic)

**Build Stage:**
- Provider: AWS CodeBuild
- Project: `cloud-health-dashboard-build`

**Deploy Stage:**
- Provider: AWS CodeDeploy
- Application: `cloud-health-dashboard`
- Deployment group: `production`

---

## 🔄 Deployment Process

### **Automatic Deployment (Recommended)**

```bash
# 1. Develop locally
docker-compose up -d

# 2. Test changes
# ... test your changes ...

# 3. Commit and push
git add .
git commit -m "Add new feature"
git push origin main

# 4. Pipeline automatically triggers!
# - CodePipeline detects push
# - CodeBuild builds Docker images
# - Pushes to ECR
# - CodeDeploy deploys to EC2
```

### **Manual Deployment**

```bash
# Trigger pipeline manually from AWS Console
# Or use AWS CLI:
aws codepipeline start-pipeline-execution --name cloud-health-dashboard-pipeline
```

---

## 📊 Monitoring Deployment

### **CodePipeline Console**

```
Source → Build → Deploy
  ✅       ✅       ✅
```

### **CodeBuild Logs**

View build logs in CodeBuild console or CloudWatch.

### **EC2 Deployment Logs**

```bash
# SSH into EC2
ssh ec2-user@your-ec2-ip

# View CodeDeploy logs
tail -f /var/log/aws/codedeploy-agent/codedeploy-agent.log

# View application logs
cd /home/ec2-user/app
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🐛 Troubleshooting

### **Build Fails: Docker Login Error**

**Error**: `Cannot perform an interactive login from a non TTY device`

**Solution**: Ensure CodeBuild has privileged mode enabled.

### **Deployment Fails: Permission Denied**

**Error**: `Permission denied accessing ECR`

**Solution**: 
1. Check EC2 IAM role has ECR access
2. Verify CodeBuild role has ECR push permissions

### **Health Check Fails**

```bash
# Check if containers are running
docker ps

# Check Nginx logs
docker logs <nginx-container-id>

# Test health endpoint
curl http://localhost/health
```

### **Images Not Pulling from ECR**

```bash
# Manually test ECR login on EC2
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Pull image manually
docker pull 123456789012.dkr.ecr.us-east-1.amazonaws.com/cloud-health-frontend:latest
```

---

## 🎯 Quick Commands

```bash
# Local Development
docker-compose up -d              # Start services
docker-compose down               # Stop services
docker-compose logs -f            # View logs
docker-compose ps                 # List running containers

# Production EC2
cd /home/ec2-user/app
docker-compose -f docker-compose.prod.yml up -d    # Start
docker-compose -f docker-compose.prod.yml down     # Stop
docker-compose -f docker-compose.prod.yml logs -f  # Logs

# AWS CLI
aws codepipeline start-pipeline-execution --name cloud-health-dashboard-pipeline
aws codebuild start-build --project-name cloud-health-dashboard-build
aws deploy create-deployment --application-name cloud-health-dashboard --deployment-group-name production
```

---

## ✅ Best Practices

1. **Always test locally first** with `docker-compose up`
2. **Use feature branches** for development
3. **Tag Docker images** with commit hash
4. **Monitor CloudWatch Logs** for errors
5. **Set up CloudWatch Alarms** for production
6. **Enable HTTPS** with Let's Encrypt or ACM
7. **Backup DynamoDB** regularly
8. **Use Parameter Store** for secrets

---

## 🔐 Security Checklist

- ✅ EC2 Security Group allows only 80, 443, 22
- ✅ IAM roles follow least privilege
- ✅ Secrets in AWS Systems Manager Parameter Store
- ✅ ECR images scanned for vulnerabilities
- ✅ Enable encryption at rest
- ✅ Enable VPC Flow Logs
- ✅ Set up AWS WAF for DDoS protection

---

## 📚 Additional Resources

- [AWS CodePipeline Documentation](https://docs.aws.amazon.com/codepipeline/)
- [AWS CodeBuild Documentation](https://docs.aws.amazon.com/codebuild/)
- [AWS CodeDeploy Documentation](https://docs.aws.amazon.com/codedeploy/)
- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

## 🆘 Support

If you encounter issues:
1. Check CloudWatch Logs
2. Review CodeBuild/CodeDeploy logs
3. SSH into EC2 and check container logs
4. Verify IAM permissions

Happy Deploying! 🚀
