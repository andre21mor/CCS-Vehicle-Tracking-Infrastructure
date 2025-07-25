# IAM Roles y Políticas para el sistema de aprobación de contratos

# Role para Step Functions
resource "aws_iam_role" "step_functions_role" {
  name = "${var.project_name}-${var.environment}-step-functions-contract-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "step_functions_policy" {
  name = "${var.project_name}-${var.environment}-step-functions-contract-policy"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.contract_validator.arn,
          aws_lambda_function.request_manager_approval.arn,
          aws_lambda_function.check_approval_status.arn,
          aws_lambda_function.auto_approve_contract.arn,
          aws_lambda_function.process_approved_contract.arn,
          aws_lambda_function.process_rejected_contract.arn,
          aws_lambda_function.send_notification.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Role para Lambda functions de contratos
resource "aws_iam_role" "lambda_contract_role" {
  name = "${var.project_name}-${var.environment}-lambda-contract-role"

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

resource "aws_iam_role_policy_attachment" "lambda_contract_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_contract_role.name
}

resource "aws_iam_role_policy" "lambda_contract_policy" {
  name = "${var.project_name}-${var.environment}-lambda-contract-policy"
  role = aws_iam_role.lambda_contract_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.contracts.arn,
          aws_dynamodb_table.contract_approvals.arn,
          aws_dynamodb_table.electronic_signatures.arn,
          "${aws_dynamodb_table.contracts.arn}/index/*",
          "${aws_dynamodb_table.contract_approvals.arn}/index/*",
          "${aws_dynamodb_table.electronic_signatures.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          aws_sns_topic.manager_approval_requests.arn,
          aws_sns_topic.contract_notifications.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "ses:FromAddress" = var.notification_email
          }
        }
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
          "states:StartExecution"
        ]
        Resource = aws_sfn_state_machine.contract_approval_workflow.arn
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminListGroupsForUser"
        ]
        Resource = "arn:aws:cognito-idp:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:userpool/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}/${var.environment}/docusign/*"
        ]
      }
    ]
  })
}

# Permisos para que Step Functions invoque Lambda
resource "aws_lambda_permission" "allow_step_functions_contract_validator" {
  statement_id  = "AllowExecutionFromStepFunctions"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.contract_validator.function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.contract_approval_workflow.arn
}

resource "aws_lambda_permission" "allow_step_functions_request_approval" {
  statement_id  = "AllowExecutionFromStepFunctions"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.request_manager_approval.function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.contract_approval_workflow.arn
}

resource "aws_lambda_permission" "allow_step_functions_check_approval" {
  statement_id  = "AllowExecutionFromStepFunctions"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.check_approval_status.function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.contract_approval_workflow.arn
}

resource "aws_lambda_permission" "allow_step_functions_auto_approve" {
  statement_id  = "AllowExecutionFromStepFunctions"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auto_approve_contract.function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.contract_approval_workflow.arn
}

resource "aws_lambda_permission" "allow_step_functions_process_approved" {
  statement_id  = "AllowExecutionFromStepFunctions"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_approved_contract.function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.contract_approval_workflow.arn
}

resource "aws_lambda_permission" "allow_step_functions_process_rejected" {
  statement_id  = "AllowExecutionFromStepFunctions"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_rejected_contract.function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.contract_approval_workflow.arn
}

resource "aws_lambda_permission" "allow_step_functions_send_notification" {
  statement_id  = "AllowExecutionFromStepFunctions"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.send_notification.function_name
  principal     = "states.amazonaws.com"
  source_arn    = aws_sfn_state_machine.contract_approval_workflow.arn
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
