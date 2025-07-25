variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "ID de la VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs de las subnets privadas"
  type        = list(string)
}

variable "database_subnet_group_name" {
  description = "Nombre del grupo de subnets de base de datos"
  type        = string
}

variable "enable_rds" {
  description = "Habilitar RDS Aurora (opcional para datos transaccionales)"
  type        = bool
  default     = false
}
