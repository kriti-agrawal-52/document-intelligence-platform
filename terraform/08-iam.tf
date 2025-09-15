# /terraform/08-iam.tf
#
# FILE PURPOSE:
# This file defines all the necessary Identity and Access Management (IAM) permissions.
# IAM controls who (users, services) can do what (actions) on which resources.
# Following the principle of least privilege is crucial for security. This file creates
# specific roles and policies that grant our services just enough permission to do their
# jobs, and no more.

# --- IAM Role for AWS Load Balancer Controller ---
# The AWS Load Balancer Controller is a pod running in our cluster that needs permission
# to manage AWS Application Load Balancers (ALBs) on our behalf. We use a secure method
# called "IAM Roles for Service Accounts" (IRSA) to grant these permissions.
module "iam_assumable_role_for_alb" {
  # This module creates an IAM role that can be assumed by a Kubernetes service account.
  source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role-with-oidc"
  version = "5.39.0"

  create_role = true
  role_name   = "aws-load-balancer-controller-role"
  # `provider_url` is the OIDC provider URL of our EKS cluster. This is how the role
  # establishes a trust relationship with the cluster. We get this URL from our EKS module output.
  provider_url = replace(module.eks.cluster_oidc_issuer_url, "https://", "")
  # `role_policy_arns` attaches the necessary permissions policy to the role.
  role_policy_arns = [aws_iam_policy.aws_load_balancer_controller.arn]
  # `oidc_fully_qualified_subjects` specifies exactly which Kubernetes service account
  # is allowed to assume this role. This locks it down to the `aws-load-balancer-controller`
  # service account running in the `kube-system` namespace.
  oidc_fully_qualified_subjects = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
}

# This `aws_iam_policy` resource contains the specific permissions the controller needs.
# This is the complete policy from AWS documentation for the Load Balancer Controller.
resource "aws_iam_policy" "aws_load_balancer_controller" {
  name        = "AWSLoadBalancerControllerIAMPolicy"
  description = "Policy for the AWS Load Balancer Controller"
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "iam:CreateServiceLinkedRole"
        ],
        Resource = "*",
        Condition = {
          StringEquals = {
            "iam:AWSServiceName" = "elasticloadbalancing.amazonaws.com"
          }
        }
      },
      {
        Effect = "Allow",
        Action = [
          "ec2:DescribeAccountAttributes",
          "ec2:DescribeAddresses",
          "ec2:DescribeAvailabilityZones",
          "ec2:DescribeInternetGateways",
          "ec2:DescribeVpcs",
          "ec2:DescribeVpcPeeringConnections",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeInstances",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeTags",
          "ec2:GetCoipPoolUsage",
          "ec2:GetIpamPoolCidrs",
          "ec2:DescribeCoipPools",
          "elasticloadbalancing:DescribeLoadBalancers",
          "elasticloadbalancing:DescribeLoadBalancerAttributes",
          "elasticloadbalancing:DescribeListeners",
          "elasticloadbalancing:DescribeListenerCertificates",
          "elasticloadbalancing:DescribeSSLPolicies",
          "elasticloadbalancing:DescribeRules",
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:DescribeTargetGroupAttributes",
          "elasticloadbalancing:DescribeTargetHealth",
          "elasticloadbalancing:DescribeTags"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "cognito-idp:DescribeUserPoolClient",
          "acm:ListCertificates",
          "acm:DescribeCertificate",
          "iam:ListServerCertificates",
          "iam:GetServerCertificate",
          "waf-regional:GetWebACL",
          "waf-regional:GetWebACLForResource",
          "waf-regional:AssociateWebACL",
          "waf-regional:DisassociateWebACL",
          "wafv2:GetWebACL",
          "wafv2:GetWebACLForResource",
          "wafv2:AssociateWebACL",
          "wafv2:DisassociateWebACL",
          "shield:DescribeProtection",
          "shield:GetSubscriptionState",
          "shield:DescribeSubscription",
          "shield:CreateProtection",
          "shield:DeleteProtection"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "ec2:CreateSecurityGroup"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "ec2:CreateTags"
        ],
        Resource = "arn:aws:ec2:*:*:security-group/*",
        Condition = {
          StringEquals = {
            "ec2:CreateAction" = "CreateSecurityGroup"
          },
          Null = {
            "aws:RequestedRegion" = "false"
          }
        }
      },
      {
        Effect = "Allow",
        Action = [
          "elasticloadbalancing:CreateLoadBalancer",
          "elasticloadbalancing:CreateTargetGroup"
        ],
        Resource = "*",
        Condition = {
          Null = {
            "aws:RequestedRegion" = "false"
          }
        }
      },
      {
        Effect = "Allow",
        Action = [
          "elasticloadbalancing:CreateListener",
          "elasticloadbalancing:DeleteListener",
          "elasticloadbalancing:CreateRule",
          "elasticloadbalancing:DeleteRule"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "elasticloadbalancing:AddTags",
          "elasticloadbalancing:RemoveTags"
        ],
        Resource = [
          "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
          "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
          "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*",
          "arn:aws:elasticloadbalancing:*:*:listener/app/*/*",
          "arn:aws:elasticloadbalancing:*:*:listener/net/*/*",
          "arn:aws:elasticloadbalancing:*:*:listener-rule/app/*/*",
          "arn:aws:elasticloadbalancing:*:*:listener-rule/net/*/*"
        ],
        Condition = {
          Null = {
            "aws:RequestedRegion" = "false"
          }
        }
      },
      {
        Effect = "Allow",
        Action = [
          "elasticloadbalancing:RegisterTargets",
          "elasticloadbalancing:DeregisterTargets"
        ],
        Resource = "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*"
      },
      {
        Effect = "Allow",
        Action = [
          "elasticloadbalancing:SetWebAcl",
          "elasticloadbalancing:ModifyListener",
          "elasticloadbalancing:AddListenerCertificates",
          "elasticloadbalancing:RemoveListenerCertificates",
          "elasticloadbalancing:ModifyRule"
        ],
        Resource = "*"
      }
    ]
  })
}

# --- IAM Policy for SQS Access ---
# This policy grants our worker nodes permission to interact with our SQS queue.
data "aws_iam_policy_document" "sqs_policy_doc" {
  statement {
    # These are the specific actions our services need: Send messages (producer),
    # and Receive/Delete messages (consumer).
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:SendMessage"
    ]
    # This `resources` block restricts the permissions to ONLY our specific SQS queue
    # and its Dead-Letter Queue (DLQ), following the principle of least privilege.
    resources = [
      aws_sqs_queue.summarization_queue.arn,
      aws_sqs_queue.summarization_dlq.arn
    ]
  }
}

resource "aws_iam_policy" "sqs_policy" {
  name   = "EKS-SQS-Summarization-Policy"
  policy = data.aws_iam_policy_document.sqs_policy_doc.json
}

# This `aws_iam_role_policy_attachment` resource attaches the SQS policy we just defined
# to the IAM role used by our EKS worker nodes. This is a simpler approach for this project.
# In a more advanced setup, we would create a separate role for each service and use IRSA
# for SQS access as well.
resource "aws_iam_role_policy_attachment" "sqs_attachment" {
  # `module.eks.eks_managed_node_groups["main"].iam_role_name` gets the name of the IAM role
  # automatically created for our node group by the EKS module.
  role       = module.eks.eks_managed_node_groups["main"].iam_role_name
  policy_arn = aws_iam_policy.sqs_policy.arn
}

# --- IAM Policy for Text Extraction Service S3 Access ---
# This policy grants the text extraction service permission to upload user images to S3.
# The service needs to store uploaded images securely and retrieve them for processing.
data "aws_iam_policy_document" "text_extraction_s3_policy_doc" {
  statement {
    # These are the specific actions needed for image upload and management:
    # - PutObject: Upload new images to S3
    # - GetObject: Retrieve images for processing (if needed)
    # - DeleteObject: Remove images if user deletes document
    # - ListBucket: List images for user (if needed)
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    # Restrict permissions to ONLY our user images bucket
    resources = [
      aws_s3_bucket.user_images_bucket.arn,
      "${aws_s3_bucket.user_images_bucket.arn}/*"
    ]
  }
}

resource "aws_iam_policy" "text_extraction_s3_policy" {
  name        = "TextExtractionService-S3-UserImages-Policy"
  description = "Policy for text extraction service to access user images S3 bucket"
  policy      = data.aws_iam_policy_document.text_extraction_s3_policy_doc.json
}

# Attach the S3 policy to the EKS worker nodes role
# This allows the text extraction service pods to upload images to S3
resource "aws_iam_role_policy_attachment" "text_extraction_s3_attachment" {
  role       = module.eks.eks_managed_node_groups["main"].iam_role_name
  policy_arn = aws_iam_policy.text_extraction_s3_policy.arn
}