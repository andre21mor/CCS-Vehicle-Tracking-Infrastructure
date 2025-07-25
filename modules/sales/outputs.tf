output "sales_clients_table_name" {
  description = "Nombre de la tabla de clientes de ventas"
  value       = aws_dynamodb_table.sales_clients.name
}

output "sales_inventory_table_name" {
  description = "Nombre de la tabla de inventario de ventas"
  value       = aws_dynamodb_table.sales_inventory.name
}

output "sales_contracts_table_name" {
  description = "Nombre de la tabla de contratos de ventas"
  value       = aws_dynamodb_table.sales_contracts.name
}

output "sales_quotations_table_name" {
  description = "Nombre de la tabla de cotizaciones"
  value       = aws_dynamodb_table.sales_quotations.name
}

output "sales_clients_lambda_arn" {
  description = "ARN de la función Lambda de clientes"
  value       = aws_lambda_function.sales_clients_api.arn
}

output "sales_inventory_lambda_arn" {
  description = "ARN de la función Lambda de inventario"
  value       = aws_lambda_function.sales_inventory_api.arn
}

output "sales_contracts_lambda_arn" {
  description = "ARN de la función Lambda de contratos"
  value       = aws_lambda_function.sales_contracts_api.arn
}

output "sales_dashboard_lambda_arn" {
  description = "ARN de la función Lambda de dashboard"
  value       = aws_lambda_function.sales_dashboard_api.arn
}

output "sales_api_endpoints" {
  description = "Endpoints de la API de ventas"
  value = {
    clients    = "/sales/clients"
    inventory  = "/sales/inventory"
    contracts  = "/sales/contracts"
    dashboard  = "/sales/dashboard"
  }
}
