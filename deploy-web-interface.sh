#!/bin/bash

# Script para desplegar la interfaz web a CloudFront
# Vehicle Tracking System

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Desplegando Interfaz Web a CloudFront${NC}"
echo "=============================================="

# Verificar que Terraform esté disponible
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Error: Terraform no está instalado${NC}"
    exit 1
fi

# Verificar que AWS CLI esté configurado
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Error: AWS CLI no está configurado correctamente${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Herramientas verificadas${NC}"

# Navegar al directorio de Terraform
cd /home/labuser/vehicle-tracking-infrastructure

# Inicializar Terraform si es necesario
echo -e "${YELLOW}📦 Inicializando Terraform...${NC}"
export PATH=$HOME/bin:$PATH
terraform init -upgrade

# Planificar el despliegue
echo -e "${YELLOW}📋 Planificando despliegue de CloudFront...${NC}"
terraform plan -target=module.cloudfront_test

# Aplicar cambios
echo -e "${YELLOW}🚀 Desplegando CloudFront...${NC}"
terraform apply -target=module.cloudfront_test -auto-approve

# Obtener información de la distribución
echo -e "${BLUE}📊 Obteniendo información de CloudFront...${NC}"
CLOUDFRONT_URL=$(terraform output -raw web_interface_url 2>/dev/null || echo "No disponible")
DISTRIBUTION_ID=$(terraform output -raw web_interface_info 2>/dev/null | grep -o '"cloudfront_distribution_id":"[^"]*"' | cut -d'"' -f4 || echo "No disponible")
S3_BUCKET=$(terraform output -raw web_interface_info 2>/dev/null | grep -o '"s3_bucket_name":"[^"]*"' | cut -d'"' -f4 || echo "No disponible")

echo -e "\n${GREEN}✅ Despliegue completado exitosamente${NC}"
echo "=========================================="
echo -e "${BLUE}🌐 URL de la Interfaz Web:${NC} $CLOUDFRONT_URL"
echo -e "${BLUE}📦 Distribution ID:${NC} $DISTRIBUTION_ID"
echo -e "${BLUE}🪣 S3 Bucket:${NC} $S3_BUCKET"

# Verificar el estado de la distribución
if [ "$DISTRIBUTION_ID" != "No disponible" ]; then
    echo -e "\n${YELLOW}⏳ Verificando estado de la distribución...${NC}"
    STATUS=$(aws cloudfront get-distribution --id "$DISTRIBUTION_ID" --query 'Distribution.Status' --output text 2>/dev/null || echo "Error")
    echo -e "${BLUE}📊 Estado:${NC} $STATUS"
    
    if [ "$STATUS" = "Deployed" ]; then
        echo -e "${GREEN}✅ La distribución está lista para usar${NC}"
    else
        echo -e "${YELLOW}⏳ La distribución se está desplegando. Puede tomar 10-15 minutos.${NC}"
    fi
fi

# Mostrar información adicional
echo -e "\n${BLUE}📝 Información adicional:${NC}"
echo "- Los archivos se suben automáticamente al bucket S3"
echo "- CloudFront cachea los archivos para mejor rendimiento"
echo "- La distribución incluye compresión automática"
echo "- SSL/TLS está habilitado por defecto"
echo "- Los logs se almacenan en un bucket S3 separado"

echo -e "\n${BLUE}🔄 Para actualizar la interfaz web:${NC}"
echo "1. Modificar archivos en ./web-interface/"
echo "2. Ejecutar: terraform apply -target=module.cloudfront_test"
echo "3. La invalidación de caché se ejecuta automáticamente"

echo -e "\n${BLUE}🛠️ Comandos útiles:${NC}"
echo "- Ver estado: aws cloudfront get-distribution --id $DISTRIBUTION_ID"
echo "- Invalidar caché: aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths '/*'"
echo "- Ver logs: aws s3 ls s3://$S3_BUCKET-logs/"

echo -e "\n${GREEN}🎉 ¡Interfaz web disponible en CloudFront!${NC}"
