# Frontend GitHub Actions Setup Guide

This guide explains how to set up automated CI/CD for your Next.js frontend using GitHub Actions and AWS App Runner.

## 🏗️ Architecture Overview

```
GitHub Repository → GitHub Actions → AWS ECR → AWS App Runner → Live Application
     ↓                    ↓            ↓           ↓              ↓
   Code Push          Build & Test   Docker Image  Auto Deploy   HTTPS URL
```

## 📋 Prerequisites

### 1. AWS Infrastructure
Make sure you've deployed the Terraform infrastructure:

```bash
cd terraform
terraform plan
terraform apply
```

This creates:
- ECR repository for Docker images
- App Runner service
- IAM roles and permissions
- VPC connector for backend access

### 2. AWS Credentials
You'll need AWS credentials with permissions to:
- Push images to ECR
- Describe App Runner services
- Access CloudWatch logs

## 🔐 GitHub Secrets Setup

Add these secrets to your GitHub repository:

### Required Secrets
Go to: `GitHub Repository → Settings → Secrets and variables → Actions`

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AWS_ACCESS_KEY_ID` | AWS access key for deployment | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for deployment | `wJalrXUtn...` |
| `AWS_ACCOUNT_ID` | Your AWS account ID | `123456789012` |

### How to Get AWS Credentials

#### Option 1: Create IAM User (Recommended for Testing)
```bash
# Create IAM user for GitHub Actions
aws iam create-user --user-name github-actions-frontend

# Create access key
aws iam create-access-key --user-name github-actions-frontend

# Attach necessary policies
aws iam attach-user-policy --user-name github-actions-frontend \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam attach-user-policy --user-name github-actions-frontend \
  --policy-arn arn:aws:iam::aws:policy/AWSAppRunnerReadOnlyAccess
```

#### Option 2: Use OIDC (Recommended for Production)
For production, use GitHub OIDC instead of long-lived credentials:

```hcl
# Add to your Terraform configuration
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions" {
  name = "github-actions-frontend"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = "repo:YOUR_USERNAME/YOUR_REPO:ref:refs/heads/main"
          }
        }
      }
    ]
  })
}
```

## 🚀 Workflows Overview

### 1. Frontend CI (`frontend-ci.yml`)
**Triggers:** Pull requests, feature branch pushes
**Purpose:** Code quality checks and build verification

**Steps:**
- ✅ Lint code
- ✅ Type checking
- ✅ Build application
- ✅ Run tests
- ✅ Bundle size analysis

### 2. Frontend Deployment (`deploy-frontend.yml`)
**Triggers:** Push to main branch, manual dispatch
**Purpose:** Build and deploy to AWS App Runner

**Steps:**
- 🔨 Build Next.js application
- 🐳 Build Docker image
- 📤 Push to ECR
- 🚀 Deploy to App Runner
- 🏥 Health check
- 📊 Deployment summary

## 📝 Configuration Files

### Environment Variables in Workflows

The workflows are configured with these defaults:
```yaml
env:
  AWS_REGION: ap-south-1
  ECR_REPOSITORY: doc-intel-frontend
  NODE_VERSION: '18'
  PNPM_VERSION: '8'
```

### Docker Build Configuration

The Docker image is built with:
- Multi-stage build for optimization
- Production environment variables
- Health check endpoint
- Non-root user for security

## 🎯 Deployment Process

### Automatic Deployment
1. Push code to `main` branch
2. GitHub Actions triggers automatically
3. Builds and tests the application
4. Creates Docker image
5. Pushes to ECR
6. App Runner automatically deploys new image
7. Health check verifies deployment
8. Deployment summary posted

### Manual Deployment
1. Go to GitHub Actions tab
2. Select "Deploy Frontend to AWS App Runner"
3. Click "Run workflow"
4. Choose environment and tag (optional)
5. Click "Run workflow" button

## 📊 Monitoring and Debugging

### Check Deployment Status
```bash
# Get App Runner service status
aws apprunner describe-service --service-arn <SERVICE_ARN>

# View recent deployments
aws apprunner list-operations --service-arn <SERVICE_ARN>
```

### View Application Logs
```bash
# CloudWatch logs
aws logs tail /aws/apprunner/doc-intel-frontend --follow

# Or in AWS Console
# CloudWatch → Log groups → /aws/apprunner/doc-intel-frontend
```

### Health Check
Your application will be available at:
- **App URL:** `https://your-app-id.ap-south-1.awsapprunner.com`
- **Health Check:** `https://your-app-id.ap-south-1.awsapprunner.com/api/health`

## 🔧 Troubleshooting

### Common Issues

#### 1. ECR Authentication Failed
```bash
# Check ECR repository exists
aws ecr describe-repositories --repository-names doc-intel-frontend

# Test ECR login
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <ECR_URI>
```

#### 2. App Runner Service Not Found
```bash
# List all App Runner services
aws apprunner list-services

# Check service name matches workflow
aws apprunner describe-service --service-arn <ARN>
```

#### 3. Deployment Timeout
- Check CloudWatch logs for errors
- Verify health check endpoint responds
- Ensure environment variables are correct
- Check VPC connectivity to backend services

#### 4. Build Failures
- Check Node.js version compatibility
- Verify all dependencies are in package.json
- Check for TypeScript errors
- Ensure environment variables are set

### Debug Commands

```bash
# Test local Docker build
cd frontend
docker build -t test-frontend .
docker run -p 3000:3000 test-frontend

# Check GitHub Actions logs
# Go to: Repository → Actions → Select workflow run → View logs

# Test health endpoint locally
curl http://localhost:3000/api/health
```

## 🚦 Workflow Status Badges

Add these to your README.md:

```markdown
[![Frontend CI](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Frontend%20CI/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions)
[![Deploy Frontend](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Deploy%20Frontend%20to%20AWS%20App%20Runner/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions)
```

## 🔄 Rollback Process

If a deployment fails:

### Option 1: Rollback via GitHub
1. Go to previous successful commit
2. Manually trigger deployment workflow
3. Wait for deployment to complete

### Option 2: Rollback via AWS Console
1. AWS Console → App Runner → Services
2. Select your service
3. Go to "Deployments" tab
4. Select previous successful deployment
5. Click "Deploy"

### Option 3: Rollback via CLI
```bash
# Get previous image tag
aws ecr list-images --repository-name doc-intel-frontend \
  --query 'imageIds[*].imageTag' --output table

# Retag and push previous image as latest
docker tag <ECR_URI>:<OLD_TAG> <ECR_URI>:latest
docker push <ECR_URI>:latest
```

## 💰 Cost Optimization

### Estimated Costs
- **App Runner:** ~$25-50/month (1-2 instances)
- **ECR Storage:** ~$0.10/GB/month
- **Data Transfer:** ~$0.09/GB outbound
- **CloudWatch Logs:** ~$0.50/GB ingested

### Cost-Saving Tips
1. Use lifecycle policies for ECR images
2. Monitor and adjust App Runner scaling
3. Use GitHub Actions efficiently (avoid unnecessary runs)
4. Clean up old Docker images regularly

## 🔒 Security Best Practices

1. **Use least-privilege IAM policies**
2. **Enable ECR image scanning**
3. **Use OIDC instead of long-lived keys**
4. **Regularly rotate credentials**
5. **Monitor access logs**
6. **Use private repositories**
7. **Scan Docker images for vulnerabilities**

## 📚 Additional Resources

- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Next.js Deployment Guide](https://nextjs.org/docs/deployment)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 🆘 Support

If you encounter issues:

1. Check GitHub Actions logs
2. Review AWS CloudWatch logs
3. Verify Terraform infrastructure
4. Test local Docker build
5. Check AWS service limits
6. Review IAM permissions

For additional help, check the AWS support documentation or create an issue in the repository.
