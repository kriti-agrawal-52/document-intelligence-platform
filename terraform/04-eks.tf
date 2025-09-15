# /terraform/04-eks.tf
#
# FILE PURPOSE:
# This file is responsible for provisioning the Amazon Elastic Kubernetes Service (EKS) cluster.
# EKS is a managed Kubernetes service that simplifies running containerized applications.
# This file defines the Kubernetes control plane (managed by AWS) and the worker nodes
# (EC2 instances) where our application pods will actually run. We use the official EKS
# module from the Terraform Registry to handle the complexity of setting up a best-practice cluster.

# --- EKS Module ---
# We use the official "terraform-aws-modules/eks/aws" module to create and configure our cluster.
# This module abstracts away hundreds of lines of code and ensures the cluster is set up
# securely and correctly.
module "eks" {
  # `source` points to the EKS module in the Terraform Registry.
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.37" # Update to a newer version that supports auth management

  # --- Cluster Configuration ---
  # These arguments configure the EKS control plane itself.

  # `cluster_name` is the unique name for our EKS cluster.
  cluster_name = "document-intelligence"
  # `cluster_version` specifies the version of Kubernetes to run. It's important to use
  # a supported version.
  cluster_version = "1.29"

  # `vpc_id` and `subnet_ids` associate the EKS cluster with our networking infrastructure
  # created in `03-vpc.tf`. The cluster's control plane and worker nodes will be placed
  # within this VPC and its private subnets.
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # This configuration ensures the EKS API server is only accessible via its public
  # endpoint. This resolves common DNS issues where `kubectl` from an external
  # network might incorrectly resolve to the private IP.
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = false

  # --- Node Group Configuration ---
  # This block defines the group of EC2 instances (worker nodes) that will join the cluster.

  # `eks_managed_node_groups` defines a node group that is managed by AWS, which simplifies
  # updates and maintenance. We are creating one node group named "main".
  eks_managed_node_groups = {
    main = {
      # `name` for the node group.
      name = "main-node-group"
      # `instance_types` specifies the type of EC2 instances to use for the worker nodes.
      # "t3.medium" is cost-effective for practice/learning environments.
      instance_types = ["t3.medium"]
      # `min_size`, `max_size`, and `desired_size` configure the autoscaling for the node group.
      # This allows the number of worker nodes to scale up or down based on the cluster's needs.
      min_size     = 1
      max_size     = 3
      desired_size = 2
    }
  }

  # `tags` are applied to all resources created by the EKS module, which is essential
  # for cost allocation and resource management.
  tags = {
    Terraform   = "true"
    Environment = "production"
    Project     = "doc-intel-app"
  }
}