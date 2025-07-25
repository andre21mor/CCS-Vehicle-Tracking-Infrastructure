# AWS IoT Core - Componente Central para Seguimiento Vehicular

# IoT Policy para vehículos
resource "aws_iot_policy" "vehicle_policy" {
  name = "${var.project_name}-${var.environment}-vehicle-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "iot:Connect"
        ]
        Resource = "arn:aws:iot:${data.aws_region.current.name}:${var.account_id}:client/vehicle-*"
      },
      {
        Effect = "Allow"
        Action = [
          "iot:Publish"
        ]
        Resource = [
          "arn:aws:iot:${data.aws_region.current.name}:${var.account_id}:topic/vehicles/+/telemetry",
          "arn:aws:iot:${data.aws_region.current.name}:${var.account_id}:topic/vehicles/+/video",
          "arn:aws:iot:${data.aws_region.current.name}:${var.account_id}:topic/vehicles/+/panic",
          "arn:aws:iot:${data.aws_region.current.name}:${var.account_id}:topic/vehicles/+/diagnostics"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iot:Subscribe",
          "iot:Receive"
        ]
        Resource = [
          "arn:aws:iot:${data.aws_region.current.name}:${var.account_id}:topicfilter/vehicles/+/commands",
          "arn:aws:iot:${data.aws_region.current.name}:${var.account_id}:topic/vehicles/+/commands"
        ]
      }
    ]
  })
}

# IoT Topic Rules para procesamiento de datos

# Rule para telemetría de vehículos
resource "aws_iot_topic_rule" "vehicle_telemetry_rule" {
  name        = "${replace(var.project_name, "-", "_")}_${replace(var.environment, "-", "_")}_telemetry_rule"
  description = "Procesa datos de telemetría de vehículos"
  enabled     = true
  sql         = "SELECT *, timestamp() as aws_timestamp FROM 'vehicles/+/telemetry'"
  sql_version = "2016-03-23"

  # Enviar a Kinesis Data Streams para procesamiento en tiempo real
  kinesis {
    role_arn    = aws_iam_role.iot_kinesis_role.arn
    stream_name = aws_kinesis_stream.vehicle_telemetry_stream.name
    partition_key = "$${vehicle_id}"
  }

  # Almacenar en DynamoDB para consultas rápidas
  dynamodb {
    role_arn   = aws_iam_role.iot_dynamodb_role.arn
    table_name = aws_dynamodb_table.vehicle_status.name
    hash_key_field = "vehicle_id"
    hash_key_value = "$${vehicle_id}"
    range_key_field = "timestamp"
    range_key_value = "$${aws_timestamp}"
  }
}

# Rule para botón de pánico - CRÍTICO
resource "aws_iot_topic_rule" "panic_button_rule" {
  name        = "${replace(var.project_name, "-", "_")}_${replace(var.environment, "-", "_")}_panic_rule"
  description = "Procesa alertas críticas del botón de pánico"
  enabled     = true
  sql         = "SELECT *, timestamp() as aws_timestamp FROM 'vehicles/+/panic'"
  sql_version = "2016-03-23"

  # Notificación inmediata via SNS
  sns {
    role_arn   = aws_iam_role.iot_sns_role.arn
    target_arn = aws_sns_topic.panic_alerts.arn
    message_format = "JSON"
  }

  # Lambda para procesamiento inmediato
  lambda {
    function_arn = aws_lambda_function.panic_processor.arn
  }

  # Almacenar en DynamoDB para auditoría
  dynamodb {
    role_arn   = aws_iam_role.iot_dynamodb_role.arn
    table_name = aws_dynamodb_table.panic_events.name
    hash_key_field = "vehicle_id"
    hash_key_value = "$${vehicle_id}"
    range_key_field = "timestamp"
    range_key_value = "$${aws_timestamp}"
  }
}

# Rule para datos de video
resource "aws_iot_topic_rule" "video_data_rule" {
  name        = "${replace(var.project_name, "-", "_")}_${replace(var.environment, "-", "_")}_video_rule"
  description = "Procesa metadatos y referencias de video"
  enabled     = true
  sql         = "SELECT *, timestamp() as aws_timestamp FROM 'vehicles/+/video'"
  sql_version = "2016-03-23"

  # Procesar con Lambda para análisis de video
  lambda {
    function_arn = aws_lambda_function.video_processor.arn
  }
}

# Kinesis Data Stream para telemetría
resource "aws_kinesis_stream" "vehicle_telemetry_stream" {
  name             = "${var.project_name}-${var.environment}-telemetry"
  shard_count      = 10  # Para manejar 5000 señales/segundo
  retention_period = 24

  shard_level_metrics = [
    "IncomingRecords",
    "OutgoingRecords",
  ]

  tags = {
    Name        = "${var.project_name}-${var.environment}-telemetry-stream"
    Environment = var.environment
    Purpose     = "vehicle-telemetry"
  }
}

# DynamoDB para estado actual de vehículos
resource "aws_dynamodb_table" "vehicle_status" {
  name           = "${var.project_name}-${var.environment}-vehicle-status"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "vehicle_id"
  range_key      = "timestamp"

  attribute {
    name = "vehicle_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  # TTL para datos antiguos (30 días)
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-vehicle-status"
    Environment = var.environment
  }
}

# DynamoDB para eventos de pánico
resource "aws_dynamodb_table" "panic_events" {
  name           = "${var.project_name}-${var.environment}-panic-events"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "vehicle_id"
  range_key      = "timestamp"

  attribute {
    name = "vehicle_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-panic-events"
    Environment = var.environment
  }
}

# SNS Topic para alertas de pánico
resource "aws_sns_topic" "panic_alerts" {
  name = "${var.project_name}-${var.environment}-panic-alerts"

  tags = {
    Name        = "${var.project_name}-${var.environment}-panic-alerts"
    Environment = var.environment
  }
}

# Lambda para procesamiento de pánico
resource "aws_lambda_function" "panic_processor" {
  filename         = "panic_processor.zip"
  function_name    = "${var.project_name}-${var.environment}-panic-processor"
  role            = aws_iam_role.lambda_panic_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.panic_alerts.arn
      ENVIRONMENT   = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-panic-processor"
    Environment = var.environment
  }
}

# Lambda para procesamiento de video
resource "aws_lambda_function" "video_processor" {
  filename         = "video_processor.zip"
  function_name    = "${var.project_name}-${var.environment}-video-processor"
  role            = aws_iam_role.lambda_video_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      S3_BUCKET     = aws_s3_bucket.video_storage.bucket
      ENVIRONMENT   = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-video-processor"
    Environment = var.environment
  }
}

# S3 Bucket para almacenamiento de video
resource "aws_s3_bucket" "video_storage" {
  bucket = "${var.project_name}-${var.environment}-video-storage-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-video-storage"
    Environment = var.environment
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Configuración del bucket S3
resource "aws_s3_bucket_versioning" "video_storage_versioning" {
  bucket = aws_s3_bucket.video_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "video_storage_encryption" {
  bucket = aws_s3_bucket.video_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Data sources
data "aws_region" "current" {}
