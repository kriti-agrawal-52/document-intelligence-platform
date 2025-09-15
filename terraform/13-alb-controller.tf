# /terraform/13-alb-controller.tf
#
# FILE PURPOSE:
# This file provisions the AWS Load Balancer Controller in the EKS cluster.
# The ALB Controller is required for Kubernetes Ingress resources to create
# Application Load Balancers (ALBs) in AWS. Without this controller, the
# ingress resources will not provision any actual load balancers.

# --- Helm Provider Configuration ---
# The Helm provider is configured in 01-main.tf as a required provider.
# We configure it here to use our EKS cluster for authentication.
provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# --- AWS Load Balancer Controller Helm Chart ---
resource "helm_release" "aws_load_balancer_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.7.2"

  # Wait for the EKS cluster to be ready before installing
  depends_on = [
    module.eks,
    module.iam_assumable_role_for_alb
  ]

  set {
    name  = "clusterName"
    value = module.eks.cluster_name
  }

  set {
    name  = "serviceAccount.create"
    value = "true"
  }

  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = module.iam_assumable_role_for_alb.iam_role_arn
  }

  set {
    name  = "region"
    value = var.aws_region
  }

  set {
    name  = "vpcId"
    value = module.vpc.vpc_id
  }

  # Disable webhook certificate provisioning as it's not needed for basic ALB functionality
  set {
    name  = "enableCertManager"
    value = "false"
  }
}

 