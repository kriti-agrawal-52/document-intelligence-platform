# 🚀 Deployment Guide: Document Intelligence Microservices on AWS EKS

This comprehensive guide walks you through deploying a production-ready Document Intelligence platform using **AWS EKS**, **Terraform**, and **Kubernetes**. The application processes documents through AI-powered text extraction and summarization services.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Understanding Terraform Infrastructure](#understanding-terraform-infrastructure)
3. [Secrets Management with AWS Secrets Manager](#secrets-management)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Monitoring & Observability](#monitoring--observability)
6. [Troubleshooting Guide](#troubleshooting-guide)

---

## 🏗️ Architecture Overview

### System Components

- **🔐 Auth Service**: User authentication and JWT token management
- **📄 Text Extraction Service**: AI-powered text extraction from images using OpenAI
- **📝 Text Summarization Service**: Asynchronous text summarization via SQS queues
- **🌐 Application Load Balancer**: External traffic routing
- **🗄️ Databases**: MySQL (user data), DocumentDB (documents), Redis (caching)
- **📬 Message Queue**: SQS for async processing

### Infrastructure Stack

- **☸️ Kubernetes**: Amazon EKS for container orchestration
- **🏢 AWS Services**: RDS, DocumentDB, ElastiCache, SQS, ECR, Secrets Manager
- **🔧 Infrastructure as Code**: Terraform for reproducible deployments
- **🔒 Security**: IAM roles, VPC networking, External Secrets Operator

---

## 🏗️ Understanding Terraform Infrastructure

### 📁 Terraform File Organization

> **Important Note**: The numeric prefixes (01-, 02-, etc.) in Terraform files are **purely for human organization**. Terraform automatically determines the correct execution order based on resource dependencies, not file names. You could rename `01-main.tf` to `zebra.tf` and it would work identically.

| File                       | Purpose                           | Key Resources                                       |
| -------------------------- | --------------------------------- | --------------------------------------------------- |
| **`01-main.tf`**           | Provider configuration & versions | AWS, Kubernetes, Helm providers                     |
| **`02-variables.tf`**      | Input variables & defaults        | Region, VPC CIDR, cluster name                      |
| **`03-vpc.tf`**            | Core networking infrastructure    | VPC, subnets, NAT gateway, ALB tags                 |
| **`04-eks.tf`**            | Kubernetes cluster setup          | EKS cluster, node groups, security                  |
| **`05-databases.tf`**      | Data layer services               | RDS MySQL, DocumentDB, subnet groups                |
| **`06-ecr.tf`**            | Container registry                | ECR repositories for Docker images                  |
| **`07-secrets.tf`**        | Secrets in AWS Secrets Manager    | Database credentials, API keys                      |
| **`08-iam.tf`**            | Identity & Access Management      | Service roles, policies, ALB controller permissions |
| **`09-outputs.tf`**        | Infrastructure outputs            | Endpoints, URLs, cluster info                       |
| **`10-redis.tf`**          | Caching layer                     | ElastiCache Redis cluster                           |
| **`11-sqs.tf`**            | Message queuing                   | SQS queues for async processing                     |
| **`12-eks-auth.tf`**       | Cluster access control            | EKS Access Entries (modern approach)                |
| **`13-alb-controller.tf`** | Load balancer management          | AWS Load Balancer Controller via Helm               |

### 🔄 Terraform Dependency Resolution

Terraform builds a **dependency graph** automatically by analyzing resource references:

```hcl
# Example: Terraform knows this order automatically
resource "aws_vpc" "main" { ... }                    # 1st: Create VPC
resource "aws_subnet" "public" {                     # 2nd: Create subnet
  vpc_id = aws_vpc.main.id                          # (depends on VPC)
}
resource "aws_eks_cluster" "main" {                  # 3rd: Create cluster
  subnet_ids = [aws_subnet.public.id]               # (depends on subnet)
}
```

**Key Insight**: You can add files like `99-new-feature.tf` or `zebra.tf` and Terraform will still execute resources in the correct dependency order.

---

## 🔐 Secrets Management with AWS Secrets Manager

### 🧠 Understanding the Security Architecture

Our deployment implements a **secure, scalable secrets management pattern** using AWS Secrets Manager and External Secrets Operator:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  AWS Secrets    │    │  External        │    │  Kubernetes     │
│  Manager        │◄───┤  Secrets         │───►│  Secrets        │
│                 │    │  Operator        │    │                 │
│  • DB passwords │    │  (ESO Pod)       │    │  • db-creds     │
│  • API keys     │    │                  │    │  • api-keys     │
│  • JWT secrets  │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 🔒 How Secrets Flow Through the System

#### 1. **AWS Secrets Manager (Centralized Storage)**

- **Purpose**: Secure, centralized storage for sensitive data
- **Access Control**: Only specific IAM roles can read secrets
- **Rotation**: Supports automatic credential rotation
- **Encryption**: All secrets encrypted at rest and in transit

```json
// Example secret in AWS Secrets Manager
{
  "username": "mongodatabaseadmin",
  "password": "FJ2rCNv7lo5vFfQ1Y4hzOK"
}
```

#### 2. **External Secrets Operator (The Bridge)**

- **What it is**: A Kubernetes pod that acts as a secure bridge
- **Purpose**: Pulls secrets from AWS and creates Kubernetes Secrets
- **Authentication**: Uses IAM roles (IRSA) - no hardcoded credentials
- **Frequency**: Continuously syncs secrets (handles rotation automatically)

```yaml
# ESO creates this ClusterSecretStore
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: aws-secret-store
spec:
  provider:
    aws:
      service: SecretsManager
      region: ap-south-1
      auth:
        secretRef: # References AWS credentials stored in k8s
```

#### 3. **Kubernetes Secrets (Pod Consumption)**

- **Purpose**: Standard Kubernetes secret objects that pods can consume
- **Scope**: Namespace-scoped for security isolation
- **Consumption**: Mounted as environment variables or files in pods

```yaml
# ESO automatically creates this Kubernetes Secret
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: doc-intel-app
data:
  MONGODB_USER: bW9uZ29kYXRhYmFzZWFkbWlu # base64 encoded
  MONGODB_PASSWORD: RkoyclJOdjdsb... # base64 encoded
```

### 🛡️ Security Benefits

| Traditional Approach                | Our Secrets Manager Approach        |
| ----------------------------------- | ----------------------------------- |
| ❌ Secrets in code/config files     | ✅ Secrets stored securely in AWS   |
| ❌ Manual secret rotation           | ✅ Automatic rotation support       |
| ❌ Same secrets across environments | ✅ Environment-specific secrets     |
| ❌ Difficult audit trail            | ✅ Complete access logging          |
| ❌ Risk of accidental exposure      | ✅ Encrypted at rest and in transit |

### 🔄 External Secrets Operator Workflow

1. **Deployment**: ESO pod starts with IAM role permissions
2. **Discovery**: ESO reads `ExternalSecret` manifests in your cluster
3. **Authentication**: ESO uses IAM role to authenticate with AWS
4. **Retrieval**: ESO fetches secrets from AWS Secrets Manager
5. **Creation**: ESO creates/updates Kubernetes Secret objects
6. **Monitoring**: ESO continuously watches for secret changes
7. **Rotation**: When AWS secrets rotate, ESO updates K8s secrets automatically

### 🎯 Why This Pattern is Production-Ready

- **🔒 Principle of Least Privilege**: Each service only accesses required secrets
- **🔄 Separation of Concerns**: Infrastructure team manages AWS secrets, dev team uses K8s secrets
- **📊 Auditability**: All secret access is logged in AWS CloudTrail
- **🚀 Scalability**: Works across multiple clusters and environments
- **🛡️ Security**: No secrets stored in Git, containers, or config files

---

## 🚀 Step-by-Step Deployment

### 📋 Prerequisites

Before starting, ensure you have:

- [x] **AWS CLI** installed and configured (`aws configure`)
- [x] **Terraform** CLI installed (version >= 1.0)
- [x] **Docker** installed and running
- [x] **kubectl** installed
- [x] **Helm** installed (version >= 3.0)
- [x] **jq** installed for JSON processing
- [x] **AWS credentials** with administrative permissions

### 🎯 Option 1: Automated Deployment (Recommended)

Use our comprehensive deployment script that handles everything:

```bash
# Make the script executable
chmod +x deploy.sh

# Run the complete deployment
./deploy.sh
```

**What the script does:**

1. ✅ Terraform infrastructure provisioning
2. ✅ AWS Load Balancer Controller installation
3. ✅ Docker image building and ECR push
4. ✅ External Secrets Operator setup
5. ✅ Database initialization
6. ✅ Kubernetes deployment
7. ✅ End-to-end application testing

### 🔧 Option 2: Manual Step-by-Step Deployment

#### Step 1: Deploy Infrastructure with Terraform

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Apply the infrastructure (creates ~25 AWS resources)
terraform apply -auto-approve

# Generate outputs for Kubernetes
terraform output -json > tf_outputs.json
```

#### Step 2: Configure kubectl for EKS

```bash
# Get cluster name from Terraform outputs
CLUSTER_NAME=$(jq -r '.eks_cluster_name.value' terraform/tf_outputs.json)
AWS_REGION=$(jq -r '.aws_region.value' terraform/tf_outputs.json || echo "ap-south-1")

# Configure kubectl to access your EKS cluster
aws eks --region $AWS_REGION update-kubeconfig --name $CLUSTER_NAME
```

#### Step 3: Install External Secrets Operator

```bash
# Add the External Secrets Operator Helm repository
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Install ESO in the external-secrets-system namespace
helm install external-secrets external-secrets/external-secrets \
    -n external-secrets-system \
    --create-namespace \
    --wait
```

#### Step 4: Build and Push Docker Images

```bash
# Return to project root
cd ..

# Get ECR URLs from Terraform outputs
AUTH_ECR=$(jq -r '.auth_service_ecr_url.value' terraform/tf_outputs.json)
EXTRACT_ECR=$(jq -r '.text_extraction_service_ecr_url.value' terraform/tf_outputs.json)
SUMMARY_ECR=$(jq -r '.text_summarization_service_ecr_url.value' terraform/tf_outputs.json)

# Authenticate Docker with ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $AUTH_ECR

# Build and push all microservice images
docker build -t auth-service:latest -f auth_service/Dockerfile .
docker tag auth-service:latest $AUTH_ECR:latest
docker push $AUTH_ECR:latest

docker build -t text-extraction-service:latest -f text_extraction_service/Dockerfile .
docker tag text-extraction-service:latest $EXTRACT_ECR:latest
docker push $EXTRACT_ECR:latest

docker build -t text-summarization-service:latest -f text_summarization_service/Dockerfile .
docker tag text-summarization-service:latest $SUMMARY_ECR:latest
docker push $SUMMARY_ECR:latest
```

#### Step 5: Deploy Kubernetes Manifests

```bash
# Process Kubernetes templates with actual values
mkdir -p kubernetes_processed
cp -r kubernetes/* kubernetes_processed/

# Replace placeholders with actual Terraform outputs
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SQS_QUEUE_URL=$(jq -r '.sqs_summarization_queue_url.value' terraform/tf_outputs.json)

# Update deployment manifests
sed -i.bak "s|<aws_account_id>|${AWS_ACCOUNT_ID}|g" kubernetes_processed/*.yaml
sed -i.bak "s|<replace-with-sqs-queue-url-from-terraform-output>|${SQS_QUEUE_URL}|g" kubernetes_processed/*.yaml

# Apply manifests in dependency order
kubectl apply -f kubernetes_processed/00-namespace.yaml
kubectl apply -f kubernetes_processed/01-secrets.yaml
kubectl apply -f kubernetes_processed/02-db-services.yaml

# Wait for secrets to sync
sleep 30

# Deploy applications
kubectl apply -f kubernetes_processed/03-auth-deployment.yaml
kubectl apply -f kubernetes_processed/04-text-extraction-deployment.yaml
kubectl apply -f kubernetes_processed/08-text-summarization-deployment.yaml

# Configure auto-scaling and load balancing
kubectl apply -f kubernetes_processed/06-auth-hpa.yaml
kubectl apply -f kubernetes_processed/07-text-extraction-hpa.yaml
kubectl apply -f kubernetes_processed/09-text-summarization-service-hpa.yaml
kubectl apply -f kubernetes_processed/05-ingress.yaml
```

#### Step 6: Initialize Database

```bash
# Create MySQL database for auth service
kubectl run mysql-client --image=mysql:8.0 --rm -it --restart=Never -n doc-intel-app -- \
  mysql -h mysql-service.doc-intel-app.svc.cluster.local \
  -u $(kubectl get secret db-credentials -n doc-intel-app -o jsonpath='{.data.MYSQL_USER}' | base64 -d) \
  -p$(kubectl get secret db-credentials -n doc-intel-app -o jsonpath='{.data.MYSQL_PASSWORD}' | base64 -d) \
  -e "CREATE DATABASE IF NOT EXISTS auth_db;"
```

### 🎯 Verifying Deployment Success

```bash
# Check all pods are running
kubectl get pods -n doc-intel-app

# Check if ALB is provisioned (may take 2-5 minutes)
kubectl get ingress -n doc-intel-app

# Test the application health endpoints
ALB_URL=$(kubectl get ingress doc-intel-ingress -n doc-intel-app -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$ALB_URL/auth/health
curl http://$ALB_URL/extract/health
```

### 🧪 End-to-End Application Testing

    ```bash

# Register a test user

curl -X POST http://$ALB_URL/auth/register \
 -H "Content-Type: application/json" \
 -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# Login to get JWT token

TOKEN=$(curl -s -X POST http://$ALB_URL/auth/token \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "username=testuser&password=password123" | jq -r '.access_token')

# Upload and process a document

curl -X POST http://$ALB_URL/extract/image_text \
 -H "Authorization: Bearer $TOKEN" \
 -F "image=@test-images/balance_sheet.png" \
 -F "image_name=test_document"

# Check processing status (summary may take 30-60 seconds)

curl -X GET http://$ALB_URL/extract/document/test_document \
 -H "Authorization: Bearer $TOKEN"

````

---

## 📊 Monitoring & Observability

### 🎯 Key Metrics to Monitor

#### Application Metrics

- **Auth Service**: Login success rate, token generation latency
- **Text Extraction**: OpenAI API response times, document processing rate
- **Text Summarization**: Queue processing rate, job success/failure ratio

#### Infrastructure Metrics

- **EKS Cluster**: Node utilization, pod restart frequency
- **Databases**: Connection counts, query performance, storage usage
- **SQS Queue**: Message count, processing latency, dead letter queue depth
- **ALB**: Request count, latency, error rates

#### Critical Alerts to Set Up

```yaml
# Example CloudWatch Alarms
High_SQS_Queue_Depth:
  threshold: 100 messages
  action: Scale up text-summarization pods

Dead_Letter_Queue_Messages:
  threshold: > 0 messages
  action: Immediate investigation required

Pod_Restart_Rate:
  threshold: > 5 restarts in 10 minutes
  action: Check application logs

Database_Connection_Errors:
  threshold: > 10 errors in 5 minutes
  action: Check database availability
````

### 📈 Recommended Monitoring Stack

1. **AWS CloudWatch**: Infrastructure and service metrics
2. **Prometheus + Grafana**: Application metrics and custom dashboards
3. **AWS X-Ray**: Distributed tracing across microservices
4. **ELK Stack**: Centralized logging and log analysis

---

## 🚨 Troubleshooting Guide

### Common Issues and Solutions

#### 1. **Pods in CrashLoopBackOff**

```bash
# Check pod logs
kubectl logs <pod-name> -n doc-intel-app

# Check pod events
kubectl describe pod <pod-name> -n doc-intel-app

# Common causes:
# - Missing environment variables
# - Database connection failures
# - Image pull errors
```

#### 2. **ALB Not Getting External IP**

```bash
# Check ALB controller status
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Check ingress events
kubectl describe ingress doc-intel-ingress -n doc-intel-app

# Common causes:
# - Missing subnet tags
# - IAM permission issues
# - Security group configuration
```

#### 3. **External Secrets Not Syncing**

    ```bash

# Check ESO pod logs

kubectl logs -n external-secrets-system -l app.kubernetes.io/name=external-secrets

# Check External Secret status

kubectl describe externalsecret -n doc-intel-app

# Common causes:

# - IAM permission issues

# - Secret not found in AWS Secrets Manager

# - Incorrect ClusterSecretStore configuration

````

#### 4. **Database Connection Issues**

    ```bash
# Test database connectivity from a pod
kubectl run test-db --image=mysql:8.0 --rm -it --restart=Never -n doc-intel-app -- \
  mysql -h mysql-service.doc-intel-app.svc.cluster.local -u <username> -p

# Check service endpoints
kubectl get endpoints -n doc-intel-app

# Common causes:
# - Security group rules
# - Incorrect service configuration
# - Database not ready
````

### 🆘 Emergency Procedures

#### Complete Environment Reset

```bash
# Delete Kubernetes resources
kubectl delete namespace doc-intel-app

# Destroy Terraform infrastructure
cd terraform
terraform destroy -auto-approve

# Clean up local Docker images
docker system prune -a
```

#### Rollback Deployment

```bash
# Rollback specific deployment
kubectl rollout undo deployment/<deployment-name> -n doc-intel-app

# Check rollout status
kubectl rollout status deployment/<deployment-name> -n doc-intel-app
```

---

## 🎯 Conclusion

You now have a **production-ready, enterprise-grade Document Intelligence platform** deployed on AWS EKS with:

✅ **Secure secrets management** via AWS Secrets Manager and External Secrets Operator  
✅ **Scalable infrastructure** with auto-scaling based on demand  
✅ **High availability** across multiple availability zones  
✅ **Complete observability** with comprehensive monitoring  
✅ **Infrastructure as Code** with Terraform for reproducible deployments  
✅ **Asynchronous processing** with SQS for reliable document processing

The platform can handle document processing at scale while maintaining security, reliability, and cost-effectiveness. The infrastructure is fully codified and can be replicated across multiple environments (dev, staging, production) with minimal configuration changes.

### 📚 Next Steps

1. **Set up monitoring dashboards** in CloudWatch and Grafana
2. **Configure backup strategies** for databases and persistent volumes
3. **Implement CI/CD pipelines** for automated deployments
4. **Set up multi-environment** deployments (dev, staging, prod)
5. **Configure disaster recovery** procedures and testing

For questions or issues, refer to the troubleshooting section above or consult the AWS EKS and Kubernetes documentation.
