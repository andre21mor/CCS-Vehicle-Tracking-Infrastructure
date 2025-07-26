# Amazon Rekognition Integration for Vehicle Tracking

# S3 Bucket for Rekognition Analysis
resource "aws_s3_bucket" "rekognition_analysis" {
  bucket = "${var.project_name}-${var.environment}-rekognition-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "Rekognition Analysis"
    Environment = var.environment
    Purpose     = "Driver Safety Analysis"
  }
}

# Lambda function for Rekognition processing
resource "aws_lambda_function" "rekognition_processor" {
  filename         = "rekognition_processor.zip"
  function_name    = "${var.project_name}-${var.environment}-rekognition-processor"
  role            = aws_iam_role.rekognition_lambda_role.arn
  handler         = "index.lambda_handler"
  runtime         = "python3.9"
  timeout         = 60
  memory_size     = 512

  environment {
    variables = {
      RESULTS_TABLE = aws_dynamodb_table.rekognition_results.name
      ALERTS_TOPIC  = var.alerts_topic_arn
    }
  }

  tags = {
    Name        = "Rekognition Processor"
    Environment = var.environment
  }
}

# DynamoDB table for Rekognition results
resource "aws_dynamodb_table" "rekognition_results" {
  name           = "${var.project_name}-${var.environment}-rekognition-results"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "analysis_id"
  range_key      = "timestamp"

  attribute {
    name = "analysis_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
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

  # GSI for vehicle-based queries
  global_secondary_index {
    name     = "VehicleIndex"
    hash_key = "vehicle_id"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  # GSI for alert-based queries
  global_secondary_index {
    name     = "AlertIndex"
    hash_key = "alert_type"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  # TTL for automatic cleanup (90 days)
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "Rekognition Results"
    Environment = var.environment
  }
}

# IAM role for Rekognition Lambda
resource "aws_iam_role" "rekognition_lambda_role" {
  name = "${var.project_name}-${var.environment}-rekognition-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for Rekognition Lambda
resource "aws_iam_role_policy" "rekognition_lambda_policy" {
  name = "${var.project_name}-${var.environment}-rekognition-lambda-policy"
  role = aws_iam_role.rekognition_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "rekognition:DetectFaces",
          "rekognition:DetectLabels",
          "rekognition:DetectText",
          "rekognition:RecognizeCelebrities"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.rekognition_analysis.arn}/*",
          "${var.video_storage_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.rekognition_results.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = var.alerts_topic_arn
      }
    ]
  })
}

# S3 trigger for automatic processing
resource "aws_s3_bucket_notification" "rekognition_trigger" {
  bucket = var.video_storage_bucket_id

  lambda_function {
    lambda_function_arn = aws_lambda_function.rekognition_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "analysis-required/"
    filter_suffix       = ".jpg"
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke]
}

# Permission for S3 to invoke Lambda
resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rekognition_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.video_storage_bucket_arn
}

# CloudWatch alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "rekognition_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-rekognition-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors rekognition lambda errors"

  dimensions = {
    FunctionName = aws_lambda_function.rekognition_processor.function_name
  }

  alarm_actions = [var.alerts_topic_arn]
}

# Random string for unique bucket naming
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}
