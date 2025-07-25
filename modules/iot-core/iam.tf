# IAM Roles y Políticas para AWS IoT Core

# Role para IoT -> Kinesis
resource "aws_iam_role" "iot_kinesis_role" {
  name = "${var.project_name}-${var.environment}-iot-kinesis-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "iot.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "iot_kinesis_policy" {
  name = "${var.project_name}-${var.environment}-iot-kinesis-policy"
  role = aws_iam_role.iot_kinesis_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:PutRecord",
          "kinesis:PutRecords"
        ]
        Resource = aws_kinesis_stream.vehicle_telemetry_stream.arn
      }
    ]
  })
}

# Role para IoT -> DynamoDB
resource "aws_iam_role" "iot_dynamodb_role" {
  name = "${var.project_name}-${var.environment}-iot-dynamodb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "iot.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "iot_dynamodb_policy" {
  name = "${var.project_name}-${var.environment}-iot-dynamodb-policy"
  role = aws_iam_role.iot_dynamodb_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          aws_dynamodb_table.vehicle_status.arn,
          aws_dynamodb_table.panic_events.arn
        ]
      }
    ]
  })
}

# Role para IoT -> SNS
resource "aws_iam_role" "iot_sns_role" {
  name = "${var.project_name}-${var.environment}-iot-sns-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "iot.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "iot_sns_policy" {
  name = "${var.project_name}-${var.environment}-iot-sns-policy"
  role = aws_iam_role.iot_sns_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.panic_alerts.arn
      }
    ]
  })
}

# Role para Lambda de procesamiento de pánico
resource "aws_iam_role" "lambda_panic_role" {
  name = "${var.project_name}-${var.environment}-lambda-panic-role"

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

resource "aws_iam_role_policy_attachment" "lambda_panic_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_panic_role.name
}

resource "aws_iam_role_policy" "lambda_panic_policy" {
  name = "${var.project_name}-${var.environment}-lambda-panic-policy"
  role = aws_iam_role.lambda_panic_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.panic_alerts.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem"
        ]
        Resource = aws_dynamodb_table.panic_events.arn
      }
    ]
  })
}

# Role para Lambda de procesamiento de video
resource "aws_iam_role" "lambda_video_role" {
  name = "${var.project_name}-${var.environment}-lambda-video-role"

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

resource "aws_iam_role_policy_attachment" "lambda_video_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_video_role.name
}

resource "aws_iam_role_policy" "lambda_video_policy" {
  name = "${var.project_name}-${var.environment}-lambda-video-policy"
  role = aws_iam_role.lambda_video_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.video_storage.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "rekognition:DetectLabels",
          "rekognition:DetectFaces",
          "rekognition:RecognizeCelebrities"
        ]
        Resource = "*"
      }
    ]
  })
}

# Permisos para que IoT pueda invocar Lambda
resource "aws_lambda_permission" "allow_iot_panic" {
  statement_id  = "AllowExecutionFromIoTPanic"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.panic_processor.function_name
  principal     = "iot.amazonaws.com"
  source_arn    = aws_iot_topic_rule.panic_button_rule.arn
}

resource "aws_lambda_permission" "allow_iot_video" {
  statement_id  = "AllowExecutionFromIoTVideo"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.video_processor.function_name
  principal     = "iot.amazonaws.com"
  source_arn    = aws_iot_topic_rule.video_data_rule.arn
}
