# /terraform/10-redis.tf

# --- ElastiCache for Redis ---

resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "redis-subnet-group-v2"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "Redis Subnet Group"
  }
}

resource "aws_security_group" "redis_access_sg" {
  name        = "redis-access-from-eks"
  description = "Allow inbound traffic from EKS nodes to Redis"
  vpc_id      = module.vpc.vpc_id

  # Ingress from EKS node security group on Redis port
  ingress {
    description     = "Allow Redis from EKS Nodes"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  tags = {
    Name = "redis-access-sg"
  }
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "doc-intel-cache"
  engine               = "redis"
  node_type            = "cache.t3.small"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis_subnet_group.name
  security_group_ids   = [aws_security_group.redis_access_sg.id]
  apply_immediately    = true
}

