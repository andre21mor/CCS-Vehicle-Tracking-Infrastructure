# Integración con DocuSign para firma electrónica

# SSM Parameters para configuración de DocuSign
resource "aws_ssm_parameter" "docusign_integration_key" {
  name  = "/${var.project_name}/${var.environment}/docusign/integration_key"
  type  = "SecureString"
  value = var.docusign_integration_key != "" ? var.docusign_integration_key : "PLACEHOLDER"

  tags = {
    Name        = "${var.project_name}-${var.environment}-docusign-integration-key"
    Environment = var.environment
  }

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "docusign_user_id" {
  name  = "/${var.project_name}/${var.environment}/docusign/user_id"
  type  = "SecureString"
  value = var.docusign_user_id != "" ? var.docusign_user_id : "PLACEHOLDER"

  tags = {
    Name        = "${var.project_name}-${var.environment}-docusign-user-id"
    Environment = var.environment
  }

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "docusign_account_id" {
  name  = "/${var.project_name}/${var.environment}/docusign/account_id"
  type  = "SecureString"
  value = var.docusign_account_id != "" ? var.docusign_account_id : "PLACEHOLDER"

  tags = {
    Name        = "${var.project_name}-${var.environment}-docusign-account-id"
    Environment = var.environment
  }

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "docusign_private_key" {
  name  = "/${var.project_name}/${var.environment}/docusign/private_key"
  type  = "SecureString"
  value = var.docusign_private_key != "" ? var.docusign_private_key : "PLACEHOLDER"

  tags = {
    Name        = "${var.project_name}-${var.environment}-docusign-private-key"
    Environment = var.environment
  }

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "docusign_base_url" {
  name  = "/${var.project_name}/${var.environment}/docusign/base_url"
  type  = "String"
  value = var.docusign_base_url != "" ? var.docusign_base_url : "https://demo.docusign.net/restapi"

  tags = {
    Name        = "${var.project_name}-${var.environment}-docusign-base-url"
    Environment = var.environment
  }
}

# Lambda Layer para DocuSign SDK
resource "aws_lambda_layer_version" "docusign_layer" {
  filename         = "docusign_layer.zip"
  layer_name       = "${var.project_name}-${var.environment}-docusign-layer"
  description      = "DocuSign Python SDK y dependencias"
  
  compatible_runtimes = ["python3.9", "python3.10", "python3.11"]
  
  depends_on = [data.archive_file.docusign_layer]
}

# Crear el layer de DocuSign
data "archive_file" "docusign_layer" {
  type        = "zip"
  output_path = "${path.module}/docusign_layer.zip"
  
  source {
    content = templatefile("${path.module}/create_docusign_layer.py", {
      requirements = file("${path.module}/docusign_requirements.txt")
    })
    filename = "create_layer.py"
  }
}

# Lambda para gestión de firmas DocuSign
resource "aws_lambda_function" "docusign_signature_manager" {
  filename         = "docusign_signature_manager.zip"
  function_name    = "${var.project_name}-${var.environment}-docusign-signature-manager"
  role            = aws_iam_role.lambda_docusign_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 512

  layers = [aws_lambda_layer_version.docusign_layer.arn]

  environment {
    variables = {
      CONTRACTS_TABLE           = aws_dynamodb_table.contracts.name
      SIGNATURES_TABLE         = aws_dynamodb_table.electronic_signatures.name
      CONTRACT_DOCUMENTS_BUCKET = aws_s3_bucket.contract_documents.bucket
      DOCUSIGN_INTEGRATION_KEY  = aws_ssm_parameter.docusign_integration_key.name
      DOCUSIGN_USER_ID         = aws_ssm_parameter.docusign_user_id.name
      DOCUSIGN_ACCOUNT_ID      = aws_ssm_parameter.docusign_account_id.name
      DOCUSIGN_PRIVATE_KEY     = aws_ssm_parameter.docusign_private_key.name
      DOCUSIGN_BASE_URL        = aws_ssm_parameter.docusign_base_url.name
      CALLBACK_URL_BASE        = "https://${var.project_name}-${var.environment}.com/docusign/callback"
      ENVIRONMENT              = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-docusign-signature-manager"
    Environment = var.environment
  }
}

# Lambda para webhook de DocuSign
resource "aws_lambda_function" "docusign_webhook_handler" {
  filename         = "docusign_webhook_handler.zip"
  function_name    = "${var.project_name}-${var.environment}-docusign-webhook-handler"
  role            = aws_iam_role.lambda_docusign_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 60

  layers = [aws_lambda_layer_version.docusign_layer.arn]

  environment {
    variables = {
      CONTRACTS_TABLE      = aws_dynamodb_table.contracts.name
      SIGNATURES_TABLE     = aws_dynamodb_table.electronic_signatures.name
      SNS_TOPIC_ARN       = aws_sns_topic.contract_notifications.arn
      ENVIRONMENT         = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-docusign-webhook-handler"
    Environment = var.environment
  }
}

# API Gateway para webhook de DocuSign
resource "aws_api_gateway_resource" "docusign_webhook" {
  rest_api_id = data.aws_api_gateway_rest_api.main.id
  parent_id   = data.aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "docusign-webhook"
}

resource "aws_api_gateway_method" "docusign_webhook_post" {
  rest_api_id   = data.aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.docusign_webhook.id
  http_method   = "POST"
  authorization = "NONE"  # DocuSign webhook no usa auth estándar
}

resource "aws_api_gateway_integration" "docusign_webhook_integration" {
  rest_api_id = data.aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.docusign_webhook.id
  http_method = aws_api_gateway_method.docusign_webhook_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.docusign_webhook_handler.invoke_arn
}

# Permisos para API Gateway invocar Lambda webhook
resource "aws_lambda_permission" "allow_api_gateway_docusign_webhook" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.docusign_webhook_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${data.aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# IAM Role para funciones Lambda de DocuSign
resource "aws_iam_role" "lambda_docusign_role" {
  name = "${var.project_name}-${var.environment}-lambda-docusign-role"

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

resource "aws_iam_role_policy_attachment" "lambda_docusign_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_docusign_role.name
}

resource "aws_iam_role_policy" "lambda_docusign_policy" {
  name = "${var.project_name}-${var.environment}-lambda-docusign-policy"
  role = aws_iam_role.lambda_docusign_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.contracts.arn,
          aws_dynamodb_table.electronic_signatures.arn,
          "${aws_dynamodb_table.contracts.arn}/index/*",
          "${aws_dynamodb_table.electronic_signatures.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.contract_documents.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.contract_documents.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          aws_ssm_parameter.docusign_integration_key.arn,
          aws_ssm_parameter.docusign_user_id.arn,
          aws_ssm_parameter.docusign_account_id.arn,
          aws_ssm_parameter.docusign_private_key.arn,
          aws_ssm_parameter.docusign_base_url.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.contract_notifications.arn
      }
    ]
  })
}

# Data sources
data "aws_api_gateway_rest_api" "main" {
  name = "${var.project_name}-${var.environment}-api"
}
