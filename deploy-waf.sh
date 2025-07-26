#!/bin/bash

# Script de deployment para módulo WAF
# Vehicle Tracking Infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info "🛡️  Iniciando deployment del módulo WAF"
echo "=============================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "main.tf" ]; then
    print_error "No se encontró main.tf. Ejecutar desde el directorio raíz del proyecto."
    exit 1
fi

# Verificar que el módulo WAF existe
if [ ! -d "modules/waf" ]; then
    print_error "Módulo WAF no encontrado en modules/waf/"
    exit 1
fi

print_info "Verificando configuración de Terraform..."

# Verificar versión de Terraform
TERRAFORM_VERSION=$(terraform version -json | jq -r '.terraform_version' 2>/dev/null || echo "unknown")
print_info "Versión de Terraform: $TERRAFORM_VERSION"

# Verificar AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI no está instalado"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
print_info "Cuenta AWS: $AWS_ACCOUNT"
print_info "Región AWS: $AWS_REGION"

# Verificar que CloudFront existe (prerequisito)
print_info "Verificando infraestructura existente..."

CLOUDFRONT_DISTRIBUTIONS=$(aws cloudfront list-distributions --query 'DistributionList.Items[?starts_with(Comment, `Vehicle Tracking`)].Id' --output text 2>/dev/null || echo "")

if [ -z "$CLOUDFRONT_DISTRIBUTIONS" ]; then
    print_warning "No se encontraron distribuciones CloudFront del proyecto"
    print_warning "Asegúrate de que la infraestructura base esté desplegada"
fi

# Mostrar configuración propuesta
print_info "📋 Configuración WAF propuesta:"
echo "  • Rate Limit: 2000 requests/5min por IP"
echo "  • Países permitidos: MX, US, CA, BR, AR, CO, PE, CL"
echo "  • AWS Managed Rules: Habilitadas"
echo "  • Bot Control: Deshabilitado (ahorro de costos)"
echo "  • Geo Blocking: Deshabilitado (modo permisivo)"
echo "  • Logs: 30 días de retención"
echo "  • Costo estimado: ~$1.30/mes"

echo ""
read -p "¿Continuar con el deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Deployment cancelado por el usuario"
    exit 0
fi

# Crear backup de configuración actual
print_info "Creando backup de configuración..."
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp main.tf "$BACKUP_DIR/" 2>/dev/null || true
cp terraform.tfstate "$BACKUP_DIR/" 2>/dev/null || true
print_success "Backup creado en $BACKUP_DIR"

# Agregar configuración WAF al main.tf si no existe
if ! grep -q "module.*waf" main.tf; then
    print_info "Agregando configuración WAF a main.tf..."
    
    cat >> main.tf << 'EOF'

# Módulo WAF para protección CloudFront
module "waf" {
  source = "./modules/waf"
  
  project_name = var.project_name
  environment  = "test-70v"
  
  # Configuración básica de seguridad
  rate_limit = 2000
  
  # Países permitidos
  allowed_countries = ["MX", "US", "CA", "BR", "AR", "CO", "PE", "CL"]
  
  # Configuración de logs
  log_retention_days = 30
  
  # Configuración de alarmas
  blocked_requests_threshold = 100
  rate_limit_threshold      = 50
  
  # Configuración de costos (ambiente de prueba)
  enable_bot_control     = false
  enable_shield_advanced = false
  enable_geo_blocking    = false
  
  # Tags adicionales
  additional_tags = {
    CostCenter   = "RnD"
    TestPhase    = "70-vehicles"
    AutoShutdown = "true"
  }
}

# Outputs para WAF
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
EOF

    print_success "Configuración WAF agregada a main.tf"
else
    print_info "Configuración WAF ya existe en main.tf"
fi

# Actualizar módulo CloudFront si es necesario
if ! grep -q "waf_web_acl_id" modules/cloudfront/main.tf; then
    print_warning "El módulo CloudFront necesita actualización para integrar WAF"
    print_info "Esto se puede hacer manualmente después del deployment"
fi

# Terraform init
print_info "Inicializando Terraform..."
terraform init -upgrade

# Terraform validate
print_info "Validando configuración..."
if ! terraform validate; then
    print_error "Validación de Terraform falló"
    exit 1
fi

# Terraform plan
print_info "Generando plan de deployment..."
terraform plan -out=waf-deployment.tfplan

echo ""
print_warning "⚠️  REVISIÓN FINAL"
print_warning "El plan anterior muestra los recursos que se crearán."
print_warning "Recursos principales:"
print_warning "  • aws_wafv2_web_acl"
print_warning "  • aws_cloudwatch_log_group"
print_warning "  • aws_cloudwatch_metric_alarm (2)"
print_warning "  • aws_wafv2_web_acl_logging_configuration"

echo ""
read -p "¿Aplicar los cambios? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Deployment cancelado. Plan guardado en waf-deployment.tfplan"
    exit 0
fi

# Terraform apply
print_info "Aplicando cambios..."
if terraform apply waf-deployment.tfplan; then
    print_success "✅ Deployment de WAF completado exitosamente!"
else
    print_error "❌ Error durante el deployment"
    exit 1
fi

# Limpiar plan file
rm -f waf-deployment.tfplan

# Mostrar información post-deployment
print_info "📊 Información post-deployment:"

# Obtener outputs
WAF_ID=$(terraform output -raw waf_web_acl_id 2>/dev/null || echo "N/A")
WAF_DASHBOARD=$(terraform output -raw waf_dashboard_url 2>/dev/null || echo "N/A")

echo "  • WAF Web ACL ID: $WAF_ID"
echo "  • Dashboard URL: $WAF_DASHBOARD"

# Verificar que WAF está activo
print_info "Verificando estado de WAF..."
if [ "$WAF_ID" != "N/A" ]; then
    WAF_STATUS=$(aws wafv2 get-web-acl --scope CLOUDFRONT --id "$WAF_ID" --query 'WebACL.Name' --output text 2>/dev/null || echo "Error")
    if [ "$WAF_STATUS" != "Error" ]; then
        print_success "WAF está activo: $WAF_STATUS"
    else
        print_warning "No se pudo verificar el estado de WAF"
    fi
fi

# Instrucciones post-deployment
print_info "📋 Próximos pasos:"
echo "  1. Integrar WAF con CloudFront (si no se hizo automáticamente)"
echo "  2. Configurar notificaciones SNS para alarmas"
echo "  3. Ajustar IPs de whitelist según necesidades"
echo "  4. Monitorear métricas en CloudWatch"
echo "  5. Revisar logs de WAF para ajustar reglas"

print_info "🔗 Enlaces útiles:"
echo "  • AWS Console WAF: https://console.aws.amazon.com/wafv2/"
echo "  • CloudWatch Metrics: https://console.aws.amazon.com/cloudwatch/"
echo "  • Documentación: modules/waf/README.md"

print_success "🎉 Deployment de WAF completado!"
print_info "Costo estimado: ~$1.30/mes para el ambiente de prueba"

# Opcional: Crear invalidación de CloudFront si existe
if [ -n "$CLOUDFRONT_DISTRIBUTIONS" ]; then
    print_info "Creando invalidación de CloudFront..."
    for dist_id in $CLOUDFRONT_DISTRIBUTIONS; do
        aws cloudfront create-invalidation --distribution-id "$dist_id" --paths "/*" >/dev/null 2>&1 || true
        print_info "Invalidación creada para distribución: $dist_id"
    done
fi

echo ""
print_success "✅ Proceso completado exitosamente!"
