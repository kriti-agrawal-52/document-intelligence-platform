# /terraform/03-vpc.tf

# FILE PURPOSE
# This file is responsible for creating VPC in AWS.
# Within this VPC, it creates subnets, gateways, routing tables that control how our resources communicate with each other and with the internet.

# -- VPC Module --
# A "module" in Terraform is a reusable package of Terraform configurations. Instead of
# defining every single VPC resource manually (VPC, subnets, route tables, internet
# gateway, NAT gateway), we use the official, well-tested VPC module from the
# Terraform Registry. This saves a lot of code and reduces the chance of misconfiguration.
module "vpc" {
  # `source` specifies the location of the module. Here, we are using the official
  # VPC module provided by the "terraform-aws-modules" community.
  source = "terraform-aws-modules/vpc/aws"
  # `version` locks the module to a specific version to prevent unexpected changes.
  version = "5.5.3"

  # --- Module Configuration Arguments ---
  # These are the inputs we provide to the VPC module to customize it for our needs.

  # name sets the vpc name
  name = "practice-vpc"
  # cidr sets the primary IP address range for the vpc using the defined variable from 02-variables.tf
  cidr = var.vpc_cidr
  # azs is the list of availability zones where subnets should be created 
  azs = var.availability_zones

  # `private_subnets` defines the IP ranges for our private subnets. Resources in these
  # subnets (like our EKS nodes and databases) are not directly accessible from the internet.
  # The `cidrsubnet` function is used to calculate subnet ranges based on the main VPC CIDR.
  private_subnets = [for k, v in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, k)]
  # `public_subnets` defines the IP ranges for our public subnets. Resources here (like
  # our Load Balancer and NAT Gateway) need a direct connection to the internet.
  public_subnets = [for k, v in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, k + 8)]

  # `enable_nat_gateway` creates a NAT Gateway. This is essential for resources in the
  # private subnets to be able to initiate outbound connections to the internet (e.g., to
  # pull Docker images or call the OpenAI API), without allowing the internet to initiate
  # connections back to them.
  enable_nat_gateway = true

  # `single_nat_gateway` creates only one NAT Gateway and shares it across all private
  # subnets. This is a cost-saving measure suitable for development/practice environments.
  single_nat_gateway = true

  # `enable_dns_hostnames` is required for certain AWS services, including EKS, to work correctly.
  enable_dns_hostnames = true

  # --- ALB Subnet Tags ---
  # These tags are required for AWS Load Balancer Controller to discover subnets
  # for ALB placement. The controller looks for these specific tags to determine
  # which subnets to use for internet-facing vs internal load balancers.

  # Tags for public subnets (internet-facing ALBs)
  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }

  # Tags for private subnets (internal ALBs)  
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }

  # `tags` are key-value pairs that we attach to all resources created by this module.
  # Tags are crucial for organization, cost tracking, and automation.
  tags = {
    Terraform                                   = "true"
    Environment                                 = "production"
    Project                                     = "doc-intel-app"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}