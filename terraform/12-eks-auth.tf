# /terraform/12-eks-auth.tf
#
# FILE PURPOSE:
# This file manages EKS cluster access using the modern Access Entries approach
# instead of the deprecated aws-auth ConfigMap method.

# --- Data source to get EKS cluster authentication token ---
data "aws_eks_cluster_auth" "this" {
  name = module.eks.cluster_name
}

# --- Kubernetes Provider Configuration ---
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.this.token
}

# --- Add IAM User as EKS Access Entry ---
# This is the modern approach recommended by AWS instead of aws-auth ConfigMap
resource "aws_eks_access_entry" "admin_user" {
  cluster_name  = module.eks.cluster_name
  principal_arn = "arn:aws:iam::911197154219:user/admin"
  type          = "STANDARD"

  depends_on = [module.eks]
}

# --- Add IAM User Access Policy ---
resource "aws_eks_access_policy_association" "admin_user_policy" {
  cluster_name  = module.eks.cluster_name
  principal_arn = "arn:aws:iam::911197154219:user/admin"
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.admin_user]
}