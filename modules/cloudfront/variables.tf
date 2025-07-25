# Variables para el módulo CloudFront

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
}

variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
}

variable "region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "enable_logging" {
  description = "Habilitar logging de CloudFront"
  type        = bool
  default     = true
}

variable "price_class" {
  description = "Clase de precio para CloudFront"
  type        = string
  default     = "PriceClass_100"
  validation {
    condition = contains([
      "PriceClass_All",
      "PriceClass_200",
      "PriceClass_100"
    ], var.price_class)
    error_message = "Price class must be PriceClass_All, PriceClass_200, or PriceClass_100."
  }
}

variable "custom_domain" {
  description = "Dominio personalizado para CloudFront (opcional)"
  type        = string
  default     = ""
}

variable "ssl_certificate_arn" {
  description = "ARN del certificado SSL para dominio personalizado"
  type        = string
  default     = ""
}

variable "allowed_countries" {
  description = "Lista de países permitidos (código ISO)"
  type        = list(string)
  default     = []
}

variable "blocked_countries" {
  description = "Lista de países bloqueados (código ISO)"
  type        = list(string)
  default     = []
}
