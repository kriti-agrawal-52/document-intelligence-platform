# 🌐 Frontend Deployment Guide: S3 + CloudFront + CDN

This guide provides a complete setup for deploying your Document Intelligence frontend to AWS using S3 for storage and CloudFront for global CDN distribution with edge caching.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Developer     │    │     AWS S3       │    │   CloudFront    │
│                 │    │                  │    │      CDN        │
│  Next.js Build  │───►│  Static Assets   │◄───┤   Edge Cache    │
│                 │    │  (HTML/JS/CSS)   │    │   Worldwide     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │     Users       │
                                               │   Worldwide     │
                                               │  Fast Access    │
                                               └─────────────────┘
```

### 🚀 **Performance Benefits:**

- **⚡ Edge Caching**: Login/signup pages cached at 300+ global locations
- **🏎️ Static Assets**: 1-year cache for JS/CSS (immutable files)
- **📱 HTML Pages**: 1-hour cache with instant invalidation
- **🔄 Auto-refresh**: CloudFront invalidation on new deployments
- **📊 Compression**: Automatic gzip/brotli compression
- **🔒 HTTPS**: Automatic SSL/TLS with HTTP to HTTPS redirect

---

## 📁 What's Been Created

### **Terraform Infrastructure** (`terraform/14-frontend-infrastructure.tf`)

- ✅ **S3 Bucket** - Secure static asset storage
- ✅ **CloudFront Distribution** - Global CDN with optimized caching
- ✅ **Origin Access Control** - Secure S3 access (no public bucket)
- ✅ **IAM Roles & Policies** - Deployment permissions
- ✅ **Cache Behaviors** - Optimized for different file types
- ✅ **Error Handling** - SPA routing support (404 → index.html)

### **Deployment Scripts** (`scripts/`)

- ✅ **`deploy-frontend.py`** - Complete boto3 deployment automation
- ✅ **`setup-frontend-deployment.sh`** - One-time setup script
- ✅ **`requirements.txt`** - Python dependencies for deployment

### **Frontend Configuration** (`frontend/`)

- ✅ **`next.config.mjs`** - Optimized for static export
- ✅ **`.env.production`** - Production environment variables
- ✅ **Build optimization** - Code splitting and caching headers

---

## 🚀 Quick Start Guide

### **Step 1: One-Time Setup**

```bash
# Navigate to scripts directory
cd scripts

# Run the setup script (interactive)
chmod +x setup-frontend-deployment.sh
./setup-frontend-deployment.sh
```

This script will:

- ✅ Check prerequisites (AWS CLI, Terraform, Node.js, Python)
- ✅ Deploy S3 bucket and CloudFront distribution via Terraform
- ✅ Configure frontend build settings
- ✅ Install deployment dependencies
- ✅ Test build process

### **Step 2: Deploy Frontend**

```bash
# Deploy with all defaults
./deploy-frontend.sh

# Deploy to staging environment
./deploy-frontend.sh --environment staging

# Deploy without rebuilding (if you already built)
./deploy-frontend.sh --skip-build
```

### **Step 3: Access Your Application**

```bash
# Your frontend URL will be displayed after deployment
# Example: https://d1234567890123.cloudfront.net
```

---

## ⚙️ Configuration Details

### **Environment Variables**

The deployment automatically configures:

```bash
# Production (.env.production)
NEXT_PUBLIC_API_BASE_URL=https://your-alb-url.amazonaws.com
NODE_ENV=production
NEXT_PUBLIC_ENVIRONMENT=production
```

### **Cache Strategy**

Optimized caching for maximum performance:

| File Type                             | Cache Duration | Invalidation      |
| ------------------------------------- | -------------- | ----------------- |
| **Static Assets** (`/_next/static/*`) | 1 year         | Never (immutable) |
| **HTML Files**                        | 1 hour         | On each deploy    |
| **API Calls** (`/api/*`)              | No cache       | Real-time         |
| **Other Assets**                      | 1 day          | On deploy         |

### **Security Headers**

Automatically applied:

- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- Automatic HTTPS redirect

---

## 🔧 Manual Deployment Steps

If you prefer manual control:

### **1. Deploy Infrastructure**

```bash
cd terraform

# Deploy frontend infrastructure specifically
terraform apply -target=aws_s3_bucket.frontend_bucket \
                -target=aws_cloudfront_distribution.frontend_distribution

# Get outputs
terraform output -json > tf_outputs.json
```

### **2. Build Frontend**

```bash
cd frontend

# Create production environment
echo "NEXT_PUBLIC_API_BASE_URL=https://your-alb-url" > .env.production

# Install and build
npm install
npm run build
```

### **3. Upload to S3**

```bash
# Using AWS CLI
aws s3 sync out/ s3://your-bucket-name/ --delete

# Or using the Python script
cd ../scripts
python3 deploy-frontend.py --skip-build
```

### **4. Invalidate CloudFront**

```bash
# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

---

## 📊 Monitoring & Analytics

### **CloudWatch Metrics**

Monitor your frontend performance:

```bash
# View CloudFront metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name Requests \
  --dimensions Name=DistributionId,Value=YOUR_DISTRIBUTION_ID \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### **Key Metrics to Watch**

- **Requests/minute** - Traffic volume
- **Cache Hit Ratio** - CDN efficiency (target: >90%)
- **Origin Latency** - S3 response time
- **Error Rate** - 4xx/5xx errors
- **Data Transfer** - Bandwidth usage

### **Cost Optimization**

- **CloudFront**: ~$0.01 per GB (first 1TB free tier)
- **S3 Storage**: ~$0.023 per GB
- **Data Transfer**: Free from S3 to CloudFront
- **Requests**: $0.0075 per 10,000 requests

---

## 🔄 CI/CD Integration

### **GitHub Actions Example**

```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths: ["frontend/**"]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-south-1

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.9"

      - name: Deploy Frontend
        run: |
          cd scripts
          pip install -r requirements.txt
          python3 deploy-frontend.py --environment production
```

### **Manual Deploy Script for CI**

```bash
#!/bin/bash
# deploy-ci.sh - For automated deployments

set -e

export AWS_DEFAULT_REGION=ap-south-1
export NODE_ENV=production

cd scripts
python3 deploy-frontend.py \
  --environment production \
  --region ap-south-1

echo "✅ Frontend deployed successfully!"
```

---

## 🐛 Troubleshooting

### **Common Issues**

#### **1. CloudFront Not Updating**

```bash
# Issue: Changes not visible after deployment
# Solution: Wait for invalidation or force clear

# Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id YOUR_DIST_ID \
  --id YOUR_INVALIDATION_ID

# Create new invalidation
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

#### **2. API Calls Failing**

```bash
# Issue: CORS errors or API not accessible
# Check: Frontend API URL configuration

# Verify environment variables
cat frontend/.env.production

# Should match your ALB URL
NEXT_PUBLIC_API_BASE_URL=https://your-alb-url.amazonaws.com
```

#### **3. Build Failures**

```bash
# Issue: Next.js build fails
# Check: Dependencies and configuration

cd frontend
npm install --force
npm run build

# Common fixes:
# - Update Node.js version
# - Clear npm cache: npm cache clean --force
# - Delete node_modules and reinstall
```

#### **4. S3 Access Denied**

```bash
# Issue: Deployment script can't upload to S3
# Check: AWS credentials and IAM permissions

# Verify credentials
aws sts get-caller-identity

# Check bucket permissions
aws s3api get-bucket-policy --bucket your-bucket-name
```

### **Debugging Commands**

```bash
# Check CloudFront distribution status
aws cloudfront get-distribution --id YOUR_DIST_ID

# List S3 bucket contents
aws s3 ls s3://your-bucket-name/ --recursive

# Test frontend URL
curl -I https://your-cloudfront-url.amazonaws.com

# Check Terraform state
cd terraform
terraform show | grep frontend
```

---

## 📈 Performance Optimization

### **Next.js Optimizations**

- ✅ **Static Export**: Pre-rendered HTML for fast loading
- ✅ **Code Splitting**: Separate bundles for vendors and app code
- ✅ **Image Optimization**: Disabled for static export (handled by CloudFront)
- ✅ **Bundle Analysis**: Optimized chunk sizes

### **CloudFront Optimizations**

- ✅ **Compression**: Automatic gzip/brotli
- ✅ **HTTP/2**: Enabled by default
- ✅ **Multiple Origins**: S3 for static, ALB for API
- ✅ **Geographic Distribution**: 300+ edge locations

### **S3 Optimizations**

- ✅ **Transfer Acceleration**: Optional for faster uploads
- ✅ **Intelligent Tiering**: Automatic cost optimization
- ✅ **Lifecycle Policies**: Automatic cleanup of old builds

---

## 🔒 Security Best Practices

### **Implemented Security**

- ✅ **No Public S3 Bucket**: CloudFront-only access
- ✅ **HTTPS Only**: Automatic redirect
- ✅ **Security Headers**: XSS, clickjacking protection
- ✅ **Origin Access Control**: Modern secure S3 access
- ✅ **IAM Least Privilege**: Minimal required permissions

### **Additional Security (Optional)**

```bash
# Add custom domain with SSL certificate
aws acm request-certificate \
  --domain-name your-domain.com \
  --validation-method DNS

# Configure WAF for DDoS protection
aws wafv2 create-web-acl \
  --name frontend-protection \
  --scope CLOUDFRONT
```

---

## 💰 Cost Estimation

### **Monthly Costs (Example)**

| Service                         | Usage          | Cost             |
| ------------------------------- | -------------- | ---------------- |
| **S3 Storage**                  | 1 GB           | $0.023           |
| **CloudFront**                  | 10 GB transfer | $0.10            |
| **CloudFront Requests**         | 1M requests    | $0.75            |
| **Route 53** (if custom domain) | 1 hosted zone  | $0.50            |
| **Total**                       |                | **~$1.40/month** |

### **Cost Optimization Tips**

- Use CloudFront free tier (1TB/month first year)
- Enable S3 Intelligent Tiering for older builds
- Monitor usage with AWS Cost Explorer
- Set up billing alerts

---

## ✅ Deployment Checklist

### **Pre-Deployment**

- [ ] AWS credentials configured (`aws configure`)
- [ ] Backend services deployed and accessible
- [ ] Domain name ready (optional)
- [ ] SSL certificate requested (if custom domain)

### **Infrastructure Setup**

- [ ] Run `./setup-frontend-deployment.sh`
- [ ] Verify Terraform outputs generated
- [ ] Test S3 bucket and CloudFront creation
- [ ] Confirm IAM roles and policies

### **Deployment**

- [ ] Frontend builds successfully locally
- [ ] Environment variables configured
- [ ] Run deployment script
- [ ] Verify CloudFront invalidation completes
- [ ] Test frontend URL accessibility

### **Post-Deployment**

- [ ] Test user registration/login flow
- [ ] Verify API calls work correctly
- [ ] Check browser console for errors
- [ ] Test document upload functionality
- [ ] Monitor CloudWatch metrics

---

## 🎯 Production Checklist

### **Performance**

- [ ] Page load time < 2 seconds
- [ ] CloudFront cache hit ratio > 90%
- [ ] Lighthouse score > 90
- [ ] Mobile performance optimized

### **Security**

- [ ] HTTPS only (HTTP redirects)
- [ ] Security headers present
- [ ] No sensitive data in client code
- [ ] API keys properly configured

### **Monitoring**

- [ ] CloudWatch alarms configured
- [ ] Error tracking set up
- [ ] Usage analytics enabled
- [ ] Cost monitoring alerts

### **Backup & Recovery**

- [ ] Infrastructure as code (Terraform)
- [ ] Deployment scripts version controlled
- [ ] Rollback procedure documented
- [ ] Disaster recovery plan

---

## 🚀 **Summary**

Your Document Intelligence frontend is now deployable to AWS with:

✅ **Global CDN** - CloudFront edge caching worldwide  
✅ **Optimized Performance** - Smart caching strategies  
✅ **Automated Deployment** - One-command deployment  
✅ **Security Best Practices** - HTTPS, security headers, secure access  
✅ **Cost Optimization** - Efficient resource usage  
✅ **Monitoring Ready** - CloudWatch integration  
✅ **Scalable Architecture** - Handles traffic spikes automatically

**Your users will experience lightning-fast page loads from anywhere in the world! 🌍⚡**
