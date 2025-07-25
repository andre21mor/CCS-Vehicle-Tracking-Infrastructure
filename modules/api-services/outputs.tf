output "api_gateway_url" {
  description = "URL base de la API Gateway"
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.environment}"
}

output "api_gateway_id" {
  description = "ID de la API Gateway"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_gateway_arn" {
  description = "ARN de la API Gateway"
  value       = aws_api_gateway_rest_api.main.arn
}

output "cognito_authorizer_id" {
  description = "ID del autorizador de Cognito"
  value       = aws_api_gateway_authorizer.cognito_authorizer.id
}

output "api_gateway_root_resource_id" {
  description = "ID del recurso raíz de la API Gateway"
  value       = aws_api_gateway_rest_api.main.root_resource_id
}

output "lambda_functions" {
  description = "ARNs de las funciones Lambda de la API"
  value = {
    vehicle_management = aws_lambda_function.vehicle_management.arn
    telemetry_api     = aws_lambda_function.telemetry_api.arn
    fleet_dashboard   = aws_lambda_function.fleet_dashboard.arn
    reports_api       = aws_lambda_function.reports_api.arn
    notifications_api = aws_lambda_function.notifications_api.arn
  }
}

output "reports_bucket" {
  description = "Nombre del bucket S3 para reportes"
  value       = aws_s3_bucket.reports.bucket
}

output "api_endpoints" {
  description = "Endpoints disponibles de la API"
  value = {
    base_url = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.environment}"
    endpoints = {
      vehicles           = "/vehicles"
      vehicle_by_id      = "/vehicles/{vehicleId}"
      vehicle_telemetry  = "/vehicles/{vehicleId}/telemetry"
      vehicle_location   = "/vehicles/{vehicleId}/location"
      vehicle_alerts     = "/vehicles/{vehicleId}/alerts"
      vehicle_video      = "/vehicles/{vehicleId}/video"
      fleet_dashboard    = "/fleet/dashboard"
      reports           = "/reports"
      notifications     = "/notifications"
      payments          = "/payments"
    }
  }
}
