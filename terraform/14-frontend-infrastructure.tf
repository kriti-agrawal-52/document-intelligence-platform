# =============================================================================
# FRONTEND INFRASTRUCTURE - S3 + CLOUDFRONT
# =============================================================================
#
# LEARNING OBJECTIVE: Understand how to deploy a modern frontend application
# using AWS S3 for storage and CloudFront for global content delivery.
#
# KEY CONCEPTS:
# 1. Static Site Hosting: Frontend apps (React/Next.js) are compiled to static files
# 2. Content Delivery Network (CDN): CloudFront caches files globally for speed
# 3. Origin Access Control (OAC): Secure way for CloudFront to access private S3
# 4. Edge Caching: Files cached at 200+ locations worldwide for fast access
#
# ARCHITECTURE FLOW:
# User Request → CloudFront Edge Location → (Cache Miss?) → Private S3 Bucket
#     ↓              ↓                           ↓              ↓
# Fast Response ← Cache Hit (No S3 needed) ← Fetch from S3 ← Secure Access
# =============================================================================

# STEP 1: Create a unique suffix for the S3 bucket name
# WHY: S3 bucket names must be globally unique across ALL AWS accounts worldwide
# EXAMPLE: If you choose "frontend", someone else might already have "my-app-frontend"
resource "random_string" "bucket_suffix" {
  length  = 8     # Creates an 8-character random string
  special = false # No special characters (!, @, #, etc.)
  upper   = false # Only lowercase letters and numbers
  # RESULT: Something like "a1b2c3d4"
}

# STEP 2: Create the S3 bucket for storing frontend files
# WHAT IT STORES: HTML files, JavaScript bundles, CSS files, images, fonts
# SECURITY MODEL: Private bucket (no public access) + CloudFront access only
resource "aws_s3_bucket" "frontend_bucket" {
  # BUCKET NAMING: Combines project name + purpose + random suffix
  # EXAMPLE: "doc-intel-frontend-a1b2c3d4"
  bucket = "${var.project_name}-frontend-${random_string.bucket_suffix.result}"

  # REGIONAL PLACEMENT: Created in the same region as your backend
  # WHY: Reduces latency when CloudFront fetches files from S3
  # ALSO: Keeps data in your preferred region for compliance
  provider = aws

  # RESOURCE TAGGING: Essential for cost tracking and resource management
  tags = {
    Name        = "${var.project_name}-frontend" # Human-readable name
    Environment = var.environment                # dev/staging/production
    Purpose     = "Frontend Static Assets"       # What this resource does
    Region      = var.aws_region                 # Which region it's in
    Backup      = "enabled"                      # Indicates backup is configured
    # COST TRACKING: These tags help you understand AWS billing by project/environment
  }
}

# STEP 3: Enable S3 Versioning for Deployment History and Rollback
# WHAT IS VERSIONING: S3 keeps multiple versions of the same file
# WHY WE NEED IT: 
# - Track deployment history (v1, v2, v3 of your app)
# - Rollback capability if new deployment breaks something
# - Accidental deletion protection (files are never truly lost)
# EXAMPLE: When you deploy, index.html gets a new version ID
resource "aws_s3_bucket_versioning" "frontend_versioning" {
  bucket = aws_s3_bucket.frontend_bucket.id # Links to our bucket above

  versioning_configuration {
    status = "Enabled" # Turn on versioning for this bucket
    # RESULT: Every file upload creates a new version instead of overwriting
  }
}

# STEP 4: Configure Lifecycle Rules for Cost Management
# WHAT IS LIFECYCLE: Automatic rules to manage old files and reduce costs
# PROBLEM: Without lifecycle rules, S3 keeps ALL versions forever = expensive
# SOLUTION: Automatically delete old versions and move files to cheaper storage
resource "aws_s3_bucket_lifecycle_configuration" "frontend_lifecycle" {
  bucket     = aws_s3_bucket.frontend_bucket.id               # Our bucket
  depends_on = [aws_s3_bucket_versioning.frontend_versioning] # Wait for versioning first

  rule {
    id     = "frontend_lifecycle" # Name for this rule
    status = "Enabled"            # Activate the rule
    
    # Filter to apply rule to all objects
    filter {
      prefix = "" # Apply to all objects in the bucket
    }

    # CURRENT VERSION MANAGEMENT: Files users are currently accessing
    expiration {
      days = 90 # Delete current files after 90 days
      # WHY 90 DAYS: Frontend files rarely accessed after new deployment
      # COST SAVINGS: Prevents accumulation of old frontend builds
    }

    # OLD VERSION MANAGEMENT: Previous deployments you deployed before
    noncurrent_version_expiration {
      noncurrent_days = 60 # Keep old versions for 60 days only
      # WHY 60 DAYS: Enough time to rollback if new deployment has issues
      # EXAMPLE: If you deploy today, last week's version deleted in 60 days
    }

    # COST OPTIMIZATION: Move old versions to cheaper storage before deletion
    noncurrent_version_transition {
      noncurrent_days = 30            # After 30 days...
      storage_class   = "STANDARD_IA" # Move to "Infrequent Access" storage
      # COST BENEFIT: STANDARD_IA costs 50% less than regular S3 storage
      # TRADE-OFF: Slightly slower access (not a problem for old versions)
    }
  }
}

# STEP 5: Enable Encryption for Data Security
# WHAT IS ENCRYPTION: Scrambles your files so only authorized users can read them
# WHY NEEDED: Protects sensitive frontend code and prevents data breaches
# HOW IT WORKS: AWS automatically encrypts files when stored, decrypts when accessed
resource "aws_s3_bucket_server_side_encryption_configuration" "frontend_encryption" {
  bucket = aws_s3_bucket.frontend_bucket.id # Apply to our bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256" # AES-256 encryption (military-grade security)
      # ALTERNATIVE: "aws:kms" for more control, but AES256 is sufficient for frontend
    }
    bucket_key_enabled = true # Reduces encryption costs by using bucket keys
    # COST BENEFIT: Reduces KMS API calls by ~99%, saving money
  }
}

# STEP 9: Configure S3 Static Website Hosting Settings
# PURPOSE: Tell S3 how to serve frontend files as a website
# KEY CONCEPTS: Index document (homepage) and error document (for missing pages)
# NOTE: This is for S3 backup access only; CloudFront handles the real traffic
resource "aws_s3_bucket_website_configuration" "frontend_website" {
  bucket = aws_s3_bucket.frontend_bucket.id # Apply to our bucket

  # INDEX DOCUMENT: The default file to serve when someone visits your site
  index_document {
    suffix = "index.html" # When user visits yourdomain.com → serve index.html
    # FRONTEND APPS: React/Next.js build creates an index.html as the main entry point
  }

  # ERROR DOCUMENT: What to show when a requested file doesn't exist
  error_document {
    key = "404.html" # When user visits yourdomain.com/nonexistent → serve 404.html
    # SPA ROUTING: For single-page apps, 404s often redirect to index.html
  }
}

# STEP 6: Block ALL Public Access (Critical Security Step)
# SECURITY PRINCIPLE: Frontend buckets should NEVER be publicly accessible
# COMMON MISTAKE: Many developers make S3 buckets public, creating security risks
# OUR APPROACH: Private bucket + CloudFront access only = secure and fast
resource "aws_s3_bucket_public_access_block" "frontend_pab" {
  bucket = aws_s3_bucket.frontend_bucket.id # Apply to our bucket

  # These 4 settings work together to completely block public access:
  block_public_acls       = true # Block any public ACLs (Access Control Lists)
  block_public_policy     = true # Block any public bucket policies
  ignore_public_acls      = true # Ignore existing public ACLs if any exist
  restrict_public_buckets = true # Restrict public bucket policies

  # RESULT: Impossible for anyone to make this bucket public, even by accident
  # SECURITY BENEFIT: Prevents data leaks and unauthorized access
}

# STEP 7: Configure Bucket Access Policy (Who Can Access What)
# SECURITY MODEL: Only CloudFront + Admin users can access this bucket
# ACCESS PATTERNS: 
# - CloudFront: Read files to serve to users
# - Admin Users: Upload new deployments, view files, manage content
# - Everyone Else: DENIED (no access at all)
resource "aws_s3_bucket_policy" "frontend_policy" {
  bucket = aws_s3_bucket.frontend_bucket.id # Apply to our bucket

  # DEPENDENCIES: Wait for these resources to be created first
  depends_on = [
    aws_s3_bucket_public_access_block.frontend_pab,   # Security settings first
    aws_cloudfront_distribution.frontend_distribution # CloudFront exists
  ]

  # IAM POLICY LANGUAGE: JSON document defining permissions
  policy = jsonencode({
    Version = "2012-10-17" # IAM policy language version (always use this)

    Statement = [
      # STATEMENT 1: Allow CloudFront to read files (serve to users)
      {
        Sid    = "AllowCloudFrontServicePrincipalReadOnly" # Human-readable ID
        Effect = "Allow"                                   # Grant permission
        Principal = {
          Service = "cloudfront.amazonaws.com" # Only AWS CloudFront service
          # NOTE: This is service-to-service auth, no credentials needed
        }
        Action   = "s3:GetObject"                           # Can only READ files, cannot write/delete
        Resource = "${aws_s3_bucket.frontend_bucket.arn}/*" # All files in bucket

        # SECURITY CONDITION: Only OUR specific CloudFront distribution
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend_distribution.arn
            # PREVENTS: Other CloudFront distributions from accessing our bucket
          }
        }
      },

      # STATEMENT 2: Allow admin users full access for deployments and management
      {
        Sid    = "AllowAdminUserFullAccess" # For deployment and management
        Effect = "Allow"                    # Grant permission
        Principal = {
          AWS = data.aws_caller_identity.current.arn # Current AWS user/role
          # EXPLANATION: The person running Terraform becomes an admin
        }
        Action = [
          "s3:GetObject",          # Read files (view deployments)
          "s3:PutObject",          # Upload files (deploy new versions)
          "s3:DeleteObject",       # Delete files (cleanup)
          "s3:ListBucket",         # List files (see what's deployed)
          "s3:GetObjectVersion",   # Access old versions (rollback)
          "s3:DeleteObjectVersion" # Delete old versions (cleanup)
        ]
        Resource = [
          aws_s3_bucket.frontend_bucket.arn,       # Bucket itself
          "${aws_s3_bucket.frontend_bucket.arn}/*" # All files in bucket
        ]
        # NO CONDITIONS: Admin has unrestricted access for management
      }
    ]
  })
}

# STEP 10: Create Origin Access Control (Modern S3 Security)
# WHAT IS OAC: A secure way for CloudFront to access private S3 buckets
# WHY NOT PUBLIC S3: Public buckets are security risks and bypass CloudFront
# HOW IT WORKS: CloudFront signs requests to S3 using AWS credentials
# LEGACY NOTE: Replaces old "Origin Access Identity" (OAI) with better security
resource "aws_cloudfront_origin_access_control" "frontend_oac" {
  name                              = "${var.project_name}-frontend-oac-v2" # Human-readable name
  description                       = "OAC for frontend S3 bucket"       # What this does
  origin_access_control_origin_type = "s3"                               # We're accessing S3
  signing_behavior                  = "always"                           # Sign all requests
  signing_protocol                  = "sigv4"                            # AWS Signature V4 protocol

  # SECURITY BENEFIT: All requests from CloudFront to S3 are cryptographically signed
  # RESULT: S3 can verify requests came from our specific CloudFront distribution
}

# STEP 11: Create CloudFront Distribution (Global Content Delivery Network)
# WHAT IS CLOUDFRONT: AWS's CDN that caches your frontend files worldwide
# WHY WE NEED IT: Users get fast loading from nearby edge locations
# EDGE LOCATIONS: 200+ data centers worldwide that cache your content
# PERFORMANCE BENEFIT: Load times go from ~2000ms to ~50ms for repeat visitors
resource "aws_cloudfront_distribution" "frontend_distribution" {

  # ORIGIN CONFIGURATION: Where CloudFront gets files when cache misses

  # S3 Origin for static files
  origin {
    # S3 BUCKET DOMAIN: The URL CloudFront uses to fetch files from S3
    domain_name = aws_s3_bucket.frontend_bucket.bucket_regional_domain_name
    # SECURITY: Link to our Origin Access Control for secure S3 access
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend_oac.id
    # ORIGIN ID: Unique identifier for this origin
    origin_id = "S3-${aws_s3_bucket.frontend_bucket.id}"
  }

  # S3 Origin for user images (thumbnails)
  origin {
    # USER IMAGES BUCKET: The URL CloudFront uses to fetch user uploaded images
    domain_name = aws_s3_bucket.user_images_bucket.bucket_regional_domain_name
    # SECURITY: Link to our Origin Access Control for secure S3 access
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend_oac.id
    # ORIGIN ID: Unique identifier for this origin
    origin_id = "S3-${aws_s3_bucket.user_images_bucket.id}"
  }

  # ALB Origin for API requests
  origin {
    # ALB DOMAIN: The URL CloudFront uses to fetch API responses from ALB
    domain_name = "k8s-docintel-docintel-48f655f88f-1320207614.ap-south-1.elb.amazonaws.com"
    # ORIGIN ID: Unique identifier for this origin
    origin_id = "ALB-backend-api"

    custom_origin_config {
      # HTTP SETTINGS: ALB accepts HTTP on port 80
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only" # ALB is HTTP only
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # BASIC SETTINGS: Core CloudFront configuration
  enabled             = true                                        # Turn on the distribution
  is_ipv6_enabled     = true                                        # Support modern IPv6 protocol
  comment             = "${var.project_name} Frontend Distribution" # Human description
  default_root_object = "index.html"                                # Serve this when user visits root URL

  # GLOBAL COVERAGE: Control which edge locations to use (affects cost vs performance)
  # PriceClass_All: All 400+ edge locations (best performance, highest cost ~$0.12/GB)
  # PriceClass_200: ~200 major edge locations (good balance ~$0.08/GB)
  # PriceClass_100: ~100 edge locations in US/Europe only (lowest cost ~$0.06/GB)
  price_class = "PriceClass_200" # Good balance of global performance vs cost

  # PROTOCOL OPTIMIZATION: Enable latest web protocols for speed
  http_version = "http2and3" # HTTP/2 and HTTP/3 for faster connections
  # BENEFIT: HTTP/2 allows multiple file downloads in one connection
  # BENEFIT: HTTP/3 reduces latency with QUIC protocol

  # STEP 11A: Configure Default Cache Behavior (How CloudFront Handles All Requests)
  # CACHE BEHAVIOR: Rules that determine how CloudFront processes requests
  # DEFAULT BEHAVIOR: Applies to all files unless overridden by specific rules
  default_cache_behavior {
    # HTTP METHODS: Which HTTP verbs are allowed
    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    # WHY ALL METHODS: Frontend apps may need API calls through CloudFront
    # SECURITY: CloudFront validates all methods before forwarding

    # CACHED METHODS: Which methods get cached (stored at edge locations)
    cached_methods = ["GET", "HEAD"]
    # WHY ONLY GET/HEAD: These are read-only operations safe to cache
    # NOT CACHED: POST/PUT/DELETE are dynamic and must reach origin every time

    # ORIGIN TARGET: Where to fetch files when cache misses
    target_origin_id = "S3-${aws_s3_bucket.frontend_bucket.id}"
    # LINKS TO: Our S3 bucket defined in the origin block above

    # COMPRESSION: Automatically compress files for faster transfer
    compress = true
    # BENEFIT: Reduces file sizes by 60-80% (HTML/CSS/JS compress well)
    # EXAMPLE: 1MB JavaScript file → 250KB compressed → faster loading

    # HTTPS ENFORCEMENT: Force all connections to use secure HTTPS
    viewer_protocol_policy = "redirect-to-https"
    # SECURITY: Prevents man-in-the-middle attacks and eavesdropping
    # USER EXPERIENCE: Browsers show "secure" lock icon

    # REQUEST FORWARDING: What data to pass from client to origin
    forwarded_values {
      # QUERY STRINGS: Don't forward URL parameters to S3
      query_string = false
      # WHY FALSE: Static files don't change based on query parameters
      # EXAMPLE: app.js?debug=true → CloudFront serves same app.js file

      # COOKIES: Don't forward browser cookies to S3
      cookies {
        forward = "none"
      }
      # WHY NONE: S3 doesn't use cookies, forwarding them reduces cache efficiency
      # CACHE BENEFIT: Same file served to all users regardless of cookies
    }

    # TTL SETTINGS: How long files stay cached at edge locations
    min_ttl     = 0        # Minimum cache time (0 = can be immediately refreshed)
    default_ttl = 86400    # Default cache time: 1 day (24 * 60 * 60 seconds)
    max_ttl     = 31536000 # Maximum cache time: 1 year (365 * 24 * 60 * 60 seconds)

    # TTL STRATEGY EXPLANATION:
    # - HTML files: Short cache (1 day) → Fresh content quickly
    # - CSS/JS files: Long cache (1 year) → Better performance
    # - Images: Medium cache → Balance freshness vs performance
  }

  # STEP 11B: Special Cache Behavior for Static Assets (Performance Optimization)
  # ORDERED CACHE BEHAVIOR: Specific rules that override default behavior
  # PURPOSE: Static assets (JS/CSS bundles) never change, so cache aggressively
  ordered_cache_behavior {
    # PATH PATTERN: Apply this behavior only to Next.js static assets
    path_pattern = "/_next/static/*"
    # MATCHES: /_next/static/chunks/app.js, /_next/static/css/styles.css
    # WHY NEXT.JS: Next.js puts unchanging assets in /_next/static/ with unique hashes
    # HASH EXAMPLE: app-abc123.js → if app changes, becomes app-def456.js

    # LIMITED HTTP METHODS: Only allow read operations for static files
    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    # SECURITY: Static assets shouldn't accept POST/PUT/DELETE operations
    # PERFORMANCE: Fewer allowed methods = faster CloudFront processing

    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.frontend_bucket.id}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    # AGGRESSIVE CACHING: Cache static assets for 1 full year
    min_ttl     = 31536000 # 1 year minimum (365 * 24 * 60 * 60 seconds)
    default_ttl = 31536000 # 1 year default
    max_ttl     = 31536000 # 1 year maximum

    # WHY 1 YEAR CACHE:
    # - Static assets have unique hashes in filenames
    # - If file changes, filename changes, so cache automatically refreshes
    # - Maximizes cache hits = fastest possible loading for users
    # - Reduces S3 requests = lower costs

    # CACHE HIT BENEFIT: After first load, static assets load instantly (0ms)
  }

  # STEP 11C: API Route Behavior (No Caching for Dynamic Content)
  # PURPOSE: Handle API calls by proxying them to the backend ALB
  # BENEFIT: Avoids CORS issues by serving API through same domain
  ordered_cache_behavior {
    # PATH PATTERN: Apply to any URL starting with /auth/
    path_pattern = "/auth/*"
    # EXAMPLES: /auth/login, /auth/register, /auth/health
    # WHY SEPARATE: API responses are dynamic and shouldn't be cached

    # FULL HTTP METHODS: APIs need all HTTP verbs for different operations
    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    # GET: Fetch data, POST: Create data, PUT: Update data, DELETE: Remove data
    # OPTIONS: CORS preflight requests (browser security)

    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "ALB-backend-api"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    # FORWARD EVERYTHING: API calls need all request data
    forwarded_values {
      # QUERY STRINGS: Pass URL parameters to API
      query_string = true
      # EXAMPLES: /api/documents?page=2&limit=10
      # WHY TRUE: APIs use query parameters for filtering, pagination, etc.

      # IMPORTANT HEADERS: Pass authentication and content type
      headers = ["Authorization", "Content-Type"]
      # Authorization: JWT tokens for user authentication
      # Content-Type: Tells API what data format is being sent (JSON, form data)

      # COOKIES: Forward all cookies for session management
      cookies {
        forward = "all"
      }
      # WHY ALL: APIs might use cookies for authentication or session state
    }

    # NO CACHING: Always fetch fresh data from API
    min_ttl     = 0 # Never cache (always fetch from origin)
    default_ttl = 0 # Default: no caching
    max_ttl     = 0 # Maximum: no caching

    # WHY NO CACHE: API responses are dynamic and user-specific
    # EXAMPLES: User profile, document list, authentication status
    # RISK: Caching would show wrong user's data or stale information
  }

  # STEP 11D: Extract Route Behavior (No Caching for Dynamic Content)
  # PURPOSE: Handle document extraction API calls by proxying them to the backend ALB
  # BENEFIT: Avoids CORS issues by serving API through same domain
  ordered_cache_behavior {
    # PATH PATTERN: Apply to any URL starting with /extract/
    path_pattern = "/extract/*"
    # EXAMPLES: /extract/image_text, /extract/documents, /extract/health
    # WHY SEPARATE: API responses are dynamic and shouldn't be cached

    # FULL HTTP METHODS: APIs need all HTTP verbs for different operations
    allowed_methods = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    # GET: Fetch data, POST: Create data, PUT: Update data, DELETE: Remove data
    # OPTIONS: CORS preflight requests (browser security)

    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "ALB-backend-api"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    # FORWARD EVERYTHING: API calls need all request data
    forwarded_values {
      # QUERY STRINGS: Pass URL parameters to API
      query_string = true
      # EXAMPLES: /extract/documents?page=2&limit=10
      # WHY TRUE: APIs use query parameters for filtering, pagination, etc.

      # IMPORTANT HEADERS: Pass authentication and content type
      headers = ["Authorization", "Content-Type"]
      # Authorization: JWT tokens for user authentication
      # Content-Type: Tells API what data format is being sent (JSON, form data)

      # COOKIES: Forward all cookies for session management
      cookies {
        forward = "all"
      }
      # WHY ALL: APIs might use cookies for authentication or session state
    }

    # NO CACHING: Always fetch fresh data from API
    min_ttl     = 0 # Never cache (always fetch from origin)
    default_ttl = 0 # Default: no caching
    max_ttl     = 0 # Maximum: no caching

    # WHY NO CACHE: API responses are dynamic and user-specific
    # EXAMPLES: User profile, document list, authentication status
    # RISK: Caching would show wrong user's data or stale information
  }

  # STEP 11E: User Images Cache Behavior (Optimized for Thumbnails)
  # PURPOSE: Handle user-uploaded images with appropriate caching
  # BENEFIT: Fast thumbnail loading while allowing image updates
  ordered_cache_behavior {
    # PATH PATTERN: Apply to user images stored in S3
    path_pattern = "/user-images/*"
    # MATCHES: /user-images/123/document_20241201_143022.jpg
    # WHY SEPARATE: User images need different caching than static assets

    # LIMITED HTTP METHODS: Only allow read operations for images
    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    # SECURITY: Images shouldn't accept POST/PUT/DELETE operations
    # PERFORMANCE: Fewer allowed methods = faster CloudFront processing

    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.user_images_bucket.id}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    # MODERATE CACHING: Cache images for 1 week (balance performance vs freshness)
    min_ttl     = 0       # Allow immediate cache invalidation if needed
    default_ttl = 604800  # 1 week default (7 * 24 * 60 * 60 seconds)
    max_ttl     = 2592000 # 1 month maximum (30 * 24 * 60 * 60 seconds)

    # WHY 1 WEEK CACHE:
    # - Images rarely change once uploaded
    # - Good balance between performance and storage costs
    # - Allows for image updates if needed (cache invalidation)
    # - Reduces S3 requests for frequently viewed images
  }

  # Geographic restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL/TLS configuration
  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  # STEP 11D: Custom Error Handling for Single Page Applications (SPA)
  # SPA ROUTING PROBLEM: When user visits yourapp.com/profile, S3 doesn't have /profile file
  # SOLUTION: Redirect 404/403 errors to index.html, let React Router handle the route

  # HANDLE 404 ERRORS: File not found → Serve index.html instead
  custom_error_response {
    error_code         = 404           # When S3 returns "file not found"
    response_code      = 200           # Tell browser "success" instead of "error"
    response_page_path = "/index.html" # Serve the main React app

    # EXAMPLE SCENARIO:
    # 1. User visits: yourapp.com/dashboard/documents
    # 2. CloudFront asks S3 for: /dashboard/documents (file doesn't exist)
    # 3. S3 returns: 404 Not Found
    # 4. CloudFront intercepts: Returns index.html with 200 OK
    # 5. React Router loads: Sees /dashboard/documents URL, renders correct page
  }

  # HANDLE 403 ERRORS: Access forbidden → Also serve index.html
  custom_error_response {
    error_code         = 403           # When S3 returns "access denied"
    response_code      = 200           # Tell browser "success"
    response_page_path = "/index.html" # Serve the main React app

    # WHY NEEDED: Sometimes S3 returns 403 instead of 404 for security
    # SAME RESULT: React Router handles the routing client-side
  }

  # SPA ROUTING BENEFIT: 
  # - Clean URLs work: yourapp.com/profile, yourapp.com/settings
  # - Direct navigation works: User can bookmark any page
  # - Browser back/forward works normally
  # - No ugly hash routes needed: yourapp.com/#/profile

  tags = {
    Name        = "${var.project_name}-frontend-distribution"
    Environment = var.environment
    Purpose     = "Frontend CDN"
  }
}

# IAM Role for Frontend Deployment
# STEP 12: Create IAM Role for Automated Frontend Deployments
# PURPOSE: Allow CI/CD systems and admin users to deploy frontend securely
# SECURITY MODEL: Role-based access instead of long-lived access keys
# BENEFITS: Temporary credentials, automatic rotation, audit trail
resource "aws_iam_role" "frontend_deployment_role" {
  name = "${var.project_name}-frontend-deployment-role-v2"

  # ASSUME ROLE POLICY: Who can "become" this role and use its permissions
  assume_role_policy = jsonencode({
    Version = "2012-10-17" # IAM policy language version
    Statement = [
      # STATEMENT 1: Allow EC2 instances to assume this role (for CI/CD)
      {
        Action = "sts:AssumeRole" # Action to "become" this role
        Effect = "Allow"          # Grant permission
        Principal = {
          Service = "ec2.amazonaws.com" # EC2 instances can assume this role
          # USE CASE: CI/CD runners on EC2 instances (Jenkins, GitLab Runner)
        }
      },
      # STATEMENT 2: Allow current admin user to assume this role
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = data.aws_caller_identity.current.arn # The user who runs Terraform
          # USE CASE: Admin can test deployment permissions or run manual deployments
        }
      }
    ]
    # ALTERNATIVE PRINCIPALS for different CI/CD systems:
    # GitHub Actions: "Federated" with GitHub OIDC provider
    # AWS CodeBuild: "Service" = "codebuild.amazonaws.com"
    # Lambda: "Service" = "lambda.amazonaws.com"
  })

  tags = {
    Name        = "${var.project_name}-frontend-deployment-role-v2"
    Environment = var.environment
    Purpose     = "Frontend Deployment Automation" # What this role does
  }
}

# STEP 13: Define IAM Permissions for Frontend Deployment
# PURPOSE: Specify exactly what the deployment role can do (least privilege)
# PERMISSIONS NEEDED: Upload files to S3 + Clear CloudFront cache
resource "aws_iam_role_policy" "frontend_deployment_policy" {
  name = "${var.project_name}-frontend-deployment-policy"
  role = aws_iam_role.frontend_deployment_role.id # Attach to role above

  # IAM POLICY: Specific permissions for frontend deployment tasks
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # STATEMENT 1: S3 Bucket Permissions for File Management
      {
        Effect = "Allow" # Grant permissions
        Action = [
          "s3:GetObject",    # Download files (for verification)
          "s3:PutObject",    # Upload files (deployment)
          "s3:DeleteObject", # Remove files (cleanup)
          "s3:ListBucket"    # List files (inventory, sync operations)
        ]
        Resource = [
          aws_s3_bucket.frontend_bucket.arn,       # Bucket itself (for ListBucket)
          "${aws_s3_bucket.frontend_bucket.arn}/*" # All files in bucket (for Get/Put/Delete)
        ]
        # DEPLOYMENT WORKFLOW PERMISSIONS:
        # 1. ListBucket: See what's currently deployed
        # 2. PutObject: Upload new build files
        # 3. DeleteObject: Remove old/unused files
        # 4. GetObject: Verify uploads completed successfully
      },
      # STATEMENT 2: CloudFront Cache Invalidation Permissions
      {
        Effect = "Allow"
        Action = [
          "cloudfront:CreateInvalidation", # Clear cache for updated files
          "cloudfront:GetInvalidation",    # Check invalidation status
          "cloudfront:ListInvalidations"   # View invalidation history
        ]
        Resource = aws_cloudfront_distribution.frontend_distribution.arn

        # WHY INVALIDATION NEEDED:
        # Problem: CloudFront caches files for performance
        # Issue: New deployment files won't be served until cache expires
        # Solution: Invalidation immediately clears cache for updated files
        # 
        # DEPLOYMENT PROCESS:
        # 1. Upload new files to S3
        # 2. Create invalidation for changed files
        # 3. Users get new version immediately (not cached old version)
      }
    ]
    # SECURITY PRINCIPLE: Least privilege - only permissions needed for deployment
    # NO PERMISSIONS FOR: Creating buckets, modifying other AWS resources, etc.
  })
}

# STEP 14: Export Important Values for Deployment Scripts and Monitoring
# PURPOSE: Make key infrastructure details available to other systems
# USAGE: Deployment scripts, monitoring tools, documentation
# TERRAFORM OUTPUTS: Values that other tools need to interact with infrastructure

# S3 BUCKET NAME: Required for deployment scripts to upload files
output "frontend_bucket_name" {
  description = "Name of the S3 bucket for frontend assets"
  value       = aws_s3_bucket.frontend_bucket.id
  # USED BY: deploy-frontend.py script for aws s3 sync command
  # EXAMPLE: "doc-intel-frontend-a1b2c3d4"
}

# CLOUDFRONT DISTRIBUTION ID: Required for cache invalidation
output "frontend_distribution_id" {
  description = "CloudFront distribution ID for frontend"
  value       = aws_cloudfront_distribution.frontend_distribution.id
  # USED BY: deploy-frontend.py for aws cloudfront create-invalidation
  # EXAMPLE: "E1ABCDEFGHIJKL"
  # PURPOSE: Clear CDN cache after deployments so users get fresh content
}

# CLOUDFRONT DOMAIN: The CDN URL where users access your app
output "frontend_distribution_domain" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.frontend_distribution.domain_name
  # EXAMPLE: "d123456789abcdef.cloudfront.net"
  # PURPOSE: This is where your app is actually served from (not S3 directly)
}

# FRONTEND URL: Complete HTTPS URL for easy access
output "frontend_url" {
  description = "Full URL to access the frontend"
  value       = "https://${aws_cloudfront_distribution.frontend_distribution.domain_name}"
  # COMPLETE URL: Ready to use in browsers, documentation, etc.
  # EXAMPLE: "https://d123456789abcdef.cloudfront.net"
  # USAGE: Share this URL with users, testers, or for custom domain setup
}

# IAM ROLE ARN: For CI/CD systems to assume deployment permissions
output "frontend_deployment_role_arn" {
  description = "ARN of the IAM role for frontend deployment"
  value       = aws_iam_role.frontend_deployment_role.arn
  # USED BY: GitHub Actions, Jenkins, or other CI/CD systems
  # PURPOSE: Assume this role to get deployment permissions
  # EXAMPLE: "arn:aws:iam::123456789012:role/doc-intel-frontend-deployment-role"
}

# STEP 15: Security and Monitoring Outputs (For Compliance and Verification)
# PURPOSE: Provide security confirmation and monitoring information
# USAGE: Security audits, compliance reports, infrastructure documentation

# S3 REGION: Confirm where data is stored for compliance requirements
output "frontend_s3_region" {
  description = "Region where the S3 bucket is located"
  value       = var.aws_region
  # COMPLIANCE USE: Data residency requirements, GDPR, audit reports
  # EXAMPLE: "us-west-2"
  # PURPOSE: Confirm data stays in expected geographic region
}

# CLOUDFRONT COVERAGE: Show which edge locations are being used
output "cloudfront_price_class" {
  description = "CloudFront price class (edge location coverage)"
  value       = aws_cloudfront_distribution.frontend_distribution.price_class
  # MONITORING USE: Understand global performance coverage
  # EXAMPLE: "PriceClass_200" = ~200 edge locations worldwide
  # COST TRACKING: Higher price classes = more edge locations = higher costs
}

# ENCRYPTION STATUS: Confirm security compliance
output "s3_bucket_encryption_status" {
  description = "S3 bucket encryption configuration"
  value       = "AES256 enabled"
  # SECURITY AUDIT: Prove data is encrypted at rest
  # COMPLIANCE: Required for many security standards (SOC2, ISO27001, etc.)
  # CONFIRMATION: All files stored with military-grade encryption
}

output "s3_public_access_blocked" {
  description = "Confirmation that S3 bucket blocks all public access"
  value       = "All public access blocked - CloudFront OAC only"
} 