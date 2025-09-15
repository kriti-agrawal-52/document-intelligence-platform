# =============================================================================
# FRONTEND INFRASTRUCTURE - AWS APP RUNNER
# =============================================================================
#
# LEARNING OBJECTIVE: Deploy a dynamic Next.js application using AWS App Runner
# for zero-infrastructure-management serverless container deployment.
#
# KEY CONCEPTS:
# 1. AWS App Runner: Fully managed container service for web applications
# 2. Auto Scaling: Automatically scales based on traffic with zero configuration
# 3. Built-in SSL: HTTPS certificates managed automatically
# 4. Container Registry: Uses ECR to store and deploy container images
# 5. VPC Connector: Secure connection to backend services in private VPC
#
# ARCHITECTURE FLOW:
# Internet → App Runner (Auto SSL) → Next.js Container → VPC Connector → Backend Services
#     ↓              ↓                    ↓                 ↓              ↓
# HTTPS Only    Auto Scaling        Dynamic Content     Private Network   ECS Services
# =============================================================================

# STEP 1: Create ECR Repository for Frontend Container Images
# PURPOSE: Store Docker images for the Next.js application
# WHY ECR: Secure, private container registry integrated with AWS services
resource "aws_ecr_repository" "frontend_repo" {
  name                 = "${var.project_name}-frontend"
  image_tag_mutability = "MUTABLE" # Allow updating 'latest' tag for deployments

  # IMAGE SCANNING: Automatically scan for security vulnerabilities
  image_scanning_configuration {
    scan_on_push = true # Scan every new image for CVEs and security issues
  }

  # ENCRYPTION: Encrypt container images at rest
  encryption_configuration {
    encryption_type = "AES256" # AWS managed encryption (no additional cost)
  }

  tags = {
    Name        = "${var.project_name}-frontend-ecr"
    Environment = var.environment
    Purpose     = "Frontend Container Registry"
  }
}

# STEP 2: ECR Lifecycle Policy for Cost Management
# PURPOSE: Automatically delete old container images to reduce storage costs
# STRATEGY: Keep recent images for rollback, delete old ones
resource "aws_ecr_lifecycle_policy" "frontend_lifecycle" {
  repository = aws_ecr_repository.frontend_repo.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 production images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "release"] # Keep versioned releases
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep only latest 3 untagged images"
        selection = {
          tagStatus   = "untagged"
          countType   = "imageCountMoreThan"
          countNumber = 3
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# STEP 3: IAM Role for App Runner Service
# PURPOSE: Allow App Runner to pull images from ECR and access AWS services
# SECURITY: Service-linked role with minimal required permissions
resource "aws_iam_role" "apprunner_instance_role" {
  name = "${var.project_name}-apprunner-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-apprunner-instance-role"
    Environment = var.environment
    Purpose     = "App Runner Service Role"
  }
}

# STEP 4: IAM Role for App Runner Access (ECR Pull Permissions)
# PURPOSE: Allow App Runner to pull container images from ECR
resource "aws_iam_role" "apprunner_access_role" {
  name = "${var.project_name}-apprunner-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-apprunner-access-role"
    Environment = var.environment
    Purpose     = "App Runner ECR Access Role"
  }
}

# STEP 5: Attach ECR Access Policy to App Runner Access Role
# PURPOSE: Grant permission to pull images from our ECR repository
resource "aws_iam_role_policy_attachment" "apprunner_access_policy" {
  role       = aws_iam_role.apprunner_access_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# STEP 6: Custom IAM Policy for Backend API Access
# PURPOSE: Allow frontend to make API calls to backend services
resource "aws_iam_role_policy" "apprunner_backend_access" {
  name = "${var.project_name}-apprunner-backend-access"
  role = aws_iam_role.apprunner_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:*"
      }
    ]
  })
}

# STEP 7: VPC Connector for Backend Access
# PURPOSE: Allow App Runner to securely connect to backend services in private VPC
# BENEFIT: Frontend can make direct calls to backend without going through internet
resource "aws_apprunner_vpc_connector" "frontend_vpc_connector" {
  vpc_connector_name = "${var.project_name}-frontend-vpc-connector"
  subnets            = module.vpc.private_subnets
  security_groups    = [aws_security_group.frontend_sg.id]

  tags = {
    Name        = "${var.project_name}-frontend-vpc-connector"
    Environment = var.environment
    Purpose     = "Frontend to Backend Connectivity"
  }
}

# STEP 8: Security Group for Frontend App Runner
# PURPOSE: Control network access for the frontend service
resource "aws_security_group" "frontend_sg" {
  name_prefix = "${var.project_name}-frontend-apprunner-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for Frontend App Runner service"

  # OUTBOUND RULES: Allow frontend to connect to backend services
  egress {
    description = "HTTPS to backend services"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "HTTP to backend services"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Backend API ports"
    from_port   = 8000
    to_port     = 8002
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Internet access for external APIs"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-frontend-apprunner-sg"
    Environment = var.environment
    Purpose     = "Frontend App Runner Security"
  }
}

# STEP 9: App Runner Service Configuration
# PURPOSE: Deploy the Next.js frontend as a managed container service
# BENEFITS: Auto-scaling, SSL, load balancing, monitoring - all managed by AWS
resource "aws_apprunner_service" "frontend_service" {
  service_name = "${var.project_name}-frontend"

  # SOURCE CONFIGURATION: Where to get the container image
  source_configuration {
    # AUTO DEPLOYMENTS: Automatically deploy when new images are pushed
    auto_deployments_enabled = true

    # AUTHENTICATION: IAM role for pulling images from ECR
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access_role.arn
    }

    image_repository {
      # CONTAINER IMAGE: Point to our ECR repository
      image_identifier      = "${aws_ecr_repository.frontend_repo.repository_url}:latest"
      image_repository_type = "ECR"

      # CONTAINER CONFIGURATION: How to run the Next.js app
      image_configuration {
        port = "3000" # Next.js default port

        # ENVIRONMENT VARIABLES: Configure the app for production
        runtime_environment_variables = {
          # Backend API URLs will be set by GitHub Actions during deployment
          # The ALB DNS name is determined after Kubernetes ingress is created

          # App Configuration
          NODE_ENV                = "production"
          NEXT_PUBLIC_APP_NAME    = "Document Intelligence Platform"
          NEXT_PUBLIC_APP_VERSION = "1.0.0"

          # Performance Optimizations
          NEXT_TELEMETRY_DISABLED = "1"
        }

        # STARTUP COMMAND: How to start the Next.js application
        start_command = "pnpm start"
      }
    }
  }

  # INSTANCE CONFIGURATION: Resource allocation and scaling
  instance_configuration {
    # INSTANCE SIZE: CPU and memory allocation
    cpu    = "1 vCPU" # 1 virtual CPU core
    memory = "2 GB"   # 2 GB RAM

    # IAM ROLE: Permissions for the running container
    instance_role_arn = aws_iam_role.apprunner_instance_role.arn
  }

  # AUTO SCALING: Automatically scale based on traffic
  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.frontend_scaling.arn

  # HEALTH CHECK: Configure health monitoring
  health_check_configuration {
    healthy_threshold   = 1             # Consider healthy after 1 successful check
    interval            = 10            # Check every 10 seconds
    path                = "/api/health" # Our custom health endpoint
    protocol            = "HTTP"
    timeout             = 5 # 5 second timeout per check
    unhealthy_threshold = 5 # Consider unhealthy after 5 failed checks
  }

  # VPC CONNECTIVITY: Connect to backend services in private VPC
  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.frontend_vpc_connector.arn
    }
  }

  tags = {
    Name        = "${var.project_name}-frontend-apprunner"
    Environment = var.environment
    Purpose     = "Frontend Web Application"
  }

  # DEPENDENCIES: Ensure these resources exist before creating the service
  depends_on = [
    aws_iam_role_policy_attachment.apprunner_access_policy,
    aws_apprunner_vpc_connector.frontend_vpc_connector
  ]
}

# STEP 10: Auto Scaling Configuration
# PURPOSE: Define how the frontend should scale based on traffic
resource "aws_apprunner_auto_scaling_configuration_version" "frontend_scaling" {
  auto_scaling_configuration_name = "${var.project_name}-frontend-scaling"

  # SCALING LIMITS: Minimum and maximum number of instances
  min_size = 1  # Always keep at least 1 instance running
  max_size = 10 # Scale up to 10 instances under high load

  # CONCURRENCY: How many requests each instance can handle
  max_concurrency = 100 # Each instance can handle 100 concurrent requests

  tags = {
    Name        = "${var.project_name}-frontend-scaling"
    Environment = var.environment
    Purpose     = "Frontend Auto Scaling Configuration"
  }
}

# STEP 11: Custom Domain Configuration (Optional)
# PURPOSE: Use your own domain instead of the default App Runner URL
# UNCOMMENT AND CONFIGURE IF YOU HAVE A CUSTOM DOMAIN
/*
resource "aws_apprunner_custom_domain_association" "frontend_domain" {
  domain_name = "app.yourdomain.com"  # Replace with your domain
  service_arn = aws_apprunner_service.frontend_service.arn

  # DNS VALIDATION: App Runner will provide DNS records to add to your domain
  # You'll need to add these records to your DNS provider (Route 53, Cloudflare, etc.)
}
*/

# STEP 12: CloudWatch Log Group for Application Logs
# PURPOSE: Centralized logging for debugging and monitoring
resource "aws_cloudwatch_log_group" "frontend_logs" {
  name              = "/aws/apprunner/${var.project_name}-frontend"
  retention_in_days = 30 # Keep logs for 30 days

  tags = {
    Name        = "${var.project_name}-frontend-logs"
    Environment = var.environment
    Purpose     = "Frontend Application Logs"
  }
}

# =============================================================================
# OUTPUTS: Important values for deployment and monitoring
# =============================================================================

# ECR REPOSITORY URL: Used by CI/CD to push container images
output "frontend_ecr_repository_url" {
  description = "ECR repository URL for frontend container images"
  value       = aws_ecr_repository.frontend_repo.repository_url
  # USAGE: docker push <this-url>:latest
}

# APP RUNNER SERVICE URL: The public URL where your app is accessible
output "frontend_app_runner_url" {
  description = "App Runner service URL for the frontend"
  value       = "https://${aws_apprunner_service.frontend_service.service_url}"
  # EXAMPLE: https://abc123.us-west-2.awsapprunner.com
  # USAGE: This is your live application URL
}

# APP RUNNER SERVICE ARN: For monitoring and management
output "frontend_app_runner_arn" {
  description = "App Runner service ARN"
  value       = aws_apprunner_service.frontend_service.arn
  # USAGE: AWS CLI commands, monitoring tools, IAM policies
}

# DEPLOYMENT INFORMATION
output "frontend_deployment_info" {
  description = "Frontend deployment information"
  value = {
    service_name   = aws_apprunner_service.frontend_service.service_name
    service_url    = aws_apprunner_service.frontend_service.service_url
    ecr_repository = aws_ecr_repository.frontend_repo.repository_url
    auto_scaling   = "1-10 instances, 100 concurrent requests per instance"
    health_check   = "/api/health"
    vpc_connected  = true
  }
}

# COST ESTIMATION
output "frontend_cost_estimation" {
  description = "Estimated monthly cost breakdown"
  value = {
    base_cost          = "$25-50/month (1-2 instances running)"
    scaling_cost       = "$25/instance/month under load"
    data_transfer      = "$0.09/GB outbound"
    container_registry = "$0.10/GB/month for image storage"
    note               = "Costs scale with actual usage - pay only for what you use"
  }
}

# MONITORING AND LOGS
output "frontend_monitoring_info" {
  description = "Monitoring and logging information"
  value = {
    cloudwatch_logs     = aws_cloudwatch_log_group.frontend_logs.name
    health_check_url    = "https://${aws_apprunner_service.frontend_service.service_url}/api/health"
    auto_scaling_config = aws_apprunner_auto_scaling_configuration_version.frontend_scaling.arn
  }
}
