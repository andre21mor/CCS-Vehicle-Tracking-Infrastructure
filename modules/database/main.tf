# Base de datos y almacenamiento para la plataforma vehicular

# DynamoDB Table para información de vehículos
resource "aws_dynamodb_table" "vehicles" {
  name           = "${var.project_name}-${var.environment}-vehicles"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "vehicle_id"

  attribute {
    name = "vehicle_id"
    type = "S"
  }

  attribute {
    name = "owner_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  # GSI para consultar vehículos por propietario
  global_secondary_index {
    name     = "OwnerIndex"
    hash_key = "owner_id"
    range_key = "status"
    projection_type = "ALL"
  }

  # GSI para consultar por estado
  global_secondary_index {
    name     = "StatusIndex"
    hash_key = "status"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-vehicles"
    Environment = var.environment
  }
}

# DynamoDB Table para usuarios y clientes
resource "aws_dynamodb_table" "users" {
  name           = "${var.project_name}-${var.environment}-users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  attribute {
    name = "company_id"
    type = "S"
  }

  # GSI para consultar por email
  global_secondary_index {
    name     = "EmailIndex"
    hash_key = "email"
    projection_type = "ALL"
  }

  # GSI para consultar por empresa
  global_secondary_index {
    name     = "CompanyIndex"
    hash_key = "company_id"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-users"
    Environment = var.environment
  }
}

# DynamoDB Table para conductores
resource "aws_dynamodb_table" "drivers" {
  name           = "${var.project_name}-${var.environment}-drivers"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "driver_id"

  attribute {
    name = "driver_id"
    type = "S"
  }

  attribute {
    name = "license_number"
    type = "S"
  }

  attribute {
    name = "company_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  # GSI para consultar por licencia
  global_secondary_index {
    name     = "LicenseIndex"
    hash_key = "license_number"
    projection_type = "ALL"
  }

  # GSI para consultar por empresa
  global_secondary_index {
    name     = "CompanyIndex"
    hash_key = "company_id"
    range_key = "status"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-drivers"
    Environment = var.environment
  }
}

# DynamoDB Table para rutas
resource "aws_dynamodb_table" "routes" {
  name           = "${var.project_name}-${var.environment}-routes"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "route_id"

  attribute {
    name = "route_id"
    type = "S"
  }

  attribute {
    name = "company_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  # GSI para consultar rutas por empresa
  global_secondary_index {
    name     = "CompanyIndex"
    hash_key = "company_id"
    range_key = "status"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-routes"
    Environment = var.environment
  }
}

# DynamoDB Table para viajes/trips
resource "aws_dynamodb_table" "trips" {
  name           = "${var.project_name}-${var.environment}-trips"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "trip_id"

  attribute {
    name = "trip_id"
    type = "S"
  }

  attribute {
    name = "vehicle_id"
    type = "S"
  }

  attribute {
    name = "driver_id"
    type = "S"
  }

  attribute {
    name = "start_time"
    type = "N"
  }

  attribute {
    name = "status"
    type = "S"
  }

  # GSI para consultar viajes por vehículo
  global_secondary_index {
    name     = "VehicleIndex"
    hash_key = "vehicle_id"
    range_key = "start_time"
    projection_type = "ALL"
  }

  # GSI para consultar viajes por conductor
  global_secondary_index {
    name     = "DriverIndex"
    hash_key = "driver_id"
    range_key = "start_time"
    projection_type = "ALL"
  }

  # GSI para consultar por estado
  global_secondary_index {
    name     = "StatusIndex"
    hash_key = "status"
    range_key = "start_time"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-trips"
    Environment = var.environment
  }
}

# DynamoDB Table para alertas y notificaciones
resource "aws_dynamodb_table" "alerts" {
  name           = "${var.project_name}-${var.environment}-alerts"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "alert_id"

  attribute {
    name = "alert_id"
    type = "S"
  }

  attribute {
    name = "vehicle_id"
    type = "S"
  }

  attribute {
    name = "alert_type"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  attribute {
    name = "severity"
    type = "S"
  }

  # GSI para consultar alertas por vehículo
  global_secondary_index {
    name     = "VehicleIndex"
    hash_key = "vehicle_id"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  # GSI para consultar por tipo de alerta
  global_secondary_index {
    name     = "TypeIndex"
    hash_key = "alert_type"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  # GSI para consultar por severidad
  global_secondary_index {
    name     = "SeverityIndex"
    hash_key = "severity"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  # TTL para alertas antiguas (90 días)
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-alerts"
    Environment = var.environment
  }
}

# DynamoDB Table para configuración de notificaciones
resource "aws_dynamodb_table" "notification_preferences" {
  name           = "${var.project_name}-${var.environment}-notification-preferences"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-notification-preferences"
    Environment = var.environment
  }
}

# RDS Aurora Serverless para datos transaccionales (opcional)
resource "aws_rds_cluster" "main" {
  count = var.enable_rds ? 1 : 0

  cluster_identifier      = "${var.project_name}-${var.environment}-cluster"
  engine                 = "aurora-mysql"
  engine_mode            = "serverless"
  engine_version         = "5.7.mysql_aurora.2.10.1"
  database_name          = replace("${var.project_name}_${var.environment}", "-", "_")
  master_username        = "admin"
  master_password        = random_password.rds_password[0].result
  backup_retention_period = 7
  preferred_backup_window = "07:00-09:00"
  
  db_subnet_group_name   = var.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.rds[0].id]
  
  scaling_configuration {
    auto_pause               = true
    max_capacity            = 2
    min_capacity            = 1
    seconds_until_auto_pause = 300
  }

  skip_final_snapshot = true
  deletion_protection = false

  tags = {
    Name        = "${var.project_name}-${var.environment}-aurora-cluster"
    Environment = var.environment
  }
}

# Password para RDS
resource "random_password" "rds_password" {
  count = var.enable_rds ? 1 : 0

  length  = 16
  special = true
}

# Security Group para RDS
resource "aws_security_group" "rds" {
  count = var.enable_rds ? 1 : 0

  name_prefix = "${var.project_name}-${var.environment}-rds-"
  vpc_id      = var.vpc_id

  ingress {
    description = "MySQL/Aurora"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.main.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-sg"
    Environment = var.environment
  }
}

# ElastiCache Redis para cache
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-cache-subnet"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id         = "${var.project_name}-${var.environment}-redis"
  description                  = "Redis cluster para cache de aplicación"
  
  node_type                   = "cache.t3.micro"
  port                        = 6379
  parameter_group_name        = "default.redis7"
  
  num_cache_clusters          = 2
  automatic_failover_enabled  = true
  multi_az_enabled           = true
  
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-redis"
    Environment = var.environment
  }
}

# Security Group para Redis
resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-${var.environment}-redis-"
  vpc_id      = var.vpc_id

  ingress {
    description = "Redis"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.main.cidr_block]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-redis-sg"
    Environment = var.environment
  }
}

# S3 Bucket para backups de base de datos
resource "aws_s3_bucket" "database_backups" {
  bucket = "${var.project_name}-${var.environment}-db-backups-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-backups"
    Environment = var.environment
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_versioning" "database_backups_versioning" {
  bucket = aws_s3_bucket.database_backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "database_backups_encryption" {
  bucket = aws_s3_bucket.database_backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle policy para backups
resource "aws_s3_bucket_lifecycle_configuration" "database_backups_lifecycle" {
  bucket = aws_s3_bucket.database_backups.id

  rule {
    id     = "backup_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Data sources
data "aws_vpc" "main" {
  id = var.vpc_id
}
