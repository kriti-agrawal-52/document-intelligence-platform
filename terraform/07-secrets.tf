# /terraform/07-secrets.tf
#
# FILE PURPOSE:
# This file is dedicated to managing application secrets using AWS Secrets Manager.
# It is a critical security best practice to NEVER hardcode sensitive information like
# database passwords or API keys directly in your code. This file creates "secrets" in
# a secure, managed vault. Our application and other Terraform files can then reference
# these secrets by name, without ever exposing the actual secret values in the codebase.

# --- RDS Database Credentials Secret ---
# This `aws_secretsmanager_secret` resource creates a new secret container in Secrets Manager.
resource "aws_secretsmanager_secret" "rds_secret" {
  # `name` is the unique path-like identifier for the secret.
  name = "doc-intel/rds-credentials"
  # *** FIX: Set recovery window to 0 to allow immediate deletion. ***
  # This disables the default 7-30 day recovery period.
  recovery_window_in_days = 0
}

# This `aws_secretsmanager_secret_version` resource populates the secret container with a value.
resource "aws_secretsmanager_secret_version" "rds_creds" {
  # `secret_id` links this version to the secret container created above.
  secret_id = aws_secretsmanager_secret.rds_secret.id
  # `secret_string` holds the actual sensitive value. We are storing it as a JSON
  # string because it contains multiple related values (username and password).
  
  secret_string = jsonencode({
    username = "rdsdatabaseadmin"
    password = "PM1xlPCkRgZwploysH0i"
  })
}

# --- DocumentDB Credentials Secret ---
# We follow the same pattern to create a separate secret for our DocumentDB credentials.
resource "aws_secretsmanager_secret" "docdb_secret" {
  name = "doc-intel/docdb-credentials"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "docdb_creds" {
  secret_id = aws_secretsmanager_secret.docdb_secret.id
  secret_string = jsonencode({
    username = "mongodatabaseadmin"
    password = "FJ2rCNv7lo5vFfQ1Y4hzOK"
  })
}

# --- JWT Secret Key ---
# This secret stores the key used to sign the JSON Web Tokens for authentication.
resource "aws_secretsmanager_secret" "jwt_key_secret" {
  name = "doc-intel/jwt-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "jwt_key" {
  secret_id     = aws_secretsmanager_secret.jwt_key_secret.id
  secret_string = var.jwt_secret_key
}

# --- OpenAI API Key ---
# This secret stores the API key for the external OpenAI service.
resource "aws_secretsmanager_secret" "openai_key_secret" {
  name = "doc-intel/openai-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "openai_key" {
  secret_id     = aws_secretsmanager_secret.openai_key_secret.id
  secret_string = var.openai_api_key
}
