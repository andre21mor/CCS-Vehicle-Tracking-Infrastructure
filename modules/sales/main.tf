# Módulo de Ventas - Tablas DynamoDB y Funciones Lambda

# DynamoDB Table para clientes de ventas
resource "aws_dynamodb_table" "sales_clients" {
  name           = "${var.project_name}-${var.environment}-sales-clients"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "client_id"

  attribute {
    name = "client_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  attribute {
    name = "company_name"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "N"
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
    hash_key = "company_name"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # GSI para consultar por estado
  global_secondary_index {
    name     = "StatusIndex"
    hash_key = "status"
    range_key = "created_at"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-sales-clients"
    Environment = var.environment
  }
}

# DynamoDB Table para inventario de ventas
resource "aws_dynamodb_table" "sales_inventory" {
  name           = "${var.project_name}-${var.environment}-sales-inventory"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "inventory_id"

  attribute {
    name = "inventory_id"
    type = "S"
  }

  attribute {
    name = "vehicle_type"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "price_range"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "N"
  }

  # GSI para consultar por tipo de vehículo
  global_secondary_index {
    name     = "VehicleTypeIndex"
    hash_key = "vehicle_type"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # GSI para consultar por estado
  global_secondary_index {
    name     = "StatusIndex"
    hash_key = "status"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # GSI para consultar por rango de precio
  global_secondary_index {
    name     = "PriceRangeIndex"
    hash_key = "price_range"
    range_key = "created_at"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-sales-inventory"
    Environment = var.environment
  }
}

# DynamoDB Table para contratos de venta
resource "aws_dynamodb_table" "sales_contracts" {
  name           = "${var.project_name}-${var.environment}-sales-contracts"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "contract_id"

  attribute {
    name = "contract_id"
    type = "S"
  }

  attribute {
    name = "client_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "N"
  }

  attribute {
    name = "total_amount"
    type = "N"
  }

  # GSI para consultar por cliente
  global_secondary_index {
    name     = "ClientIndex"
    hash_key = "client_id"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # GSI para consultar por estado
  global_secondary_index {
    name     = "StatusIndex"
    hash_key = "status"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # GSI para consultar por monto
  global_secondary_index {
    name     = "AmountIndex"
    hash_key = "total_amount"
    range_key = "created_at"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-sales-contracts"
    Environment = var.environment
  }
}

# DynamoDB Table para cotizaciones
resource "aws_dynamodb_table" "sales_quotations" {
  name           = "${var.project_name}-${var.environment}-sales-quotations"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "quotation_id"

  attribute {
    name = "quotation_id"
    type = "S"
  }

  attribute {
    name = "client_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "N"
  }

  # GSI para consultar por cliente
  global_secondary_index {
    name     = "ClientIndex"
    hash_key = "client_id"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # GSI para consultar por estado
  global_secondary_index {
    name     = "StatusIndex"
    hash_key = "status"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # TTL para cotizaciones expiradas (30 días)
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-sales-quotations"
    Environment = var.environment
  }
}

# Lambda para gestión de clientes de ventas
resource "aws_lambda_function" "sales_clients_api" {
  filename         = "sales_clients_api.zip"
  function_name    = "${var.project_name}-${var.environment}-sales-clients-api"
  role            = aws_iam_role.sales_lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      CLIENTS_TABLE = aws_dynamodb_table.sales_clients.name
      ENVIRONMENT   = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-sales-clients-api"
    Environment = var.environment
  }
}

# Lambda para gestión de inventario de ventas
resource "aws_lambda_function" "sales_inventory_api" {
  filename         = "sales_inventory_api.zip"
  function_name    = "${var.project_name}-${var.environment}-sales-inventory-api"
  role            = aws_iam_role.sales_lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      INVENTORY_TABLE = aws_dynamodb_table.sales_inventory.name
      ENVIRONMENT     = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-sales-inventory-api"
    Environment = var.environment
  }
}

# Lambda para gestión de contratos de venta
resource "aws_lambda_function" "sales_contracts_api" {
  filename         = "sales_contracts_api.zip"
  function_name    = "${var.project_name}-${var.environment}-sales-contracts-api"
  role            = aws_iam_role.sales_lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      CONTRACTS_TABLE   = aws_dynamodb_table.sales_contracts.name
      CLIENTS_TABLE     = aws_dynamodb_table.sales_clients.name
      INVENTORY_TABLE   = aws_dynamodb_table.sales_inventory.name
      ENVIRONMENT       = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-sales-contracts-api"
    Environment = var.environment
  }
}

# Lambda para dashboard de ventas
resource "aws_lambda_function" "sales_dashboard_api" {
  filename         = "sales_dashboard_api.zip"
  function_name    = "${var.project_name}-${var.environment}-sales-dashboard-api"
  role            = aws_iam_role.sales_lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      CONTRACTS_TABLE   = aws_dynamodb_table.sales_contracts.name
      CLIENTS_TABLE     = aws_dynamodb_table.sales_clients.name
      INVENTORY_TABLE   = aws_dynamodb_table.sales_inventory.name
      QUOTATIONS_TABLE  = aws_dynamodb_table.sales_quotations.name
      ENVIRONMENT       = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-sales-dashboard-api"
    Environment = var.environment
  }
}

# API Gateway Resources para Sales

# /sales - Recurso principal de ventas
resource "aws_api_gateway_resource" "sales" {
  rest_api_id = var.api_gateway_id
  parent_id   = var.api_gateway_root_resource_id
  path_part   = "sales"
}

# /sales/clients
resource "aws_api_gateway_resource" "sales_clients" {
  rest_api_id = var.api_gateway_id
  parent_id   = aws_api_gateway_resource.sales.id
  path_part   = "clients"
}

# /sales/clients/{clientId}
resource "aws_api_gateway_resource" "sales_client_by_id" {
  rest_api_id = var.api_gateway_id
  parent_id   = aws_api_gateway_resource.sales_clients.id
  path_part   = "{clientId}"
}

# /sales/inventory
resource "aws_api_gateway_resource" "sales_inventory" {
  rest_api_id = var.api_gateway_id
  parent_id   = aws_api_gateway_resource.sales.id
  path_part   = "inventory"
}

# /sales/inventory/{inventoryId}
resource "aws_api_gateway_resource" "sales_inventory_by_id" {
  rest_api_id = var.api_gateway_id
  parent_id   = aws_api_gateway_resource.sales_inventory.id
  path_part   = "{inventoryId}"
}

# /sales/contracts
resource "aws_api_gateway_resource" "sales_contracts" {
  rest_api_id = var.api_gateway_id
  parent_id   = aws_api_gateway_resource.sales.id
  path_part   = "contracts"
}

# /sales/contracts/{contractId}
resource "aws_api_gateway_resource" "sales_contract_by_id" {
  rest_api_id = var.api_gateway_id
  parent_id   = aws_api_gateway_resource.sales_contracts.id
  path_part   = "{contractId}"
}

# /sales/dashboard
resource "aws_api_gateway_resource" "sales_dashboard" {
  rest_api_id = var.api_gateway_id
  parent_id   = aws_api_gateway_resource.sales.id
  path_part   = "dashboard"
}

# Métodos API para Clientes

# GET /sales/clients
resource "aws_api_gateway_method" "get_sales_clients" {
  rest_api_id   = var.api_gateway_id
  resource_id   = aws_api_gateway_resource.sales_clients.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.cognito_authorizer_id
}

resource "aws_api_gateway_integration" "get_sales_clients_integration" {
  rest_api_id = var.api_gateway_id
  resource_id = aws_api_gateway_resource.sales_clients.id
  http_method = aws_api_gateway_method.get_sales_clients.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sales_clients_api.invoke_arn
}

# POST /sales/clients
resource "aws_api_gateway_method" "post_sales_clients" {
  rest_api_id   = var.api_gateway_id
  resource_id   = aws_api_gateway_resource.sales_clients.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.cognito_authorizer_id
}

resource "aws_api_gateway_integration" "post_sales_clients_integration" {
  rest_api_id = var.api_gateway_id
  resource_id = aws_api_gateway_resource.sales_clients.id
  http_method = aws_api_gateway_method.post_sales_clients.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sales_clients_api.invoke_arn
}

# GET /sales/clients/{clientId}
resource "aws_api_gateway_method" "get_sales_client_by_id" {
  rest_api_id   = var.api_gateway_id
  resource_id   = aws_api_gateway_resource.sales_client_by_id.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.cognito_authorizer_id
}

resource "aws_api_gateway_integration" "get_sales_client_by_id_integration" {
  rest_api_id = var.api_gateway_id
  resource_id = aws_api_gateway_resource.sales_client_by_id.id
  http_method = aws_api_gateway_method.get_sales_client_by_id.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sales_clients_api.invoke_arn
}

# PUT /sales/clients/{clientId}
resource "aws_api_gateway_method" "put_sales_client_by_id" {
  rest_api_id   = var.api_gateway_id
  resource_id   = aws_api_gateway_resource.sales_client_by_id.id
  http_method   = "PUT"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.cognito_authorizer_id
}

resource "aws_api_gateway_integration" "put_sales_client_by_id_integration" {
  rest_api_id = var.api_gateway_id
  resource_id = aws_api_gateway_resource.sales_client_by_id.id
  http_method = aws_api_gateway_method.put_sales_client_by_id.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sales_clients_api.invoke_arn
}

# DELETE /sales/clients/{clientId}
resource "aws_api_gateway_method" "delete_sales_client_by_id" {
  rest_api_id   = var.api_gateway_id
  resource_id   = aws_api_gateway_resource.sales_client_by_id.id
  http_method   = "DELETE"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.cognito_authorizer_id
}

resource "aws_api_gateway_integration" "delete_sales_client_by_id_integration" {
  rest_api_id = var.api_gateway_id
  resource_id = aws_api_gateway_resource.sales_client_by_id.id
  http_method = aws_api_gateway_method.delete_sales_client_by_id.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sales_clients_api.invoke_arn
}

# Métodos API para Inventario

# GET /sales/inventory
resource "aws_api_gateway_method" "get_sales_inventory" {
  rest_api_id   = var.api_gateway_id
  resource_id   = aws_api_gateway_resource.sales_inventory.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.cognito_authorizer_id
}

resource "aws_api_gateway_integration" "get_sales_inventory_integration" {
  rest_api_id = var.api_gateway_id
  resource_id = aws_api_gateway_resource.sales_inventory.id
  http_method = aws_api_gateway_method.get_sales_inventory.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sales_inventory_api.invoke_arn
}

# POST /sales/inventory
resource "aws_api_gateway_method" "post_sales_inventory" {
  rest_api_id   = var.api_gateway_id
  resource_id   = aws_api_gateway_resource.sales_inventory.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.cognito_authorizer_id
}

resource "aws_api_gateway_integration" "post_sales_inventory_integration" {
  rest_api_id = var.api_gateway_id
  resource_id = aws_api_gateway_resource.sales_inventory.id
  http_method = aws_api_gateway_method.post_sales_inventory.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sales_inventory_api.invoke_arn
}

# Métodos API para Contratos

# GET /sales/contracts
resource "aws_api_gateway_method" "get_sales_contracts" {
  rest_api_id   = var.api_gateway_id
  resource_id   = aws_api_gateway_resource.sales_contracts.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.cognito_authorizer_id
}

resource "aws_api_gateway_integration" "get_sales_contracts_integration" {
  rest_api_id = var.api_gateway_id
  resource_id = aws_api_gateway_resource.sales_contracts.id
  http_method = aws_api_gateway_method.get_sales_contracts.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sales_contracts_api.invoke_arn
}

# POST /sales/contracts
resource "aws_api_gateway_method" "post_sales_contracts" {
  rest_api_id   = var.api_gateway_id
  resource_id   = aws_api_gateway_resource.sales_contracts.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.cognito_authorizer_id
}

resource "aws_api_gateway_integration" "post_sales_contracts_integration" {
  rest_api_id = var.api_gateway_id
  resource_id = aws_api_gateway_resource.sales_contracts.id
  http_method = aws_api_gateway_method.post_sales_contracts.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sales_contracts_api.invoke_arn
}

# GET /sales/dashboard
resource "aws_api_gateway_method" "get_sales_dashboard" {
  rest_api_id   = var.api_gateway_id
  resource_id   = aws_api_gateway_resource.sales_dashboard.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = var.cognito_authorizer_id
}

resource "aws_api_gateway_integration" "get_sales_dashboard_integration" {
  rest_api_id = var.api_gateway_id
  resource_id = aws_api_gateway_resource.sales_dashboard.id
  http_method = aws_api_gateway_method.get_sales_dashboard.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.sales_dashboard_api.invoke_arn
}

# Permisos Lambda
resource "aws_lambda_permission" "allow_api_gateway_sales_clients" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sales_clients_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.api_gateway_id}/*/*"
}

resource "aws_lambda_permission" "allow_api_gateway_sales_inventory" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sales_inventory_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.api_gateway_id}/*/*"
}

resource "aws_lambda_permission" "allow_api_gateway_sales_contracts" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sales_contracts_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.api_gateway_id}/*/*"
}

resource "aws_lambda_permission" "allow_api_gateway_sales_dashboard" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sales_dashboard_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.api_gateway_id}/*/*"
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
