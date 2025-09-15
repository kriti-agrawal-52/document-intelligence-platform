# /terraform/05-databases.tf

# FILE PURPOSE
# This file provisions all of the stateful databases required by the microservices
# It creates a relational database (AWS RDS for MySQL) for the auth-service and a 
# NoSQL document database (AWS DocumentDB) for the text-extraction-service.
# It also sets up the necessary security groups to ensure that only our EKS cluster nodes can communicate with these databases,
# following the principle of least privilege.

# --- Security Group for Database Access ---
resource "aws_security_group" "db_access_sg" {
    name = "db-access-from-eks"
    description = "Allow inbound traffic from EKS nodes to databases"
    # It must be created within our VPC.
    vpc_id      = module.vpc.vpc_id

    # the ingress block defines the inbound rule
    ingress {
        description = "Allow MySQL from EKS nodes."
        from_port = 3306 # the default mysql port
        to_port = 3306
        protocol = "tcp"
        # it only allows traffic from resources that have the EKS node's security group attached.
        security_groups = [module.eks.node_security_group_id]
    }
    # A similar rule is defined for DocumentDB on its default port.
    ingress {
        description     = "Allow DocumentDB from EKS Nodes"
        from_port       = 27017 # The default MongoDB/DocumentDB port
        to_port         = 27017
        protocol        = "tcp"
        security_groups = [module.eks.node_security_group_id]
    }
    tags = {Name = "db-access-sg"}
}

# --- RDS MySQL Database for Auth Service ---
# A `db_subnet_group` tells RDS which subnets it is allowed to place the database instance in.
# We must use our private subnets to keep the database secure.
resource "aws_db_subnet_group" "rds_subnet_group" {
    name = "rds-subnet-group"
    subnet_ids = module.vpc.private_subnets
    tags = {Name = " RDS Subnet Group"}
}

# This `aws_db_instance` resource provisions the actual MySQL database.
resource "aws_db_instance" "mysql_db" {
    identifier = "auth-db"
    engine = "mysql"
    engine_version = "8.0"
    instance_class       = "db.t3.micro" # A small, cost-effective instance type for this project
    allocated_storage    = 20
    storage_type         = "gp2"
    # The username and password are securely retrieved from AWS Secrets Manager.
    # We use `jsondecode` to parse the secret string which is stored in JSON format.
    username             = jsondecode(aws_secretsmanager_secret_version.rds_creds.secret_string)["username"]
    password             = jsondecode(aws_secretsmanager_secret_version.rds_creds.secret_string)["password"]
    db_subnet_group_name = aws_db_subnet_group.rds_subnet_group.name
    # We attach the security group we created earlier to enforce our access rules.
    vpc_security_group_ids = [aws_security_group.db_access_sg.id]
    # For a practice project, we skip creating a final snapshot on deletion to avoid costs.
    skip_final_snapshot  = true
    # This ensures the database is not accessible from the public internet.
    publicly_accessible  = false
}

# --- DocumentDB Cluster for Text Extraction Service ---
# DocumentDB also requires a subnet group, similar to RDS.
resource "aws_docdb_subnet_group" "docdb_subnet_group" {
    name       = "docdb-subnet-group"
    subnet_ids = module.vpc.private_subnets
    tags = { Name = "DocDB Subnet Group" }
}

# This `aws_docdb_cluster` resource provisions the DocumentDB cluster's control plane.
resource "aws_docdb_cluster" "docdb" {
    cluster_identifier      = "doc-intel-db"
    engine                  = "docdb"
    engine_version          = "4.0.0"
    # Credentials are also securely fetched from AWS Secrets Manager.
    master_username         = jsondecode(aws_secretsmanager_secret_version.docdb_creds.secret_string)["username"]
    master_password         = jsondecode(aws_secretsmanager_secret_version.docdb_creds.secret_string)["password"]
    db_subnet_group_name    = aws_docdb_subnet_group.docdb_subnet_group.name
    vpc_security_group_ids  = [aws_security_group.db_access_sg.id]
    skip_final_snapshot     = true
    backup_retention_period = 5 # Keep backups for 5 days
}

# This `aws_docdb_cluster_instance` resource provisions the actual instances for the cluster.
resource "aws_docdb_cluster_instance" "docdb_instances" {
    # `count = 3` creates three instances (1 primary, 2 replicas) for high availability.
    count              = 3
    identifier         = "doc-intel-db-instance-${count.index}"
    cluster_identifier = aws_docdb_cluster.docdb.id
    instance_class     = "db.t3.medium"
    engine             = aws_docdb_cluster.docdb.engine
}