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

variable "user_pool_id" {
  description = "ID del User Pool de Cognito"
  type        = string
}

variable "api_gateway_id" {
  description = "ID del API Gateway principal"
  type        = string
}

variable "api_gateway_root_resource_id" {
  description = "ID del recurso raíz del API Gateway"
  type        = string
}

variable "cognito_authorizer_id" {
  description = "ID del autorizador de Cognito"
  type        = string
}
