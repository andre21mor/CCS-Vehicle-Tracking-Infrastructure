# Sistema de Aprobación de Contratos con Firma Electrónica

# DynamoDB Table para contratos
resource "aws_dynamodb_table" "contracts" {
  name           = "${var.project_name}-${var.environment}-contracts"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "contract_id"

  attribute {
    name = "contract_id"
    type = "S"
  }

  attribute {
    name = "customer_id"
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
    name = "vehicle_count"
    type = "N"
  }

  # GSI para consultar contratos por cliente
  global_secondary_index {
    name     = "CustomerIndex"
    hash_key = "customer_id"
    range_key = "created_at"
  }

  # GSI para consultar por estado
  global_secondary_index {
    name     = "StatusIndex"
    hash_key = "status"
    range_key = "created_at"
  }

  # GSI para consultar por cantidad de vehículos
  global_secondary_index {
    name     = "VehicleCountIndex"
    hash_key = "vehicle_count"
    range_key = "created_at"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-contracts"
    Environment = var.environment
  }
}

# DynamoDB Table para aprobaciones
resource "aws_dynamodb_table" "contract_approvals" {
  name           = "${var.project_name}-${var.environment}-contract-approvals"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "approval_id"

  attribute {
    name = "approval_id"
    type = "S"
  }

  attribute {
    name = "contract_id"
    type = "S"
  }

  attribute {
    name = "approver_id"
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

  # GSI para consultar aprobaciones por contrato
  global_secondary_index {
    name     = "ContractIndex"
    hash_key = "contract_id"
    range_key = "created_at"
  }

  # GSI para consultar aprobaciones por aprobador
  global_secondary_index {
    name     = "ApproverIndex"
    hash_key = "approver_id"
    range_key = "created_at"
  }

  # GSI para consultar por estado
  global_secondary_index {
    name     = "StatusIndex"
    hash_key = "status"
    range_key = "created_at"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-contract-approvals"
    Environment = var.environment
  }
}

# DynamoDB Table para firmas electrónicas
resource "aws_dynamodb_table" "electronic_signatures" {
  name           = "${var.project_name}-${var.environment}-electronic-signatures"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "signature_id"

  attribute {
    name = "signature_id"
    type = "S"
  }

  attribute {
    name = "contract_id"
    type = "S"
  }

  attribute {
    name = "signer_id"
    type = "S"
  }

  attribute {
    name = "signed_at"
    type = "N"
  }

  # GSI para consultar firmas por contrato
  global_secondary_index {
    name     = "ContractIndex"
    hash_key = "contract_id"
    range_key = "signed_at"
  }

  # GSI para consultar firmas por firmante
  global_secondary_index {
    name     = "SignerIndex"
    hash_key = "signer_id"
    range_key = "signed_at"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-electronic-signatures"
    Environment = var.environment
  }
}

# Step Functions State Machine para flujo de aprobación
resource "aws_sfn_state_machine" "contract_approval_workflow" {
  name     = "${var.project_name}-${var.environment}-contract-approval"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = jsonencode({
    Comment = "Flujo de aprobación de contratos con validación de cantidad de vehículos"
    StartAt = "ValidateContract"
    States = {
      ValidateContract = {
        Type = "Task"
        Resource = aws_lambda_function.contract_validator.arn
        Next = "CheckVehicleCount"
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 6
            BackoffRate = 2
          }
        ]
      }
      CheckVehicleCount = {
        Type = "Choice"
        Choices = [
          {
            Variable = "$.vehicle_count"
            NumericGreaterThan = 50
            Next = "RequireManagerApproval"
          }
        ]
        Default = "AutoApprove"
      }
      RequireManagerApproval = {
        Type = "Task"
        Resource = aws_lambda_function.request_manager_approval.arn
        Next = "WaitForApproval"
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 3
            BackoffRate = 2
          }
        ]
      }
      WaitForApproval = {
        Type = "Wait"
        Seconds = 300
        Next = "CheckApprovalStatus"
      }
      CheckApprovalStatus = {
        Type = "Task"
        Resource = aws_lambda_function.check_approval_status.arn
        Next = "ApprovalDecision"
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 3
            BackoffRate = 2
          }
        ]
      }
      ApprovalDecision = {
        Type = "Choice"
        Choices = [
          {
            Variable = "$.approval_status"
            StringEquals = "APPROVED"
            Next = "ProcessApprovedContract"
          },
          {
            Variable = "$.approval_status"
            StringEquals = "REJECTED"
            Next = "ProcessRejectedContract"
          },
          {
            Variable = "$.approval_status"
            StringEquals = "PENDING"
            Next = "WaitForApproval"
          }
        ]
        Default = "ProcessRejectedContract"
      }
      AutoApprove = {
        Type = "Task"
        Resource = aws_lambda_function.auto_approve_contract.arn
        Next = "ProcessApprovedContract"
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 3
            BackoffRate = 2
          }
        ]
      }
      ProcessApprovedContract = {
        Type = "Task"
        Resource = aws_lambda_function.process_approved_contract.arn
        Next = "SendApprovalNotification"
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 3
            BackoffRate = 2
          }
        ]
      }
      ProcessRejectedContract = {
        Type = "Task"
        Resource = aws_lambda_function.process_rejected_contract.arn
        Next = "SendRejectionNotification"
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 3
            BackoffRate = 2
          }
        ]
      }
      SendApprovalNotification = {
        Type = "Task"
        Resource = aws_lambda_function.send_notification.arn
        End = true
      }
      SendRejectionNotification = {
        Type = "Task"
        Resource = aws_lambda_function.send_notification.arn
        End = true
      }
    }
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-contract-approval-workflow"
    Environment = var.environment
  }
}

# Lambda Functions para el flujo de aprobación

# Validador de contratos
resource "aws_lambda_function" "contract_validator" {
  filename         = "contract_validator.zip"
  function_name    = "${var.project_name}-${var.environment}-contract-validator"
  role            = aws_iam_role.lambda_contract_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      CONTRACTS_TABLE = aws_dynamodb_table.contracts.name
      ENVIRONMENT     = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-contract-validator"
    Environment = var.environment
  }
}

# Solicitar aprobación del manager
resource "aws_lambda_function" "request_manager_approval" {
  filename         = "request_manager_approval.zip"
  function_name    = "${var.project_name}-${var.environment}-request-manager-approval"
  role            = aws_iam_role.lambda_contract_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      CONTRACTS_TABLE          = aws_dynamodb_table.contracts.name
      APPROVALS_TABLE         = aws_dynamodb_table.contract_approvals.name
      SNS_TOPIC_ARN          = aws_sns_topic.manager_approval_requests.arn
      APPROVAL_URL_BASE      = "https://${var.project_name}-${var.environment}.com/approve"
      ENVIRONMENT            = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-request-manager-approval"
    Environment = var.environment
  }
}

# Verificar estado de aprobación
resource "aws_lambda_function" "check_approval_status" {
  filename         = "check_approval_status.zip"
  function_name    = "${var.project_name}-${var.environment}-check-approval-status"
  role            = aws_iam_role.lambda_contract_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      APPROVALS_TABLE = aws_dynamodb_table.contract_approvals.name
      ENVIRONMENT     = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-check-approval-status"
    Environment = var.environment
  }
}

# Auto-aprobar contratos pequeños
resource "aws_lambda_function" "auto_approve_contract" {
  filename         = "auto_approve_contract.zip"
  function_name    = "${var.project_name}-${var.environment}-auto-approve-contract"
  role            = aws_iam_role.lambda_contract_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      CONTRACTS_TABLE = aws_dynamodb_table.contracts.name
      ENVIRONMENT     = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-auto-approve-contract"
    Environment = var.environment
  }
}

# Procesar contrato aprobado
resource "aws_lambda_function" "process_approved_contract" {
  filename         = "process_approved_contract.zip"
  function_name    = "${var.project_name}-${var.environment}-process-approved-contract"
  role            = aws_iam_role.lambda_contract_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 60

  environment {
    variables = {
      CONTRACTS_TABLE    = aws_dynamodb_table.contracts.name
      SIGNATURES_TABLE   = aws_dynamodb_table.electronic_signatures.name
      DOCUSIGN_API_KEY   = var.docusign_api_key
      ENVIRONMENT        = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-process-approved-contract"
    Environment = var.environment
  }
}

# Procesar contrato rechazado
resource "aws_lambda_function" "process_rejected_contract" {
  filename         = "process_rejected_contract.zip"
  function_name    = "${var.project_name}-${var.environment}-process-rejected-contract"
  role            = aws_iam_role.lambda_contract_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      CONTRACTS_TABLE = aws_dynamodb_table.contracts.name
      ENVIRONMENT     = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-process-rejected-contract"
    Environment = var.environment
  }
}

# Enviar notificaciones
resource "aws_lambda_function" "send_notification" {
  filename         = "send_notification.zip"
  function_name    = "${var.project_name}-${var.environment}-contract-notification"
  role            = aws_iam_role.lambda_contract_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.contract_notifications.arn
      SES_FROM_EMAIL = var.notification_email
      ENVIRONMENT    = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-contract-notification"
    Environment = var.environment
  }
}

# API Lambda para gestión de contratos
resource "aws_lambda_function" "contract_management_api" {
  filename         = "contract_management_api.zip"
  function_name    = "${var.project_name}-${var.environment}-contract-management-api"
  role            = aws_iam_role.lambda_contract_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      CONTRACTS_TABLE           = aws_dynamodb_table.contracts.name
      APPROVALS_TABLE          = aws_dynamodb_table.contract_approvals.name
      SIGNATURES_TABLE         = aws_dynamodb_table.electronic_signatures.name
      STEP_FUNCTIONS_ARN       = aws_sfn_state_machine.contract_approval_workflow.arn
      ENVIRONMENT              = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-contract-management-api"
    Environment = var.environment
  }
}

# SNS Topics para notificaciones
resource "aws_sns_topic" "manager_approval_requests" {
  name = "${var.project_name}-${var.environment}-manager-approval-requests"

  tags = {
    Name        = "${var.project_name}-${var.environment}-manager-approval-requests"
    Environment = var.environment
  }
}

resource "aws_sns_topic" "contract_notifications" {
  name = "${var.project_name}-${var.environment}-contract-notifications"

  tags = {
    Name        = "${var.project_name}-${var.environment}-contract-notifications"
    Environment = var.environment
  }
}

# S3 Bucket para documentos de contratos
resource "aws_s3_bucket" "contract_documents" {
  bucket = "${var.project_name}-${var.environment}-contract-documents-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-contract-documents"
    Environment = var.environment
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_versioning" "contract_documents_versioning" {
  bucket = aws_s3_bucket.contract_documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "contract_documents_encryption" {
  bucket = aws_s3_bucket.contract_documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Política de retención para documentos legales
resource "aws_s3_bucket_lifecycle_configuration" "contract_documents_lifecycle" {
  bucket = aws_s3_bucket.contract_documents.id

  rule {
    id     = "contract_retention"
    status = "Enabled"

    # Mantener documentos por 7 años (requisito legal)
    expiration {
      days = 2555  # 7 años
    }

    # Mover a IA después de 90 días
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    # Mover a Glacier después de 1 año
    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
}

# EventBridge Rule para timeouts de aprobación
resource "aws_cloudwatch_event_rule" "approval_timeout" {
  name        = "${var.project_name}-${var.environment}-approval-timeout"
  description = "Detectar aprobaciones pendientes que han expirado"

  schedule_expression = "rate(1 hour)"  # Revisar cada hora

  tags = {
    Name        = "${var.project_name}-${var.environment}-approval-timeout"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "approval_timeout_target" {
  rule      = aws_cloudwatch_event_rule.approval_timeout.name
  target_id = "ApprovalTimeoutLambdaTarget"
  arn       = aws_lambda_function.approval_timeout_handler.arn
}

# Lambda para manejar timeouts de aprobación
resource "aws_lambda_function" "approval_timeout_handler" {
  filename         = "approval_timeout_handler.zip"
  function_name    = "${var.project_name}-${var.environment}-approval-timeout-handler"
  role            = aws_iam_role.lambda_contract_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      APPROVALS_TABLE = aws_dynamodb_table.contract_approvals.name
      CONTRACTS_TABLE = aws_dynamodb_table.contracts.name
      SNS_TOPIC_ARN   = aws_sns_topic.contract_notifications.arn
      TIMEOUT_HOURS   = "72"  # 72 horas para aprobar
      ENVIRONMENT     = var.environment
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-approval-timeout-handler"
    Environment = var.environment
  }
}

resource "aws_lambda_permission" "allow_eventbridge_approval_timeout" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.approval_timeout_handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.approval_timeout.arn
}
