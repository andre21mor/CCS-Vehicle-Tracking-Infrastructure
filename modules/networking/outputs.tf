output "vpc_id" {
  description = "ID de la VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block de la VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs de las subnets públicas"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs de las subnets privadas"
  value       = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  description = "IDs de las subnets de base de datos"
  value       = aws_subnet.database[*].id
}

output "database_subnet_group_name" {
  description = "Nombre del grupo de subnets de base de datos"
  value       = aws_db_subnet_group.main.name
}

output "alb_security_group_id" {
  description = "ID del security group del ALB"
  value       = aws_security_group.alb.id
}

output "app_security_group_id" {
  description = "ID del security group de aplicaciones"
  value       = aws_security_group.app.id
}

output "database_security_group_id" {
  description = "ID del security group de base de datos"
  value       = aws_security_group.database.id
}

output "internet_gateway_id" {
  description = "ID del Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_ids" {
  description = "IDs de los NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}
