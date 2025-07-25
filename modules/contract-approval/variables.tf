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

variable "docusign_api_key" {
  description = "API Key de DocuSign para firma electrónica (DEPRECATED - usar integration_key)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "docusign_integration_key" {
  description = "Integration Key de DocuSign"
  type        = string
  sensitive   = true
  default     = ""
}

variable "docusign_user_id" {
  description = "User ID de DocuSign"
  type        = string
  sensitive   = true
  default     = ""
}

variable "docusign_account_id" {
  description = "Account ID de DocuSign"
  type        = string
  sensitive   = true
  default     = ""
}

variable "docusign_private_key" {
  description = "Private Key para JWT authentication con DocuSign"
  type        = string
  sensitive   = true
  default     = ""
}

variable "docusign_base_url" {
  description = "Base URL de DocuSign API"
  type        = string
  default     = "https://demo.docusign.net/restapi"
}

variable "notification_email" {
  description = "Email para envío de notificaciones"
  type        = string
  default     = "notifications@vehicletracking.com"
}
