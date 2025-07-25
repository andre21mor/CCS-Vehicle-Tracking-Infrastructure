output "step_functions_arn" {
  description = "ARN de la State Machine de Step Functions"
  value       = aws_sfn_state_machine.contract_approval_workflow.arn
}

output "contracts_table_name" {
  description = "Nombre de la tabla de contratos"
  value       = aws_dynamodb_table.contracts.name
}

output "contract_approvals_table_name" {
  description = "Nombre de la tabla de aprobaciones"
  value       = aws_dynamodb_table.contract_approvals.name
}

output "electronic_signatures_table_name" {
  description = "Nombre de la tabla de firmas electrónicas"
  value       = aws_dynamodb_table.electronic_signatures.name
}

output "contract_documents_bucket" {
  description = "Bucket S3 para documentos de contratos"
  value       = aws_s3_bucket.contract_documents.bucket
}

output "manager_approval_topic_arn" {
  description = "ARN del topic SNS para solicitudes de aprobación"
  value       = aws_sns_topic.manager_approval_requests.arn
}

output "contract_notifications_topic_arn" {
  description = "ARN del topic SNS para notificaciones de contratos"
  value       = aws_sns_topic.contract_notifications.arn
}

output "contract_management_api_arn" {
  description = "ARN de la función Lambda para API de gestión de contratos"
  value       = aws_lambda_function.contract_management_api.arn
}

output "approval_workflow_info" {
  description = "Información del flujo de aprobación"
  value = {
    state_machine_arn = aws_sfn_state_machine.contract_approval_workflow.arn
    vehicle_threshold = 50
    approval_timeout_hours = 72
    auto_approve_limit = 50
  }
}
