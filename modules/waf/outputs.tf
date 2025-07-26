# Outputs del módulo WAF
# Vehicle Tracking System

output "web_acl_id" {
  description = "ID del Web ACL de WAF"
  value       = aws_wafv2_web_acl.vehicle_tracking_waf.id
}

output "web_acl_arn" {
  description = "ARN del Web ACL de WAF"
  value       = aws_wafv2_web_acl.vehicle_tracking_waf.arn
}

output "web_acl_name" {
  description = "Nombre del Web ACL de WAF"
  value       = aws_wafv2_web_acl.vehicle_tracking_waf.name
}

output "web_acl_capacity" {
  description = "Capacidad utilizada por el Web ACL"
  value       = aws_wafv2_web_acl.vehicle_tracking_waf.capacity
}

output "ip_whitelist_arn" {
  description = "ARN del IP Set de whitelist"
  value       = length(aws_wafv2_ip_set.ip_whitelist) > 0 ? aws_wafv2_ip_set.ip_whitelist[0].arn : null
}

output "ip_blacklist_arn" {
  description = "ARN del IP Set de blacklist"
  value       = length(aws_wafv2_ip_set.ip_blacklist) > 0 ? aws_wafv2_ip_set.ip_blacklist[0].arn : null
}

output "log_group_name" {
  description = "Nombre del CloudWatch Log Group para WAF"
  value       = aws_cloudwatch_log_group.waf_log_group.name
}

output "log_group_arn" {
  description = "ARN del CloudWatch Log Group para WAF"
  value       = aws_cloudwatch_log_group.waf_log_group.arn
}

output "blocked_requests_alarm_arn" {
  description = "ARN de la alarma de requests bloqueadas"
  value       = aws_cloudwatch_metric_alarm.waf_blocked_requests.arn
}

output "rate_limit_alarm_arn" {
  description = "ARN de la alarma de rate limiting"
  value       = aws_cloudwatch_metric_alarm.waf_rate_limit_triggered.arn
}

# Outputs para integración con CloudFront
output "cloudfront_web_acl_id" {
  description = "ID del Web ACL para asociar con CloudFront (formato requerido)"
  value       = aws_wafv2_web_acl.vehicle_tracking_waf.arn
}

# Outputs para monitoreo y debugging
output "waf_rules_summary" {
  description = "Resumen de reglas configuradas en WAF"
  value = {
    rate_limit_enabled     = true
    common_rules_enabled   = true
    sqli_protection       = true
    xss_protection        = true
    ip_reputation_enabled = true
    bot_control_enabled   = var.enable_bot_control
    geo_blocking_enabled  = var.enable_geo_blocking
    custom_whitelist      = length(var.ip_whitelist) > 0
    custom_blacklist      = length(var.ip_blacklist) > 0
  }
}

output "waf_configuration" {
  description = "Configuración actual de WAF"
  value = {
    rate_limit           = var.rate_limit
    allowed_countries    = var.allowed_countries
    log_retention_days   = var.log_retention_days
    sampling_rate        = var.sampling_rate
    cost_optimization    = var.enable_cost_optimization
  }
}

# Outputs para métricas y costos
output "estimated_monthly_cost" {
  description = "Costo estimado mensual de WAF (USD)"
  value = {
    base_web_acl     = 1.00  # $1.00 por Web ACL por mes
    rule_evaluations = "Variable según tráfico (~$0.60 por millón de requests)"
    bot_control      = var.enable_bot_control ? 10.00 : 0.00  # $10.00 por millón si está habilitado
    shield_advanced  = var.enable_shield_advanced ? 3000.00 : 0.00
    total_fixed      = var.enable_bot_control ? (var.enable_shield_advanced ? 3011.00 : 11.00) : (var.enable_shield_advanced ? 3001.00 : 1.00)
  }
}

# Outputs para troubleshooting
output "waf_dashboard_url" {
  description = "URL del dashboard de WAF en AWS Console"
  value       = "https://console.aws.amazon.com/wafv2/homev2/web-acl/${aws_wafv2_web_acl.vehicle_tracking_waf.name}/${aws_wafv2_web_acl.vehicle_tracking_waf.id}/overview?region=global"
}

output "cloudwatch_dashboard_url" {
  description = "URL del dashboard de CloudWatch para métricas WAF"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=${var.project_name}-${var.environment}-waf"
}

# Outputs para integración con otros módulos
output "waf_tags" {
  description = "Tags aplicadas a recursos WAF"
  value = merge(
    {
      Name        = "${var.project_name}-${var.environment}-waf"
      Environment = var.environment
      Purpose     = "CloudFront Protection"
      Project     = var.project_name
    },
    var.additional_tags
  )
}

# Output para validación de configuración
output "waf_validation" {
  description = "Validación de configuración WAF"
  value = {
    web_acl_created           = aws_wafv2_web_acl.vehicle_tracking_waf.id != ""
    logging_configured        = aws_wafv2_web_acl_logging_configuration.waf_logging.resource_arn != ""
    alarms_configured         = aws_cloudwatch_metric_alarm.waf_blocked_requests.alarm_name != ""
    ip_sets_configured        = length(var.ip_whitelist) > 0 || length(var.ip_blacklist) > 0
    geo_restrictions_active   = var.enable_geo_blocking
    advanced_features_enabled = var.enable_bot_control || var.enable_shield_advanced
  }
}
