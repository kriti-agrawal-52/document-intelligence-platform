#!/bin/bash

# =============================================================================
# FRONTEND DEPLOYMENT SCRIPT FOR AWS APP RUNNER
# =============================================================================
# 
# This script builds the Next.js Docker image and deploys it to AWS App Runner
# via Amazon ECR (Elastic Container Registry).
#
# PREREQUISITES:
# 1. AWS CLI installed and configured
# 2. Docker installed and running
# 3. Terraform outputs available (ECR repository URL)
# 4. Proper IAM permissions for ECR operations
#
# USAGE:
#   ./scripts/deploy-frontend.sh
#   ./scripts/deploy-frontend.sh --tag v1.2.3
#   ./scripts/deploy-frontend.sh --region us-west-2
# =============================================================================

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Default configuration
DEFAULT_REGION="ap-south-1"
DEFAULT_TAG="latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --tag TAG        Docker image tag (default: latest)"
    echo "  --region REGION  AWS region (default: ap-south-1)"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Deploy with default settings"
    echo "  $0 --tag v1.2.3           # Deploy with specific version tag"
    echo "  $0 --region us-west-2      # Deploy to specific region"
}

# Parse command line arguments
REGION="$DEFAULT_REGION"
TAG="$DEFAULT_TAG"

while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    # Check if we're in the right directory
    if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
        print_error "Frontend directory not found. Please run this script from the project root."
        exit 1
    fi

    # Check if Terraform directory exists
    if [[ ! -d "$TERRAFORM_DIR" ]]; then
        print_error "Terraform directory not found. Please ensure infrastructure is set up."
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Function to get ECR repository URL from Terraform output
get_ecr_repository_url() {
    print_status "Getting ECR repository URL from Terraform..."
    
    cd "$TERRAFORM_DIR"
    
    if ! ECR_REPO_URL=$(terraform output -raw frontend_ecr_repository_url 2>/dev/null); then
        print_error "Failed to get ECR repository URL from Terraform output."
        print_error "Make sure you've run 'terraform apply' to create the infrastructure."
        exit 1
    fi
    
    if [[ -z "$ECR_REPO_URL" ]]; then
        print_error "ECR repository URL is empty. Check your Terraform configuration."
        exit 1
    fi
    
    print_success "ECR repository URL: $ECR_REPO_URL"
    cd - > /dev/null
}

# Function to authenticate Docker with ECR
authenticate_ecr() {
    print_status "Authenticating Docker with ECR..."
    
    if ! aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_REPO_URL"; then
        print_error "Failed to authenticate with ECR. Check your AWS credentials and permissions."
        exit 1
    fi
    
    print_success "Successfully authenticated with ECR"
}

# Function to build Docker image
build_docker_image() {
    print_status "Building Docker image for Next.js frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Create .env.local for build if it doesn't exist
    if [[ ! -f ".env.local" ]]; then
        print_warning "Creating .env.local with default values..."
        cat > .env.local << EOF
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8000
NEXT_PUBLIC_EXTRACTION_SERVICE_URL=http://localhost:8001
NEXT_PUBLIC_SUMMARIZATION_SERVICE_URL=http://localhost:8002
NEXT_PUBLIC_APP_NAME=Document Intelligence Platform
NEXT_PUBLIC_APP_VERSION=1.0.0
EOF
    fi
    
    # Build the Docker image
    if ! docker build -t "$ECR_REPO_URL:$TAG" .; then
        print_error "Failed to build Docker image"
        exit 1
    fi
    
    # Also tag as latest if not already latest
    if [[ "$TAG" != "latest" ]]; then
        docker tag "$ECR_REPO_URL:$TAG" "$ECR_REPO_URL:latest"
    fi
    
    print_success "Successfully built Docker image: $ECR_REPO_URL:$TAG"
    cd - > /dev/null
}

# Function to push Docker image to ECR
push_docker_image() {
    print_status "Pushing Docker image to ECR..."
    
    # Push the specific tag
    if ! docker push "$ECR_REPO_URL:$TAG"; then
        print_error "Failed to push Docker image with tag: $TAG"
        exit 1
    fi
    
    # Push latest tag if we created it
    if [[ "$TAG" != "latest" ]]; then
        if ! docker push "$ECR_REPO_URL:latest"; then
            print_error "Failed to push Docker image with tag: latest"
            exit 1
        fi
    fi
    
    print_success "Successfully pushed Docker image to ECR"
}

# Function to wait for App Runner deployment
wait_for_deployment() {
    print_status "Waiting for App Runner to deploy the new image..."
    
    cd "$TERRAFORM_DIR"
    
    if SERVICE_ARN=$(terraform output -raw frontend_app_runner_arn 2>/dev/null); then
        print_status "Monitoring App Runner deployment status..."
        
        # Wait for deployment to complete (max 10 minutes)
        local max_attempts=60
        local attempt=1
        
        while [[ $attempt -le $max_attempts ]]; do
            local status=$(aws apprunner describe-service --service-arn "$SERVICE_ARN" --region "$REGION" --query 'Service.Status' --output text)
            
            case $status in
                "RUNNING")
                    print_success "App Runner service is running successfully!"
                    break
                    ;;
                "OPERATION_IN_PROGRESS")
                    print_status "Deployment in progress... (attempt $attempt/$max_attempts)"
                    ;;
                "CREATE_FAILED"|"UPDATE_FAILED"|"DELETE_FAILED")
                    print_error "App Runner deployment failed with status: $status"
                    exit 1
                    ;;
                *)
                    print_warning "Unknown status: $status"
                    ;;
            esac
            
            sleep 10
            ((attempt++))
        done
        
        if [[ $attempt -gt $max_attempts ]]; then
            print_warning "Deployment monitoring timed out. Check AWS console for status."
        fi
    else
        print_warning "Could not get App Runner ARN. Deployment status unknown."
    fi
    
    cd - > /dev/null
}

# Function to display deployment information
show_deployment_info() {
    print_status "Deployment completed! Here's your application information:"
    
    cd "$TERRAFORM_DIR"
    
    if APP_URL=$(terraform output -raw frontend_app_runner_url 2>/dev/null); then
        echo ""
        echo "🚀 Application URL: $APP_URL"
        echo "📊 Health Check: $APP_URL/api/health"
        echo "📝 Logs: AWS CloudWatch -> /aws/apprunner/doc-intel-frontend"
        echo "🔧 Monitoring: AWS Console -> App Runner -> Services"
        echo ""
        print_success "Frontend successfully deployed to AWS App Runner!"
    else
        print_warning "Could not retrieve App Runner URL from Terraform output."
    fi
    
    cd - > /dev/null
}

# Function to cleanup local Docker images (optional)
cleanup_local_images() {
    print_status "Cleaning up local Docker images..."
    
    # Remove the built images to save disk space
    docker rmi "$ECR_REPO_URL:$TAG" 2>/dev/null || true
    if [[ "$TAG" != "latest" ]]; then
        docker rmi "$ECR_REPO_URL:latest" 2>/dev/null || true
    fi
    
    # Clean up dangling images
    docker image prune -f > /dev/null 2>&1 || true
    
    print_success "Cleaned up local Docker images"
}

# Main deployment function
main() {
    echo "============================================="
    echo "🚀 Frontend Deployment to AWS App Runner"
    echo "============================================="
    echo "Region: $REGION"
    echo "Tag: $TAG"
    echo "============================================="
    echo ""

    check_prerequisites
    get_ecr_repository_url
    authenticate_ecr
    build_docker_image
    push_docker_image
    wait_for_deployment
    show_deployment_info
    cleanup_local_images

    echo ""
    echo "============================================="
    print_success "🎉 Deployment completed successfully!"
    echo "============================================="
}

# Run main function
main "$@"
