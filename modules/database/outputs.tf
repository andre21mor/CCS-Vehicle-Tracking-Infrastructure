output "dynamodb_tables" {
  description = "Nombres de las tablas DynamoDB creadas"
  value = {
    vehicles                 = aws_dynamodb_table.vehicles.name
    users                   = aws_dynamodb_table.users.name
    drivers                 = aws_dynamodb_table.drivers.name
    routes                  = aws_dynamodb_table.routes.name
    trips                   = aws_dynamodb_table.trips.name
    alerts                  = aws_dynamodb_table.alerts.name
    notification_preferences = aws_dynamodb_table.notification_preferences.name
  }
}

output "dynamodb_table_arns" {
  description = "ARNs de las tablas DynamoDB"
  value = {
    vehicles                 = aws_dynamodb_table.vehicles.arn
    users                   = aws_dynamodb_table.users.arn
    drivers                 = aws_dynamodb_table.drivers.arn
    routes                  = aws_dynamodb_table.routes.arn
    trips                   = aws_dynamodb_table.trips.arn
    alerts                  = aws_dynamodb_table.alerts.arn
    notification_preferences = aws_dynamodb_table.notification_preferences.arn
  }
}

output "redis_endpoint" {
  description = "Endpoint del cluster Redis"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_port" {
  description = "Puerto del cluster Redis"
  value       = aws_elasticache_replication_group.main.port
}

output "rds_cluster_endpoint" {
  description = "Endpoint del cluster RDS Aurora (si está habilitado)"
  value       = var.enable_rds ? aws_rds_cluster.main[0].endpoint : null
}

output "rds_cluster_reader_endpoint" {
  description = "Endpoint de lectura del cluster RDS Aurora (si está habilitado)"
  value       = var.enable_rds ? aws_rds_cluster.main[0].reader_endpoint : null
}

output "database_backups_bucket" {
  description = "Bucket S3 para backups de base de datos"
  value       = aws_s3_bucket.database_backups.bucket
}

output "database_connection_info" {
  description = "Información de conexión a las bases de datos"
  value = {
    dynamodb_region = data.aws_region.current.name
    redis_endpoint  = aws_elasticache_replication_group.main.primary_endpoint_address
    redis_port      = aws_elasticache_replication_group.main.port
    rds_endpoint    = var.enable_rds ? aws_rds_cluster.main[0].endpoint : null
    rds_database    = var.enable_rds ? aws_rds_cluster.main[0].database_name : null
  }
  sensitive = true
}

# Data sources
data "aws_region" "current" {}
