# API Gateway para aplicaciones web y móvil

# API Gateway REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-${var.environment}-api"
  description = "API para plataforma de seguimiento vehicular"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  # Configuración de CORS
  binary_media_types = [
    "application/octet-stream",
    "image/*",
    "video/*"
  ]

  tags = {
    Name        = "${var.project_name}-${var.environment}-api"
    Environment = var.environment
  }
}

# Authorizer de Cognito
resource "aws_api_gateway_authorizer" "cognito_authorizer" {
  name                   = "${var.project_name}-${var.environment}-cognito-authorizer"
  rest_api_id           = aws_api_gateway_rest_api.main.id
  type                  = "COGNITO_USER_POOLS"
  provider_arns         = [data.aws_cognito_user_pool.client_pool.arn]
  identity_source       = "method.request.header.Authorization"
  authorizer_credentials = aws_iam_role.api_gateway_cognito_role.arn
}

# Recursos de la API

# /vehicles - Gestión de vehículos
resource "aws_api_gateway_resource" "vehicles" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "vehicles"
}

# /vehicles/{vehicleId}
resource "aws_api_gateway_resource" "vehicle_by_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.vehicles.id
  path_part   = "{vehicleId}"
}

# /vehicles/{vehicleId}/telemetry
resource "aws_api_gateway_resource" "vehicle_telemetry" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.vehicle_by_id.id
  path_part   = "telemetry"
}

# /vehicles/{vehicleId}/location
resource "aws_api_gateway_resource" "vehicle_location" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.vehicle_by_id.id
  path_part   = "location"
}

# /vehicles/{vehicleId}/alerts
resource "aws_api_gateway_resource" "vehicle_alerts" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.vehicle_by_id.id
  path_part   = "alerts"
}

# /vehicles/{vehicleId}/video
resource "aws_api_gateway_resource" "vehicle_video" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.vehicle_by_id.id
  path_part   = "video"
}

# /fleet - Gestión de flotas
resource "aws_api_gateway_resource" "fleet" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "fleet"
}

# /fleet/dashboard
resource "aws_api_gateway_resource" "fleet_dashboard" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.fleet.id
  path_part   = "dashboard"
}

# /reports - Reportes y estadísticas
resource "aws_api_gateway_resource" "reports" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "reports"
}

# /notifications - Gestión de notificaciones
resource "aws_api_gateway_resource" "notifications" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "notifications"
}

# /payments - Sistema de pagos
resource "aws_api_gateway_resource" "payments" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "payments"
}

# /contracts - Gestión de contratos
resource "aws_api_gateway_resource" "contracts" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "contracts"
}

# /contracts/{contractId}
resource "aws_api_gateway_resource" "contract_by_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.contracts.id
  path_part   = "{contractId}"
}

# /contracts/dashboard
resource "aws_api_gateway_resource" "contracts_dashboard" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.contracts.id
  path_part   = "dashboard"
}

# /approvals - Gestión de aprobaciones
resource "aws_api_gateway_resource" "approvals" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "approvals"
}

# /approvals/pending
resource "aws_api_gateway_resource" "approvals_pending" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.approvals.id
  path_part   = "pending"
}

# /approvals/{approvalId}/approve
resource "aws_api_gateway_resource" "approval_by_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.approvals.id
  path_part   = "{approvalId}"
}

resource "aws_api_gateway_resource" "approval_approve" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.approval_by_id.id
  path_part   = "approve"
}

resource "aws_api_gateway_resource" "approval_reject" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.approval_by_id.id
  path_part   = "reject"
}

# Lambda Functions para la API

# Lambda para gestión de vehículos
resource "aws_lambda_function" "vehicle_management" {
  filename         = "vehicle_management.zip"
  function_name    = "${var.project_name}-${var.environment}-vehicle-management"
  role            = aws_iam_role.lambda_api_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      DYNAMODB_TABLE = "${var.project_name}-${var.environment}-vehicles"
      KINESIS_STREAM = "${var.project_name}-${var.environment}-telemetry"
      ENVIRONMENT    = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-vehicle-management"
    Environment = var.environment
  }
}

# Lambda para telemetría en tiempo real
resource "aws_lambda_function" "telemetry_api" {
  filename         = "telemetry_api.zip"
  function_name    = "${var.project_name}-${var.environment}-telemetry-api"
  role            = aws_iam_role.lambda_api_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      DYNAMODB_TABLE = "${var.project_name}-${var.environment}-vehicle-status"
      KINESIS_STREAM = "${var.project_name}-${var.environment}-telemetry"
      ENVIRONMENT    = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-telemetry-api"
    Environment = var.environment
  }
}

# Lambda para dashboard de flota
resource "aws_lambda_function" "fleet_dashboard" {
  filename         = "fleet_dashboard.zip"
  function_name    = "${var.project_name}-${var.environment}-fleet-dashboard"
  role            = aws_iam_role.lambda_api_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      DYNAMODB_TABLE = "${var.project_name}-${var.environment}-vehicle-status"
      ENVIRONMENT    = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-fleet-dashboard"
    Environment = var.environment
  }
}

# Lambda para reportes
resource "aws_lambda_function" "reports_api" {
  filename         = "reports_api.zip"
  function_name    = "${var.project_name}-${var.environment}-reports-api"
  role            = aws_iam_role.lambda_api_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 60

  environment {
    variables = {
      DYNAMODB_TABLE = "${var.project_name}-${var.environment}-vehicle-status"
      S3_BUCKET      = "${var.project_name}-${var.environment}-reports"
      ENVIRONMENT    = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-reports-api"
    Environment = var.environment
  }
}

# Lambda para notificaciones
resource "aws_lambda_function" "notifications_api" {
  filename         = "notifications_api.zip"
  function_name    = "${var.project_name}-${var.environment}-notifications-api"
  role            = aws_iam_role.lambda_api_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      SNS_TOPIC_ARN = "arn:aws:sns:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.project_name}-${var.environment}-vehicle-alerts"
      ENVIRONMENT   = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-notifications-api"
    Environment = var.environment
  }
}

# Lambda para gestión de contratos (referencia externa)
# data "aws_lambda_function" "contract_management_api" {
#   function_name = "${var.project_name}-${var.environment}-contract-management-api"
#   depends_on    = [var.contract_approval_module]
# }

# Métodos de la API

# GET /vehicles - Listar vehículos
resource "aws_api_gateway_method" "get_vehicles" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.vehicles.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id

  request_parameters = {
    "method.request.querystring.limit"  = false
    "method.request.querystring.offset" = false
    "method.request.querystring.status" = false
  }
}

resource "aws_api_gateway_integration" "get_vehicles_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.vehicles.id
  http_method = aws_api_gateway_method.get_vehicles.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.vehicle_management.invoke_arn
}

# GET /vehicles/{vehicleId} - Obtener vehículo específico
resource "aws_api_gateway_method" "get_vehicle_by_id" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.vehicle_by_id.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id

  request_parameters = {
    "method.request.path.vehicleId" = true
  }
}

resource "aws_api_gateway_integration" "get_vehicle_by_id_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.vehicle_by_id.id
  http_method = aws_api_gateway_method.get_vehicle_by_id.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.vehicle_management.invoke_arn
}

# GET /vehicles/{vehicleId}/telemetry - Obtener telemetría
resource "aws_api_gateway_method" "get_vehicle_telemetry" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.vehicle_telemetry.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id

  request_parameters = {
    "method.request.path.vehicleId"        = true
    "method.request.querystring.startTime" = false
    "method.request.querystring.endTime"   = false
    "method.request.querystring.limit"     = false
  }
}

resource "aws_api_gateway_integration" "get_vehicle_telemetry_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.vehicle_telemetry.id
  http_method = aws_api_gateway_method.get_vehicle_telemetry.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.telemetry_api.invoke_arn
}

# GET /fleet/dashboard - Dashboard de flota
resource "aws_api_gateway_method" "get_fleet_dashboard" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.fleet_dashboard.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

resource "aws_api_gateway_integration" "get_fleet_dashboard_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.fleet_dashboard.id
  http_method = aws_api_gateway_method.get_fleet_dashboard.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.fleet_dashboard.invoke_arn
}

# GET /reports - Generar reportes
resource "aws_api_gateway_method" "get_reports" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.reports.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id

  request_parameters = {
    "method.request.querystring.type"      = true
    "method.request.querystring.startDate" = true
    "method.request.querystring.endDate"   = true
    "method.request.querystring.vehicleId" = false
  }
}

resource "aws_api_gateway_integration" "get_reports_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.reports.id
  http_method = aws_api_gateway_method.get_reports.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.reports_api.invoke_arn
}

# POST /notifications - Configurar notificaciones
resource "aws_api_gateway_method" "post_notifications" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.notifications.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

resource "aws_api_gateway_integration" "post_notifications_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.notifications.id
  http_method = aws_api_gateway_method.post_notifications.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.notifications_api.invoke_arn
}

# Configuración de CORS para todos los recursos
resource "aws_api_gateway_method" "options_vehicles" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.vehicles.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_vehicles_integration" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.vehicles.id
  http_method = aws_api_gateway_method.options_vehicles.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "options_vehicles_response" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.vehicles.id
  http_method = aws_api_gateway_method.options_vehicles.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "options_vehicles_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.vehicles.id
  http_method = aws_api_gateway_method.options_vehicles.http_method
  status_code = aws_api_gateway_method_response.options_vehicles_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT,DELETE'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Deployment de la API
resource "aws_api_gateway_deployment" "main" {
  depends_on = [
    aws_api_gateway_integration.get_vehicles_integration,
    aws_api_gateway_integration.get_vehicle_by_id_integration,
    aws_api_gateway_integration.get_vehicle_telemetry_integration,
    aws_api_gateway_integration.get_fleet_dashboard_integration,
    aws_api_gateway_integration.get_reports_integration,
    aws_api_gateway_integration.post_notifications_integration,
    aws_api_gateway_integration.options_vehicles_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.vehicles.id,
      aws_api_gateway_method.get_vehicles.id,
      aws_api_gateway_integration.get_vehicles_integration.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Stage de la API
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  # Configuración de logging
  xray_tracing_enabled = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip            = "$context.identity.sourceIp"
      caller        = "$context.identity.caller"
      user          = "$context.identity.user"
      requestTime   = "$context.requestTime"
      httpMethod    = "$context.httpMethod"
      resourcePath  = "$context.resourcePath"
      status        = "$context.status"
      protocol      = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-stage"
    Environment = var.environment
  }
}

# CloudWatch Log Group para API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-logs"
    Environment = var.environment
  }
}

# S3 Bucket para reportes
resource "aws_s3_bucket" "reports" {
  bucket = "${var.project_name}-${var.environment}-reports-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-reports"
    Environment = var.environment
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_versioning" "reports_versioning" {
  bucket = aws_s3_bucket.reports.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports_encryption" {
  bucket = aws_s3_bucket.reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_cognito_user_pool" "client_pool" {
  user_pool_id = var.user_pool_id
}
