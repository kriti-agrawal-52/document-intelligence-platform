# terraform/01-main.terraform

# FILE PURPOSE:
# This file is the primary entry point for terraform. It: 
# - configures the cloud provider we are using/interacting with (in this case AWS)
# - Set version constraints for both terraform and the provider plugins to ensure that the code runs predictably and does not break with future updates.
# It does not define any specific resources such as servers or databases, but it sets up the foundational connection and requirements of all other .tf files in the project.

# -- Terraform configuration block -- 
# This block is used to configure Terraform's own behavior.
terraform {
    # `required_version` specifies the minimum version of the Terraform CLI that can be
    # used with this code. This prevents accidental use of an older, incompatible version
    # that might not support the features or syntax used in these files.
    required_version = ">= 1.0"
   
    # `required_providers` is a nested block that declares all the cloud providers
    # this project depends on. For each provider, we specify its source and version.
    required_providers {
        # `source` tells Terraform where to download the provider plugin from.
        # "hashicorp/aws" is the official AWS provider maintained by HashiCorp.
        aws = {
            source = "hashicorp/aws"
            version = "~> 5.0"
        }
        # Random provider for generating unique identifiers
        random = {
            source  = "hashicorp/random"
            version = "~> 3.0"
        }
        # --- ADDED: Kubernetes Provider ---
        # This provider allows Terraform to interact with the Kubernetes API to manage
        # resources like ConfigMaps, Deployments, etc.
        kubernetes = {
        source  = "hashicorp/kubernetes"
        version = "~> 2.0"
    }
        # --- ADDED: Helm Provider ---
        # This provider allows Terraform to install Helm charts in the Kubernetes cluster
        helm = {
            source  = "hashicorp/helm"
            version = "~> 2.0"
        }
    }
}
# --- Provider Configuration Block ---
# This block configures the specifics for a declared provider, in this case, "aws".
# You can have multiple provider blocks if you are managing resources across different accounts or regions.
provider "aws" {
    # The `region` argument tells the AWS provider which geographical region to create
    # all the resources in. All resources defined in this project (unless explicitly
    # overridden) will be created in the region specified by this variable.
    # We are using a variable `var.aws_region` to make this configurable without
    # hardcoding the value here. The actual value is defined in '02-variables.tf'.
    region = var.aws_region
}

# Data source to get AWS account information
data "aws_caller_identity" "current" {}
