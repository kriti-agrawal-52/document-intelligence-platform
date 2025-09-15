# /terraform/09-outputs.tf
#
# FILE PURPOSE:
# This file declares all the output values for our Terraform project. After Terraform
# successfully creates or updates the infrastructure, it will print these values to the
# console. Outputs are a way to expose important information about the resources we've
# created, such as server IP addresses, database endpoints, or resource ARNs.
# This is extremely useful for configuring other systems (like our Kubernetes manifests)
# or for simply connecting to the resources after they are created.

# --- VPC Output ---
# This output exposes the unique ID of the VPC we created.
output "vpc_id" {
  description = "The ID of the created VPC."
  # The `value` is retrieved from the `vpc` module's outputs.
  value       = module.vpc.vpc_id
}

# --- EKS Cluster Outputs ---
# This output provides the API server endpoint for our EKS cluster. We use this URL
# to configure `kubectl` to communicate with our cluster.
output "eks_cluster_endpoint" {
  description = "The endpoint for the EKS cluster."
  value       = module.eks.cluster_endpoint
}

# This output provides the name of the EKS cluster.
output "eks_cluster_name" {
  description = "The name of the EKS cluster."
  value       = module.eks.cluster_name
}

# --- Database Outputs ---
# This output provides the connection endpoint for our RDS MySQL instance.
# Our application will use this hostname to connect to the database.
output "rds_endpoint" {
  description = "The endpoint of the RDS MySQL instance."
  value       = aws_db_instance.mysql_db.endpoint
}

# This output provides the connection endpoint for our DocumentDB cluster.
output "docdb_endpoint" {
  description = "The endpoint of the DocumentDB cluster."
  value       = aws_docdb_cluster.docdb.endpoint
}

# --- Redis Cache Output ---
# This output provides the connection endpoint for our ElastiCache for Redis cluster.
output "redis_endpoint" {
  description = "The primary endpoint of the ElastiCache for Redis cluster."
  # We get the address of the first (and only) node in the cluster.
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

# --- ECR Repository Outputs ---
# These outputs provide the full URL for each of our ECR repositories. We need these
# URLs to tag and push our Docker images.
output "auth_service_ecr_url" {
  description = "The URL of the ECR repository for the auth service."
  value       = aws_ecr_repository.auth_service_ecr.repository_url
}

output "text_extraction_service_ecr_url" {
  description = "The URL of the ECR repository for the text extraction service."
  value       = aws_ecr_repository.text_extraction_service_ecr.repository_url
}

# --- ECR Repository Output for Summarization Service ---
# *** FIX: Ensure the output name is 'text_summarization_service_ecr_url' to match the script ***
output "text_summarization_service_ecr_url" {
  description = "The URL of the ECR repository for the text summarization service."
  # The value correctly references the resource defined in 06-ecr.tf
  value       = aws_ecr_repository.text_summarization_service_ecr.repository_url
}

# --- SQS Queue Output ---
# This output provides the unique URL of our SQS queue. Our producer and consumer
# applications will use this URL to interact with the queue.
output "sqs_summarization_queue_url" {
  description = "The URL of the SQS queue for summarization jobs."
  value       = aws_sqs_queue.summarization_queue.id
}

# --- Application Load Balancer URL ---
# Note: This ALB is created by Kubernetes ingress controller, not directly by Terraform
# The actual URL should be retrieved from the Kubernetes ingress resource
# This is a placeholder that can be updated by external scripts
output "alb_url" {
  description = "The URL of the Application Load Balancer created by Kubernetes ingress controller"
  value       = "http://k8s-docintel-docintel-48f655f88f-1320207614.ap-south-1.elb.amazonaws.com"
}

# --- Load Balancer Controller Status ---
# This output provides the status of the AWS Load Balancer Controller deployment.
output "aws_load_balancer_controller_status" {
  description = "The status of the AWS Load Balancer Controller."
  value = {
    name      = helm_release.aws_load_balancer_controller.name
    namespace = helm_release.aws_load_balancer_controller.namespace
    status    = helm_release.aws_load_balancer_controller.status
    version   = helm_release.aws_load_balancer_controller.version
  }
}

# --- User Images S3 Bucket Outputs ---
# These outputs provide information about the S3 bucket used for storing user-uploaded images.
# The text extraction service uses this bucket to store document images securely.
output "user_images_bucket_name" {
  description = "Name of the S3 bucket for user uploaded images"
  value       = aws_s3_bucket.user_images_bucket.id
}

output "user_images_bucket_arn" {
  description = "ARN of the S3 bucket for user uploaded images"
  value       = aws_s3_bucket.user_images_bucket.arn
}

output "user_images_bucket_region" {
  description = "Region where user images are stored"
  value       = var.aws_region
}