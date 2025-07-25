import json
import boto3
import os
from datetime import datetime, timedelta
import logging
import uuid

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
cognito = boto3.client('cognito-idp')

def handler(event, context):
    """
    Solicitar aprobación del manager para contratos de más de 50 vehículos
    """
    try:
        logger.info(f"Solicitando aprobación del manager: {json.dumps(event)}")
        
        # Extraer datos del contrato
        contract_id = event.get('contract_id')
        customer_name = event.get('customer_name')
        vehicle_count = event.get('vehicle_count')
        total_contract_value = event.get('total_contract_value')
        risk_level = event.get('risk_level')
        
        if not contract_id:
            raise ValueError("contract_id es requerido")
        
        # Generar ID único para la aprobación
        approval_id = str(uuid.uuid4())
        
        # Obtener managers disponibles
        managers = get_available_managers()
        
        if not managers:
            raise Exception("No hay managers disponibles para aprobación")
        
        # Crear registro de aprobación en DynamoDB
        approvals_table = dynamodb.Table(os.environ['APPROVALS_TABLE'])
        
        approval_item = {
            'approval_id': approval_id,
            'contract_id': contract_id,
            'approver_id': managers[0]['user_id'],  # Asignar al primer manager disponible
            'approver_name': managers[0]['name'],
            'approver_email': managers[0]['email'],
            'status': 'PENDING',
            'created_at': int(datetime.utcnow().timestamp()),
            'expires_at': int((datetime.utcnow() + timedelta(hours=72)).timestamp()),  # 72 horas para aprobar
            'contract_details': {
                'customer_name': customer_name,
                'vehicle_count': vehicle_count,
                'total_value': total_contract_value,
                'risk_level': risk_level
            },
            'approval_url': f"{os.environ['APPROVAL_URL_BASE']}/{approval_id}",
            'rejection_reason': None,
            'approved_at': None,
            'rejected_at': None
        }
        
        approvals_table.put_item(Item=approval_item)
        
        # Actualizar estado del contrato
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET #status = :status, approval_id = :approval_id, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PENDING_MANAGER_APPROVAL',
                ':approval_id': approval_id,
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        
        # Enviar notificación al manager
        notification_sent = send_manager_notification(
            manager=managers[0],
            contract_id=contract_id,
            customer_name=customer_name,
            vehicle_count=vehicle_count,
            total_value=total_contract_value,
            risk_level=risk_level,
            approval_url=approval_item['approval_url']
        )
        
        logger.info(f"Solicitud de aprobación creada: {approval_id}")
        
        # Preparar respuesta para Step Functions
        response = {
            'approval_id': approval_id,
            'contract_id': contract_id,
            'approver_id': managers[0]['user_id'],
            'approver_name': managers[0]['name'],
            'approver_email': managers[0]['email'],
            'approval_status': 'PENDING',
            'expires_at': approval_item['expires_at'],
            'notification_sent': notification_sent,
            'approval_url': approval_item['approval_url']
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error solicitando aprobación del manager: {str(e)}")
        
        # Actualizar contrato con error
        if 'contract_id' in locals():
            try:
                contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
                contracts_table.update_item(
                    Key={'contract_id': contract_id},
                    UpdateExpression='SET #status = :status, approval_error = :error, updated_at = :updated_at',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'APPROVAL_REQUEST_FAILED',
                        ':error': str(e),
                        ':updated_at': int(datetime.utcnow().timestamp())
                    }
                )
            except:
                pass
        
        return {
            'approval_status': 'ERROR',
            'error': str(e),
            'contract_id': event.get('contract_id', 'unknown')
        }

def get_available_managers():
    """Obtener lista de managers disponibles para aprobación"""
    try:
        # En un entorno real, esto consultaría Cognito para obtener usuarios del grupo FleetManagers
        # Por ahora, devolvemos una lista simulada
        
        managers = [
            {
                'user_id': 'manager-001',
                'name': 'Carlos Rodriguez',
                'email': 'carlos.rodriguez@vehicletracking.com',
                'phone': '+51999123456',
                'department': 'Fleet Operations',
                'approval_limit': 1000000  # $1M
            },
            {
                'user_id': 'manager-002',
                'name': 'Ana Martinez',
                'email': 'ana.martinez@vehicletracking.com',
                'phone': '+51999654321',
                'department': 'Sales',
                'approval_limit': 500000   # $500K
            }
        ]
        
        # Filtrar managers activos y disponibles
        available_managers = []
        for manager in managers:
            # Verificar si el manager no tiene demasiadas aprobaciones pendientes
            pending_approvals = count_pending_approvals(manager['user_id'])
            if pending_approvals < 5:  # Máximo 5 aprobaciones pendientes
                available_managers.append(manager)
        
        return available_managers
        
    except Exception as e:
        logger.error(f"Error obteniendo managers: {str(e)}")
        return []

def count_pending_approvals(manager_id):
    """Contar aprobaciones pendientes de un manager"""
    try:
        approvals_table = dynamodb.Table(os.environ['APPROVALS_TABLE'])
        
        response = approvals_table.query(
            IndexName='ApproverIndex',
            KeyConditionExpression='approver_id = :approver_id',
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':approver_id': manager_id,
                ':status': 'PENDING'
            }
        )
        
        return len(response.get('Items', []))
        
    except Exception as e:
        logger.error(f"Error contando aprobaciones pendientes: {str(e)}")
        return 0

def send_manager_notification(manager, contract_id, customer_name, vehicle_count, total_value, risk_level, approval_url):
    """Enviar notificación al manager para aprobación"""
    try:
        # Preparar mensaje de notificación
        subject = f"🚨 APROBACIÓN REQUERIDA - Contrato {contract_id} ({vehicle_count} vehículos)"
        
        message = f"""
SOLICITUD DE APROBACIÓN DE CONTRATO

Estimado/a {manager['name']},

Se requiere su aprobación para el siguiente contrato que excede el límite de 50 vehículos:

📋 DETALLES DEL CONTRATO:
• ID del Contrato: {contract_id}
• Cliente: {customer_name}
• Cantidad de Vehículos: {vehicle_count}
• Valor Total: ${total_value:,.2f}
• Nivel de Riesgo: {risk_level}

⏰ TIEMPO LÍMITE:
• Debe aprobar o rechazar dentro de 72 horas
• Vencimiento: {(datetime.utcnow() + timedelta(hours=72)).strftime('%Y-%m-%d %H:%M:%S')} UTC

🔗 ACCIONES:
Para revisar y aprobar/rechazar este contrato, haga clic en el siguiente enlace:
{approval_url}

O responda a este mensaje con:
• "APROBAR {contract_id}" para aprobar
• "RECHAZAR {contract_id} [motivo]" para rechazar

⚠️ IMPORTANTE:
Si no se toma una decisión dentro del tiempo límite, el contrato será automáticamente rechazado.

---
Sistema de Gestión de Contratos
Plataforma de Seguimiento Vehicular
        """
        
        # Enviar notificación por SNS
        sns_response = sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Subject=subject,
            Message=message,
            MessageAttributes={
                'contract_id': {
                    'DataType': 'String',
                    'StringValue': contract_id
                },
                'approver_id': {
                    'DataType': 'String',
                    'StringValue': manager['user_id']
                },
                'vehicle_count': {
                    'DataType': 'Number',
                    'StringValue': str(vehicle_count)
                },
                'priority': {
                    'DataType': 'String',
                    'StringValue': 'HIGH' if risk_level == 'HIGH' else 'MEDIUM'
                }
            }
        )
        
        logger.info(f"Notificación enviada al manager {manager['name']}: {sns_response['MessageId']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error enviando notificación al manager: {str(e)}")
        return False
