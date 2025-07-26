# Variables para el módulo WAF
# Vehicle Tracking System

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "vehicle-tracking"
}

variable "environment" {
  description = "Ambiente (dev, test, prod)"
  type        = string
  default     = "test-70v"
}

variable "rate_limit" {
  description = "Límite de requests por IP en 5 minutos"
  type        = number
  default     = 2000
  validation {
    condition     = var.rate_limit >= 100 && var.rate_limit <= 20000000
    error_message = "Rate limit debe estar entre 100 y 20,000,000."
  }
}

variable "allowed_countries" {
  description = "Lista de códigos de países permitidos (ISO 3166-1 alpha-2)"
  type        = list(string)
  default     = ["MX", "US", "CA", "BR", "AR", "CO", "PE", "CL"]
}

variable "ip_whitelist" {
  description = "Lista de IPs o rangos CIDR permitidos (oficinas, administración)"
  type        = list(string)
  default     = []
  # Ejemplo: ["192.168.1.0/24", "10.0.0.0/8", "203.0.113.0/24"]
}

variable "ip_blacklist" {
  description = "Lista de IPs o rangos CIDR bloqueados"
  type        = list(string)
  default     = []
  # Ejemplo: ["198.51.100.0/24", "203.0.113.42/32"]
}

variable "enable_geo_blocking" {
  description = "Habilitar bloqueo geográfico (solo países permitidos)"
  type        = bool
  default     = false
}

variable "enable_bot_control" {
  description = "Habilitar AWS Bot Control (costo adicional ~$1/millón requests)"
  type        = bool
  default     = false
}

variable "common_rule_exclusions" {
  description = "Lista de reglas del Common Rule Set a excluir"
  type        = list(string)
  default     = []
  # Ejemplo: ["SizeRestrictions_BODY", "GenericRFI_BODY"]
}

variable "log_retention_days" {
  description = "Días de retención para logs de WAF en CloudWatch"
  type        = number
  default     = 30
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention debe ser un valor válido de CloudWatch."
  }
}

variable "blocked_requests_threshold" {
  description = "Umbral de requests bloqueadas para alarma CloudWatch"
  type        = number
  default     = 100
}

variable "rate_limit_threshold" {
  description = "Umbral de rate limiting para alarma CloudWatch"
  type        = number
  default     = 50
}

variable "alarm_actions" {
  description = "Lista de ARNs de SNS para notificaciones de alarmas"
  type        = list(string)
  default     = []
}

# Variables para configuración avanzada
variable "custom_rules" {
  description = "Reglas personalizadas adicionales"
  type = list(object({
    name     = string
    priority = number
    action   = string # "allow", "block", "count"
    statement = object({
      type = string # "ip", "geo", "size", "sqli", "xss"
      # Configuración específica según el tipo
      config = map(any)
    })
  }))
  default = []
}

variable "sampling_rate" {
  description = "Porcentaje de requests a samplear para logs (0-100)"
  type        = number
  default     = 100
  validation {
    condition     = var.sampling_rate >= 0 && var.sampling_rate <= 100
    error_message = "Sampling rate debe estar entre 0 y 100."
  }
}

# Variables para integración con otros servicios
variable "cloudfront_distribution_id" {
  description = "ID de la distribución CloudFront (se pasa desde el módulo CloudFront)"
  type        = string
  default     = ""
}

variable "enable_shield_advanced" {
  description = "Habilitar AWS Shield Advanced (costo adicional $3000/mes)"
  type        = bool
  default     = false
}

# Variables para configuración de métricas
variable "enable_detailed_metrics" {
  description = "Habilitar métricas detalladas en CloudWatch"
  type        = bool
  default     = true
}

variable "metric_filters" {
  description = "Filtros personalizados para métricas"
  type = list(object({
    name           = string
    filter_pattern = string
    metric_name    = string
    namespace      = string
    value          = string
  }))
  default = []
}

# Variables para configuración de costos
variable "enable_cost_optimization" {
  description = "Habilitar optimizaciones de costo (puede reducir funcionalidad)"
  type        = bool
  default     = true
}

variable "request_inspection_limit" {
  description = "Límite de inspección de requests (para optimizar costos)"
  type        = number
  default     = 1000000
}

# Tags adicionales
variable "additional_tags" {
  description = "Tags adicionales para recursos WAF"
  type        = map(string)
  default     = {}
}
