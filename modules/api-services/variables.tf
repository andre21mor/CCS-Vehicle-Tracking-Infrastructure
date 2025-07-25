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

variable "public_subnet_ids" {
  description = "IDs de las subnets públicas"
  type        = list(string)
}

variable "user_pool_id" {
  description = "ID del Cognito User Pool"
  type        = string
  default     = ""
}

variable "contract_approval_module" {
  description = "Dependencia del módulo de aprobación de contratos"
  type        = any
  default     = null
}
