#!/bin/bash

# Script para configurar usuarios de prueba en Amazon Cognito
# Vehicle Tracking System - Test Environment

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
USER_POOL_ID="us-east-1_7bPnuc8m8"
REGION="us-east-1"
TEMP_PASSWORD="TempPass123!"

echo -e "${BLUE}🚗 Vehicle Tracking System - Configuración de Usuarios de Prueba${NC}"
echo "=================================================================="

# Verificar que AWS CLI esté configurado
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Error: AWS CLI no está configurado correctamente${NC}"
    echo "Por favor configure AWS CLI con: aws configure"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configurado correctamente${NC}"

# Función para crear usuario
create_user() {
    local username=$1
    local email=$2
    local user_type=$3
    
    echo -e "${YELLOW}📝 Creando usuario: ${username}${NC}"
    
    # Crear usuario
    aws cognito-idp admin-create-user \
        --user-pool-id "$USER_POOL_ID" \
        --username "$username" \
        --user-attributes Name=email,Value="$email" Name=email_verified,Value=true \
        --temporary-password "$TEMP_PASSWORD" \
        --message-action SUPPRESS \
        --region "$REGION" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Usuario $username ya existe, actualizando...${NC}"
    }
    
    # Establecer contraseña permanente
    aws cognito-idp admin-set-user-password \
        --user-pool-id "$USER_POOL_ID" \
        --username "$username" \
        --password "$TEMP_PASSWORD" \
        --permanent \
        --region "$REGION" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  No se pudo establecer contraseña para $username${NC}"
    }
    
    echo -e "${GREEN}✅ Usuario $username configurado${NC}"
}

# Crear usuarios de prueba
echo -e "\n${BLUE}👥 Creando usuarios de prueba...${NC}"

create_user "cliente_test" "cliente@vehicletracking.test" "client"
create_user "ventas_test" "ventas@vehicletracking.test" "sales"
create_user "admin_test" "admin@vehicletracking.test" "admin"

# Mostrar información de usuarios creados
echo -e "\n${BLUE}📋 Usuarios de prueba creados:${NC}"
echo "================================"
echo -e "${GREEN}Cliente:${NC}"
echo "  Usuario: cliente_test"
echo "  Email: cliente@vehicletracking.test"
echo "  Contraseña: $TEMP_PASSWORD"
echo ""
echo -e "${GREEN}Ventas:${NC}"
echo "  Usuario: ventas_test"
echo "  Email: ventas@vehicletracking.test"
echo "  Contraseña: $TEMP_PASSWORD"
echo ""
echo -e "${GREEN}Admin:${NC}"
echo "  Usuario: admin_test"
echo "  Email: admin@vehicletracking.test"
echo "  Contraseña: $TEMP_PASSWORD"

# Verificar usuarios
echo -e "\n${BLUE}🔍 Verificando usuarios creados...${NC}"
aws cognito-idp list-users \
    --user-pool-id "$USER_POOL_ID" \
    --region "$REGION" \
    --query 'Users[?contains(Username, `test`)].{Username:Username,Status:UserStatus,Email:Attributes[?Name==`email`].Value|[0]}' \
    --output table

echo -e "\n${GREEN}✅ Configuración completada exitosamente${NC}"
echo -e "${BLUE}🌐 Ahora puede usar la interfaz web con estos usuarios${NC}"
echo ""
echo -e "${YELLOW}📝 Notas importantes:${NC}"
echo "- Los usuarios están configurados con contraseña permanente"
echo "- Puede cambiar las contraseñas desde la consola de AWS Cognito"
echo "- Los emails son ficticios para pruebas"
echo "- User Pool ID: $USER_POOL_ID"
echo ""
echo -e "${BLUE}🚀 Para abrir la interfaz web:${NC}"
echo "cd /home/labuser/vehicle-tracking-infrastructure/web-interface"
echo "python3 -m http.server 8080"
echo "Luego abrir: http://localhost:8080"
