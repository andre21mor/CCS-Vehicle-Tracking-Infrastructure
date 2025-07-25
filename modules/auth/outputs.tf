output "client_user_pool_id" {
  description = "ID del User Pool de clientes"
  value       = aws_cognito_user_pool.client_pool.id
}

output "client_user_pool_arn" {
  description = "ARN del User Pool de clientes"
  value       = aws_cognito_user_pool.client_pool.arn
}

output "driver_user_pool_id" {
  description = "ID del User Pool de conductores"
  value       = aws_cognito_user_pool.driver_pool.id
}

output "driver_user_pool_arn" {
  description = "ARN del User Pool de conductores"
  value       = aws_cognito_user_pool.driver_pool.arn
}

output "web_client_id" {
  description = "ID del cliente web"
  value       = aws_cognito_user_pool_client.web_client.id
}

output "mobile_client_id" {
  description = "ID del cliente móvil"
  value       = aws_cognito_user_pool_client.mobile_client.id
}

output "driver_client_id" {
  description = "ID del cliente de conductores"
  value       = aws_cognito_user_pool_client.driver_client.id
}

output "identity_pool_id" {
  description = "ID del Identity Pool"
  value       = aws_cognito_identity_pool.main.id
}

output "authenticated_role_arn" {
  description = "ARN del rol para usuarios autenticados"
  value       = aws_iam_role.authenticated_role.arn
}

output "cognito_domain" {
  description = "Dominio de Cognito"
  value       = aws_cognito_user_pool_domain.main.domain
}

output "cognito_domain_url" {
  description = "URL completa del dominio de Cognito"
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
}
