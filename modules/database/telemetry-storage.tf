# Telemetry Hot Storage - DynamoDB with TTL
resource "aws_dynamodb_table" "telemetry_hot" {
  name           = "${var.project_name}-${var.environment}-telemetry-hot"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "vehicle_id"
  range_key      = "timestamp"

  # TTL for automatic cleanup after 48 hours
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  attribute {
    name = "vehicle_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  # GSI for time-based queries
  global_secondary_index {
    name     = "TimestampIndex"
    hash_key = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name        = "Telemetry Hot Storage"
    Environment = var.environment
    DataType    = "IoT-Sensors"
    Retention   = "48-hours"
  }
}

# Telemetry Warm Storage - DynamoDB for recent analysis
resource "aws_dynamodb_table" "telemetry_warm" {
  name           = "${var.project_name}-${var.environment}-telemetry-warm"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "vehicle_date"
  range_key      = "timestamp"

  # TTL for cleanup after 30 days
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  attribute {
    name = "vehicle_date"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"
  }

  # GSI for date-based queries across vehicles
  global_secondary_index {
    name     = "DateIndex"
    hash_key = "date"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name        = "Telemetry Warm Storage"
    Environment = var.environment
    DataType    = "IoT-Sensors"
    Retention   = "30-days"
  }
}

# S3 Bucket for Cold Storage (Historical Data)
resource "aws_s3_bucket" "telemetry_cold" {
  bucket = "${var.project_name}-${var.environment}-telemetry-cold-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "Telemetry Cold Storage"
    Environment = var.environment
    DataType    = "IoT-Historical"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "telemetry_cold_lifecycle" {
  bucket = aws_s3_bucket.telemetry_cold.id

  rule {
    id     = "telemetry_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2555  # 7 years retention
    }
  }
}

# Video Storage
resource "aws_s3_bucket" "video_storage" {
  bucket = "${var.project_name}-${var.environment}-video-storage-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "Video Storage"
    Environment = var.environment
    DataType    = "Video"
  }
}

resource "aws_s3_bucket_intelligent_tiering_configuration" "video_tiering" {
  bucket = aws_s3_bucket.video_storage.id
  name   = "video-intelligent-tiering"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}

# Video Metadata Table
resource "aws_dynamodb_table" "video_metadata" {
  name           = "${var.project_name}-${var.environment}-video-metadata"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "video_id"

  attribute {
    name = "video_id"
    type = "S"
  }

  attribute {
    name = "vehicle_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  # GSI for vehicle-based queries
  global_secondary_index {
    name     = "VehicleIndex"
    hash_key = "vehicle_id"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name        = "Video Metadata"
    Environment = var.environment
    DataType    = "Video-Metadata"
  }
}
