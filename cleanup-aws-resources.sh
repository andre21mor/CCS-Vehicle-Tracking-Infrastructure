#!/bin/bash

# Script de limpieza completa de recursos AWS
# Vehicle Tracking Infrastructure Cleanup

set -e  # Exit on any error

echo "🧹 INICIANDO LIMPIEZA DE RECURSOS AWS"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Confirmation prompt
echo -e "${YELLOW}⚠️  ADVERTENCIA: Este script eliminará TODOS los recursos del proyecto vehicle-tracking-test-70v${NC}"
echo -e "${YELLOW}   Esto incluye:${NC}"
echo "   - 13 Funciones Lambda"
echo "   - 13 Tablas DynamoDB"
echo "   - 6 Buckets S3 (y todo su contenido)"
echo "   - API Gateway"
echo "   - CloudFront Distribution"
echo "   - Cognito User Pools"
echo "   - IAM Roles y Policies"
echo "   - CloudWatch Logs"
echo "   - Y otros recursos relacionados"
echo ""
read -p "¿Estás segura de que quieres continuar? (escribe 'SI' para confirmar): " confirmation

if [ "$confirmation" != "SI" ]; then
    echo "❌ Operación cancelada por el usuario"
    exit 0
fi

echo ""
print_status "Iniciando proceso de limpieza..."

# 1. Delete Lambda Functions
print_status "🔥 Eliminando funciones Lambda..."
LAMBDA_FUNCTIONS=$(aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `vehicle-tracking-test-70v`)].FunctionName' --output text)

if [ -n "$LAMBDA_FUNCTIONS" ]; then
    for function in $LAMBDA_FUNCTIONS; do
        print_status "Eliminando función Lambda: $function"
        aws lambda delete-function --function-name "$function" || print_warning "No se pudo eliminar $function"
    done
else
    print_status "No se encontraron funciones Lambda para eliminar"
fi

# 2. Delete DynamoDB Tables
print_status "🗄️  Eliminando tablas DynamoDB..."
DYNAMODB_TABLES=$(aws dynamodb list-tables --query 'TableNames[?starts_with(@, `vehicle-tracking-test-70v`)]' --output text)

if [ -n "$DYNAMODB_TABLES" ]; then
    for table in $DYNAMODB_TABLES; do
        print_status "Eliminando tabla DynamoDB: $table"
        aws dynamodb delete-table --table-name "$table" || print_warning "No se pudo eliminar $table"
    done
else
    print_status "No se encontraron tablas DynamoDB para eliminar"
fi

# 3. Empty and Delete S3 Buckets
print_status "🪣 Vaciando y eliminando buckets S3..."
S3_BUCKETS=$(aws s3 ls | grep vehicle-tracking-test-70v | awk '{print $3}')

if [ -n "$S3_BUCKETS" ]; then
    for bucket in $S3_BUCKETS; do
        print_status "Vaciando bucket S3: $bucket"
        aws s3 rm s3://$bucket --recursive || print_warning "No se pudo vaciar $bucket"
        
        print_status "Eliminando bucket S3: $bucket"
        aws s3 rb s3://$bucket || print_warning "No se pudo eliminar $bucket"
    done
else
    print_status "No se encontraron buckets S3 para eliminar"
fi

# 4. Delete API Gateway
print_status "🌐 Eliminando API Gateway..."
API_GATEWAYS=$(aws apigateway get-rest-apis --query 'items[?starts_with(name, `vehicle-tracking-test-70v`)].id' --output text)

if [ -n "$API_GATEWAYS" ]; then
    for api_id in $API_GATEWAYS; do
        print_status "Eliminando API Gateway: $api_id"
        aws apigateway delete-rest-api --rest-api-id "$api_id" || print_warning "No se pudo eliminar API $api_id"
    done
else
    print_status "No se encontraron APIs Gateway para eliminar"
fi

# 5. Delete CloudFront Distribution
print_status "☁️  Eliminando CloudFront Distribution..."
CLOUDFRONT_DISTRIBUTIONS=$(aws cloudfront list-distributions --query 'DistributionList.Items[?starts_with(Comment, `Vehicle Tracking`)].Id' --output text)

if [ -n "$CLOUDFRONT_DISTRIBUTIONS" ]; then
    for dist_id in $CLOUDFRONT_DISTRIBUTIONS; do
        print_warning "CloudFront Distribution encontrada: $dist_id"
        print_warning "⚠️  Las distribuciones de CloudFront deben deshabilitarse manualmente antes de eliminarlas"
        print_warning "   1. Ve a AWS Console -> CloudFront"
        print_warning "   2. Selecciona la distribución $dist_id"
        print_warning "   3. Deshabilítala y espera ~15 minutos"
        print_warning "   4. Luego elimínala manualmente"
    done
else
    print_status "No se encontraron distribuciones CloudFront"
fi

# 6. Delete Cognito User Pools
print_status "👥 Eliminando Cognito User Pools..."
USER_POOLS=$(aws cognito-idp list-user-pools --max-items 50 --query 'UserPools[?starts_with(Name, `vehicle-tracking-test-70v`)].Id' --output text)

if [ -n "$USER_POOLS" ]; then
    for pool_id in $USER_POOLS; do
        print_status "Eliminando Cognito User Pool: $pool_id"
        aws cognito-idp delete-user-pool --user-pool-id "$pool_id" || print_warning "No se pudo eliminar pool $pool_id"
    done
else
    print_status "No se encontraron User Pools de Cognito"
fi

# 7. Delete IAM Roles and Policies
print_status "🔐 Eliminando roles y políticas IAM..."
IAM_ROLES=$(aws iam list-roles --query 'Roles[?starts_with(RoleName, `vehicle-tracking-test-70v`)].RoleName' --output text)

if [ -n "$IAM_ROLES" ]; then
    for role in $IAM_ROLES; do
        print_status "Procesando rol IAM: $role"
        
        # Detach managed policies
        ATTACHED_POLICIES=$(aws iam list-attached-role-policies --role-name "$role" --query 'AttachedPolicies[].PolicyArn' --output text)
        for policy_arn in $ATTACHED_POLICIES; do
            print_status "Desvinculando política: $policy_arn"
            aws iam detach-role-policy --role-name "$role" --policy-arn "$policy_arn" || print_warning "No se pudo desvincular $policy_arn"
        done
        
        # Delete inline policies
        INLINE_POLICIES=$(aws iam list-role-policies --role-name "$role" --query 'PolicyNames' --output text)
        for policy in $INLINE_POLICIES; do
            print_status "Eliminando política inline: $policy"
            aws iam delete-role-policy --role-name "$role" --policy-name "$policy" || print_warning "No se pudo eliminar política $policy"
        done
        
        # Delete role
        print_status "Eliminando rol IAM: $role"
        aws iam delete-role --role-name "$role" || print_warning "No se pudo eliminar rol $role"
    done
else
    print_status "No se encontraron roles IAM para eliminar"
fi

# 8. Delete CloudWatch Log Groups
print_status "📊 Eliminando grupos de logs CloudWatch..."
LOG_GROUPS=$(aws logs describe-log-groups --query 'logGroups[?starts_with(logGroupName, `/aws/lambda/vehicle-tracking-test-70v`)].logGroupName' --output text)

if [ -n "$LOG_GROUPS" ]; then
    for log_group in $LOG_GROUPS; do
        print_status "Eliminando log group: $log_group"
        aws logs delete-log-group --log-group-name "$log_group" || print_warning "No se pudo eliminar $log_group"
    done
else
    print_status "No se encontraron log groups para eliminar"
fi

# 9. Delete SNS Topics
print_status "📢 Eliminando tópicos SNS..."
SNS_TOPICS=$(aws sns list-topics --query 'Topics[?contains(TopicArn, `vehicle-tracking-test-70v`)].TopicArn' --output text)

if [ -n "$SNS_TOPICS" ]; then
    for topic_arn in $SNS_TOPICS; do
        print_status "Eliminando tópico SNS: $topic_arn"
        aws sns delete-topic --topic-arn "$topic_arn" || print_warning "No se pudo eliminar $topic_arn"
    done
else
    print_status "No se encontraron tópicos SNS para eliminar"
fi

# 10. Delete Kinesis Streams
print_status "🌊 Eliminando streams Kinesis..."
KINESIS_STREAMS=$(aws kinesis list-streams --query 'StreamNames[?starts_with(@, `vehicle-tracking-test-70v`)]' --output text)

if [ -n "$KINESIS_STREAMS" ]; then
    for stream in $KINESIS_STREAMS; do
        print_status "Eliminando stream Kinesis: $stream"
        aws kinesis delete-stream --stream-name "$stream" || print_warning "No se pudo eliminar $stream"
    done
else
    print_status "No se encontraron streams Kinesis para eliminar"
fi

# 11. Delete ElastiCache Clusters
print_status "⚡ Eliminando clusters ElastiCache..."
ELASTICACHE_CLUSTERS=$(aws elasticache describe-replication-groups --query 'ReplicationGroups[?starts_with(ReplicationGroupId, `vehicle-tracking-test-70v`)].ReplicationGroupId' --output text)

if [ -n "$ELASTICACHE_CLUSTERS" ]; then
    for cluster in $ELASTICACHE_CLUSTERS; do
        print_status "Eliminando cluster ElastiCache: $cluster"
        aws elasticache delete-replication-group --replication-group-id "$cluster" || print_warning "No se pudo eliminar $cluster"
    done
else
    print_status "No se encontraron clusters ElastiCache para eliminar"
fi

# Final status
echo ""
print_status "✅ LIMPIEZA COMPLETADA"
echo "======================="
print_status "La mayoría de los recursos han sido eliminados."
print_warning "⚠️  NOTA IMPORTANTE sobre CloudFront:"
print_warning "   Si había distribuciones de CloudFront, deben deshabilitarse manualmente"
print_warning "   en la consola de AWS antes de poder eliminarlas completamente."
echo ""
print_status "💰 Esto debería detener todos los costos asociados al proyecto."
print_status "🔍 Puedes verificar en la consola de AWS que los recursos fueron eliminados."
echo ""
print_status "¡Gracias por usar Vehicle Tracking Infrastructure! 🚗✨"
