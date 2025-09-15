# /terraform/06-ecr.tf
#
# FILE PURPOSE:
# This file is responsible for creating the Amazon Elastic Container Registry (ECR)
# repositories. ECR is a managed Docker container registry service. These repositories
# will securely store the Docker images for our microservices after we build them.
# The EKS cluster will then pull the images from these repositories to run our application pods.

# --- ECR Repository for the Authentication Service ---
resource "aws_ecr_repository" "auth_service_ecr" {
  name                 = "auth-service-v2"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# --- ECR Repository for the Text Extraction Service ---
resource "aws_ecr_repository" "text_extraction_service_ecr" {
  name                 = "text-extraction-service-v2"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# --- ECR Repository for the Text Summarization Service ---
# *** FIX: Ensure the resource name uses 'summarization' with a 'z' ***
resource "aws_ecr_repository" "text_summarization_service_ecr" {
  # The `name` tag is what you see in the AWS Console.
  name                 = "text-summarization-service-v2"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}