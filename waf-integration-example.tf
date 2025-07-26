# Ejemplo de integración del módulo WAF con la infraestructura existente
# Este archivo muestra cómo integrar WAF con CloudFront

# NOTA: Este es un archivo de ejemplo. Para implementar, agregar al main.tf principal

# 1. Crear el módulo WAF
module "waf" {
  source = "./modules/waf"
  
  project_name = var.project_name
  environment  = "test-70v"
  
  # Configuración básica de seguridad
  rate_limit = 2000  # 2000 requests por IP cada 5 minutos
  
  # Países permitidos (ajustar según necesidades del negocio)
  allowed_countries = [
    "MX",  # México
    "US",  # Estados Unidos
    "CA",  # Canadá
    "BR",  # Brasil
    "AR",  # Argentina
    "CO",  # Colombia
    "PE",  # Perú
    "CL"   # Chile
  ]
  
  # IPs de oficinas/administración (ejemplo - ajustar con IPs reales)
  ip_whitelist = [
    # "203.0.113.0/24",  # Oficina principal (ejemplo)
    # "198.51.100.0/24"  # Oficina secundaria (ejemplo)
  ]
  
  # Configuración de logs
  log_retention_days = 30
  
  # Configuración de alarmas (conectar con SNS existente si está disponible)
  blocked_requests_threshold = 100
  rate_limit_threshold      = 50
  
  # Alarmas - conectar con el sistema de notificaciones existente
  alarm_actions = [
    # aws_sns_topic.vehicle_alerts.arn  # Si existe un tópico SNS
  ]
  
  # Configuración de costos (para ambiente de prueba)
  enable_bot_control     = false  # Evitar costo adicional en pruebas
  enable_shield_advanced = false  # Evitar costo alto en pruebas
  enable_geo_blocking    = false  # Opcional para pruebas
  
  # Tags adicionales
  additional_tags = {
    CostCenter = "RnD"
    TestPhase  = "70-vehicles"
    AutoShutdown = "true"
  }
}

# 2. Actualizar el módulo CloudFront para usar WAF
module "cloudfront" {
  source = "./modules/cloudfront"
  
  project_name = var.project_name
  environment  = "test-70v"
  
  # Integrar WAF con CloudFront
  waf_web_acl_id = module.waf.web_acl_arn
  
  # Resto de configuración existente...
  enable_logging = true
  price_class    = "PriceClass_100"
}

# 3. Outputs adicionales para WAF
output "waf_web_acl_id" {
  description = "ID del Web ACL de WAF"
  value       = module.waf.web_acl_id
}

output "waf_dashboard_url" {
  description = "URL del dashboard de WAF"
  value       = module.waf.waf_dashboard_url
}

output "waf_estimated_cost" {
  description = "Costo estimado mensual de WAF"
  value       = module.waf.estimated_monthly_cost
}

output "waf_configuration_summary" {
  description = "Resumen de configuración WAF"
  value       = module.waf.waf_rules_summary
}

# 4. Ejemplo de configuración para producción (comentado)
/*
module "waf_production" {
  source = "./modules/waf"
  
  project_name = var.project_name
  environment  = "prod"
  
  # Configuración más estricta para producción
  rate_limit = 1000  # Más restrictivo
  
  # Habilitar funciones avanzadas en producción
  enable_bot_control  = true   # Recomendado para prod
  enable_geo_blocking = true   # Bloquear países no permitidos
  
  # IPs de oficinas reales
  ip_whitelist = [
    "203.0.113.0/24",  # Oficina México
    "198.51.100.0/24"  # Oficina US
  ]
  
  # Retención de logs extendida
  log_retention_days = 90
  
  # Alarmas más sensibles
  blocked_requests_threshold = 50
  rate_limit_threshold      = 25
  
  # Notificaciones críticas
  alarm_actions = [
    aws_sns_topic.critical_alerts.arn,
    aws_sns_topic.security_team.arn
  ]
}
*/

# 5. Recursos adicionales recomendados para WAF

# SNS Topic para alertas de seguridad (si no existe)
resource "aws_sns_topic" "waf_security_alerts" {
  name = "${var.project_name}-waf-security-alerts"
  
  tags = {
    Name        = "${var.project_name}-waf-security-alerts"
    Environment = "test-70v"
    Purpose     = "WAF Security Notifications"
  }
}

# Suscripción de email para alertas (ajustar email)
resource "aws_sns_topic_subscription" "waf_email_alerts" {
  topic_arn = aws_sns_topic.waf_security_alerts.arn
  protocol  = "email"
  endpoint  = "security@company.com"  # Cambiar por email real
}

# Dashboard de CloudWatch para WAF (opcional)
resource "aws_cloudwatch_dashboard" "waf_dashboard" {
  dashboard_name = "${var.project_name}-waf-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/WAFV2", "AllowedRequests", "WebACL", module.waf.web_acl_name, "Rule", "ALL", "Region", "CloudFront"],
            [".", "BlockedRequests", ".", ".", ".", ".", ".", "."],
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "WAF Requests Overview"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/WAFV2", "BlockedRequests", "WebACL", module.waf.web_acl_name, "Rule", "RateLimitRule", "Region", "CloudFront"],
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "Rate Limiting Activity"
          period  = 300
        }
      }
    ]
  })
}
