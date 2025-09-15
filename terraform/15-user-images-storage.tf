# =============================================================================
# USER IMAGES STORAGE - S3 BUCKET FOR UPLOADED DOCUMENTS
# =============================================================================
#
# PURPOSE: Store user-uploaded images (documents) securely with metadata
# SECURITY: Private bucket with CloudFront access for thumbnails
# METADATA: Each image includes user_id and image_name for tracking
# ARCHITECTURE: Images stored in S3 → DocumentDB references S3 URLs
#
# STORAGE PATTERN:
# /user-images/{user_id}/{image_name}_{timestamp}.{extension}
# EXAMPLE: /user-images/123/document_20241201_143022.jpg
# =============================================================================

# STEP 1: Create a unique suffix for the user images bucket
resource "random_string" "user_images_bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# STEP 2: Create S3 bucket for user-uploaded images
resource "aws_s3_bucket" "user_images_bucket" {
  bucket = "${var.project_name}-user-images-${random_string.user_images_bucket_suffix.result}"

  provider = aws

  tags = {
    Name        = "${var.project_name}-user-images"
    Environment = var.environment
    Purpose     = "User Uploaded Document Images"
    Region      = var.aws_region
    Backup      = "enabled"
    DataType    = "user-content"
  }
}

# STEP 3: Enable versioning for image backup and rollback
resource "aws_s3_bucket_versioning" "user_images_versioning" {
  bucket = aws_s3_bucket.user_images_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# STEP 4: Configure lifecycle rules for cost management
resource "aws_s3_bucket_lifecycle_configuration" "user_images_lifecycle" {
  bucket     = aws_s3_bucket.user_images_bucket.id
  depends_on = [aws_s3_bucket_versioning.user_images_versioning]

  rule {
    id     = "user_images_lifecycle"
    status = "Enabled"

    # Filter to apply rule to all objects
    filter {
      prefix = ""
    }

    # Current version management - keep images for 1 year
    expiration {
      days = 365
    }

    # Cost optimization - move old versions to cheaper storage after 30 days
    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    # Old version management - delete old versions after 90 days
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# STEP 5: Enable encryption for data security
resource "aws_s3_bucket_server_side_encryption_configuration" "user_images_encryption" {
  bucket = aws_s3_bucket.user_images_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# STEP 6: Block all public access (security)
resource "aws_s3_bucket_public_access_block" "user_images_pab" {
  bucket = aws_s3_bucket.user_images_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# STEP 7: Configure bucket policy for secure access
resource "aws_s3_bucket_policy" "user_images_policy" {
  bucket = aws_s3_bucket.user_images_bucket.id

  depends_on = [
    aws_s3_bucket_public_access_block.user_images_pab
  ]

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      # Allow CloudFront to read images for thumbnails
      {
        Sid    = "AllowCloudFrontServicePrincipalReadOnly"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.user_images_bucket.arn}/*"

        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend_distribution.arn
          }
        }
      },

      # Allow admin users full access for management
      {
        Sid    = "AllowAdminUserFullAccess"
        Effect = "Allow"
        Principal = {
          AWS = data.aws_caller_identity.current.arn
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetObjectVersion",
          "s3:DeleteObjectVersion"
        ]
        Resource = [
          aws_s3_bucket.user_images_bucket.arn,
          "${aws_s3_bucket.user_images_bucket.arn}/*"
        ]
      }
    ]
  })
}

# STEP 8: Configure CORS for frontend access
resource "aws_s3_bucket_cors_configuration" "user_images_cors" {
  bucket = aws_s3_bucket.user_images_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = [
      "https://dw9izoh5i5hj1.cloudfront.net", # CloudFront domain
      "http://localhost:3000",                # Local development
      "http://localhost:3001"                 # Alternative local port
    ]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
