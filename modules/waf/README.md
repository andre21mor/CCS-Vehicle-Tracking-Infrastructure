# 🛡️ WAF Module - Vehicle Tracking System

## 📋 Overview

Este módulo implementa AWS WAF v2 para proteger la distribución CloudFront del sistema Vehicle Tracking. Proporciona protección contra ataques comunes, rate limiting, y capacidades de monitoreo avanzadas.

## 🎯 Características Principales

### 🔒 **Protecciones Implementadas**
- **Rate Limiting**: Protección contra DDoS (configurable)
- **AWS Managed Rules**: Core Rule Set, Known Bad Inputs, SQL Injection
- **IP Reputation**: Lista de IPs maliciosas de Amazon
- **Geographic Filtering**: Bloqueo por países (opcional)
- **Custom IP Lists**: Whitelist y blacklist personalizadas
- **Bot Control**: Protección avanzada contra bots (opcional)

### 📊 **Monitoreo y Alertas**
- **CloudWatch Logs**: Logging completo de requests
- **Métricas Detalladas**: Requests bloqueadas, rate limiting
- **Alarmas Automáticas**: Notificaciones por umbrales
- **Dashboard Integration**: URLs pre-configuradas

### 💰 **Optimización de Costos**
- **Configuración Flexible**: Habilitar/deshabilitar funciones costosas
- **Sampling Configurable**: Control de volumen de logs
- **Estimación de Costos**: Outputs con costos estimados

## 🚀 Uso Básico

```hcl
module "waf" {
  source = "./modules/waf"
  
  project_name = var.project_name
  environment  = var.environment
  
  # Configuración básica
  rate_limit        = 2000
  allowed_countries = ["MX", "US", "CA"]
  
  # IPs de oficina (opcional)
  ip_whitelist = [
    "203.0.113.0/24",  # Oficina principal
    "198.51.100.0/24"  # Oficina secundaria
  ]
  
  # Configuración de alarmas
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

## ⚙️ Configuración Avanzada

### 🌍 **Configuración Geográfica**
```hcl
module "waf" {
  source = "./modules/waf"
  
  # Habilitar bloqueo geográfico
  enable_geo_blocking = true
  allowed_countries   = ["MX", "US", "CA", "BR", "AR"]
}
```

### 🤖 **Bot Control (Costo Adicional)**
```hcl
module "waf" {
  source = "./modules/waf"
  
  # Habilitar Bot Control (~$10/millón requests)
  enable_bot_control = true
}
```

### 🛡️ **Shield Advanced (Costo Alto)**
```hcl
module "waf" {
  source = "./modules/waf"
  
  # Habilitar Shield Advanced ($3000/mes)
  enable_shield_advanced = true
}
```

## 📊 Variables Principales

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `rate_limit` | number | 2000 | Requests por IP en 5 minutos |
| `allowed_countries` | list(string) | ["MX","US","CA"...] | Países permitidos |
| `ip_whitelist` | list(string) | [] | IPs siempre permitidas |
| `ip_blacklist` | list(string) | [] | IPs siempre bloqueadas |
| `enable_geo_blocking` | bool | false | Bloquear países no permitidos |
| `enable_bot_control` | bool | false | Protección avanzada contra bots |
| `log_retention_days` | number | 30 | Retención de logs |

## 📤 Outputs Importantes

| Output | Descripción |
|--------|-------------|
| `web_acl_arn` | ARN para asociar con CloudFront |
| `web_acl_id` | ID del Web ACL |
| `estimated_monthly_cost` | Costo estimado mensual |
| `waf_dashboard_url` | URL del dashboard AWS |

## 🔗 Integración con CloudFront

Para integrar con el módulo CloudFront existente:

```hcl
# En modules/cloudfront/main.tf
resource "aws_cloudfront_distribution" "web_interface" {
  # ... configuración existente ...
  
  web_acl_id = var.waf_web_acl_id  # Pasar desde el módulo WAF
  
  # ... resto de configuración ...
}
```

## 💰 Análisis de Costos

### **Costos Base (Mensual)**
- **Web ACL**: $1.00/mes
- **Rule Evaluations**: ~$0.60 por millón de requests
- **CloudWatch Logs**: ~$0.50 por GB

### **Costos Opcionales**
- **Bot Control**: $10.00 por millón de requests
- **Shield Advanced**: $3,000.00/mes

### **Estimación para Vehicle Tracking (70 vehículos)**
- **Tráfico estimado**: ~500K requests/mes
- **Costo base**: ~$1.30/mes
- **Con Bot Control**: ~$6.30/mes
- **Total recomendado**: $1.30/mes

## 🔍 Monitoreo y Troubleshooting

### **CloudWatch Métricas Clave**
- `AllowedRequests`: Requests permitidas
- `BlockedRequests`: Requests bloqueadas
- `CountedRequests`: Requests contadas (modo count)

### **Alarmas Configuradas**
- **Blocked Requests**: >100 requests bloqueadas en 5 min
- **Rate Limiting**: >50 IPs bloqueadas por rate limit

### **Logs de WAF**
```bash
# Ver logs en CloudWatch
aws logs filter-log-events \
  --log-group-name "/aws/wafv2/vehicle-tracking-test-70v" \
  --start-time $(date -d '1 hour ago' +%s)000
```

## 🛠️ Comandos Útiles

### **Verificar Estado de WAF**
```bash
# Listar Web ACLs
aws wafv2 list-web-acls --scope CLOUDFRONT

# Ver detalles del Web ACL
aws wafv2 get-web-acl --scope CLOUDFRONT --id <web-acl-id>
```

### **Gestionar IP Sets**
```bash
# Actualizar IP whitelist
aws wafv2 update-ip-set \
  --scope CLOUDFRONT \
  --id <ip-set-id> \
  --addresses "203.0.113.0/24,198.51.100.0/24"
```

### **Ver Métricas**
```bash
# Requests bloqueadas en la última hora
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name BlockedRequests \
  --dimensions Name=WebACL,Value=vehicle-tracking-test-70v-waf \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## 🔧 Configuración de Producción

### **Configuración Recomendada para Producción**
```hcl
module "waf" {
  source = "./modules/waf"
  
  project_name = "vehicle-tracking"
  environment  = "prod"
  
  # Configuración de seguridad estricta
  rate_limit           = 1000  # Más restrictivo
  enable_geo_blocking  = true
  enable_bot_control   = true  # Recomendado para prod
  
  # IPs de oficinas
  ip_whitelist = [
    "203.0.113.0/24",  # Oficina México
    "198.51.100.0/24"  # Oficina US
  ]
  
  # Países permitidos (ajustar según mercado)
  allowed_countries = ["MX", "US", "CA"]
  
  # Retención de logs extendida
  log_retention_days = 90
  
  # Alarmas críticas
  blocked_requests_threshold = 50
  rate_limit_threshold      = 25
  
  alarm_actions = [
    aws_sns_topic.critical_alerts.arn,
    aws_sns_topic.security_team.arn
  ]
}
```

## 📚 Referencias

- [AWS WAF Developer Guide](https://docs.aws.amazon.com/waf/)
- [WAF Pricing](https://aws.amazon.com/waf/pricing/)
- [CloudFront + WAF Integration](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-awswaf.html)
- [WAF Security Best Practices](https://docs.aws.amazon.com/waf/latest/developerguide/security-best-practices.html)

## 🆘 Soporte

Para problemas con el módulo WAF:
1. Verificar logs en CloudWatch
2. Revisar métricas de WAF
3. Consultar alarmas configuradas
4. Validar configuración de reglas

---

**Creado por**: Amazon Q CloudOps Assistant  
**Fecha**: 26 de Julio, 2025  
**Versión**: 1.0  
**Compatibilidad**: Terraform >= 1.0, AWS Provider >= 5.0
