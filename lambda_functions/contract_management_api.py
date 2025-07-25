import json
import boto3
import os
from datetime import datetime
import logging
from decimal import Decimal
import uuid

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')

def handler(event, context):
    """
    API para gestión de contratos y aprobaciones
    """
    try:
        logger.info(f"Evento recibido: {json.dumps(event)}")
        
        # Extraer información del evento
        http_method = event['httpMethod']
        path = event['path']
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        body = event.get('body')
        
        # Obtener información del usuario desde Cognito
        user_info = extract_user_info(event)
        
        # Enrutar según el método y path
        if http_method == 'POST' and path == '/contracts':
            return create_contract(user_info, json.loads(body) if body else {})
        elif http_method == 'GET' and path == '/contracts':
            return list_contracts(user_info, query_parameters)
        elif http_method == 'GET' and path.startswith('/contracts/') and len(path.split('/')) == 3:
            contract_id = path_parameters.get('contractId')
            return get_contract_by_id(user_info, contract_id)
        elif http_method == 'POST' and path.startswith('/contracts/') and path.endswith('/approve'):
            approval_id = path_parameters.get('approvalId')
            return approve_contract(user_info, approval_id, json.loads(body) if body else {})
        elif http_method == 'POST' and path.startswith('/contracts/') and path.endswith('/reject'):
            approval_id = path_parameters.get('approvalId')
            return reject_contract(user_info, approval_id, json.loads(body) if body else {})
        elif http_method == 'GET' and path == '/approvals/pending':
            return get_pending_approvals(user_info, query_parameters)
        elif http_method == 'GET' and path == '/contracts/dashboard':
            return get_contracts_dashboard(user_info, query_parameters)
        else:
            return create_response(404, {'error': 'Endpoint no encontrado'})
            
    except Exception as e:
        logger.error(f"Error en contract_management_api: {str(e)}")
        return create_response(500, {'error': 'Error interno del servidor'})

def extract_user_info(event):
    """Extraer información del usuario desde el contexto de Cognito"""
    try:
        claims = event['requestContext']['authorizer']['claims']
        return {
            'user_id': claims['sub'],
            'email': claims['email'],
            'name': claims.get('name', claims['email']),
            'groups': claims.get('cognito:groups', '').split(',') if claims.get('cognito:groups') else []
        }
    except:
        return {
            'user_id': 'anonymous',
            'email': 'anonymous@example.com',
            'name': 'Anonymous User',
            'groups': []
        }

def create_contract(user_info, contract_data):
    """Crear nuevo contrato e iniciar flujo de aprobación"""
    try:
        # Generar ID único para el contrato
        contract_id = f"CT{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8].upper()}"
        
        # Validar datos requeridos
        required_fields = [
            'customer_name', 'customer_email', 'vehicle_count',
            'contract_type', 'monthly_fee', 'contract_duration_months'
        ]
        
        for field in required_fields:
            if field not in contract_data:
                return create_response(400, {'error': f'Campo requerido: {field}'})
        
        # Preparar datos del contrato
        contract_payload = {
            'contract_data': {
                'contract_id': contract_id,
                'customer_id': user_info['user_id'],
                'customer_name': contract_data['customer_name'],
                'customer_email': contract_data['customer_email'],
                'customer_phone': contract_data.get('customer_phone', ''),
                'company_name': contract_data.get('company_name', ''),
                'vehicle_count': int(contract_data['vehicle_count']),
                'contract_type': contract_data['contract_type'],
                'monthly_fee': float(contract_data['monthly_fee']),
                'contract_duration_months': int(contract_data['contract_duration_months']),
                'contract_terms': contract_data.get('contract_terms', {}),
                'billing_address': contract_data.get('billing_address', {}),
                'technical_requirements': contract_data.get('technical_requirements', {}),
                'special_conditions': contract_data.get('special_conditions', []),
                'created_by': user_info['user_id'],
                'created_by_name': user_info['name']
            }
        }
        
        # Iniciar flujo de aprobación con Step Functions
        response = stepfunctions.start_execution(
            stateMachineArn=os.environ['STEP_FUNCTIONS_ARN'],
            name=f"contract-approval-{contract_id}-{int(datetime.utcnow().timestamp())}",
            input=json.dumps(contract_payload)
        )
        
        logger.info(f"Flujo de aprobación iniciado para contrato {contract_id}: {response['executionArn']}")
        
        return create_response(201, {
            'message': 'Contrato creado e iniciado flujo de aprobación',
            'contract_id': contract_id,
            'execution_arn': response['executionArn'],
            'requires_manager_approval': int(contract_data['vehicle_count']) > 50,
            'estimated_processing_time': '72 horas' if int(contract_data['vehicle_count']) > 50 else '15 minutos'
        })
        
    except ValueError as e:
        return create_response(400, {'error': str(e)})
    except Exception as e:
        logger.error(f"Error creando contrato: {str(e)}")
        return create_response(500, {'error': 'Error creando contrato'})

def list_contracts(user_info, query_params):
    """Listar contratos del usuario"""
    try:
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        
        # Parámetros de consulta
        limit = int(query_params.get('limit', 50))
        status_filter = query_params.get('status')
        
        # Consultar contratos
        if 'FleetManagers' in user_info['groups']:
            # Managers pueden ver todos los contratos
            if status_filter:
                response = contracts_table.scan(
                    FilterExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': status_filter},
                    Limit=limit
                )
            else:
                response = contracts_table.scan(Limit=limit)
        else:
            # Usuarios normales solo ven sus contratos
            response = contracts_table.scan(
                FilterExpression='customer_id = :customer_id',
                ExpressionAttributeValues={':customer_id': user_info['user_id']},
                Limit=limit
            )
        
        contracts = convert_decimals(response.get('Items', []))
        
        # Agregar información de estado del flujo
        for contract in contracts:
            contract['status_description'] = get_status_description(contract['status'])
            contract['next_action'] = get_next_action(contract)
        
        return create_response(200, {
            'contracts': contracts,
            'total': len(contracts),
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Error listando contratos: {str(e)}")
        return create_response(500, {'error': 'Error obteniendo contratos'})

def get_contract_by_id(user_info, contract_id):
    """Obtener contrato específico"""
    try:
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        
        response = contracts_table.get_item(
            Key={'contract_id': contract_id}
        )
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Contrato no encontrado'})
        
        contract = response['Item']
        
        # Verificar permisos
        if 'FleetManagers' not in user_info['groups'] and contract.get('customer_id') != user_info['user_id']:
            return create_response(403, {'error': 'Acceso denegado'})
        
        contract = convert_decimals(contract)
        
        # Agregar información adicional
        contract['status_description'] = get_status_description(contract['status'])
        contract['next_action'] = get_next_action(contract)
        
        # Si hay aprobación pendiente, obtener detalles
        if contract.get('approval_id'):
            approval_details = get_approval_details(contract['approval_id'])
            contract['approval_details'] = approval_details
        
        return create_response(200, contract)
        
    except Exception as e:
        logger.error(f"Error obteniendo contrato {contract_id}: {str(e)}")
        return create_response(500, {'error': 'Error obteniendo contrato'})

def approve_contract(user_info, approval_id, approval_data):
    """Aprobar contrato"""
    try:
        # Verificar que el usuario es manager
        if 'FleetManagers' not in user_info['groups']:
            return create_response(403, {'error': 'Solo los managers pueden aprobar contratos'})
        
        approvals_table = dynamodb.Table(os.environ['APPROVALS_TABLE'])
        
        # Obtener aprobación
        response = approvals_table.get_item(
            Key={'approval_id': approval_id}
        )
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Aprobación no encontrada'})
        
        approval = response['Item']
        
        # Verificar que está pendiente
        if approval['status'] != 'PENDING':
            return create_response(400, {'error': f'La aprobación ya está {approval["status"]}'})
        
        # Verificar que no ha expirado
        if int(datetime.utcnow().timestamp()) > approval['expires_at']:
            return create_response(400, {'error': 'La aprobación ha expirado'})
        
        # Actualizar aprobación
        approvals_table.update_item(
            Key={'approval_id': approval_id},
            UpdateExpression='SET #status = :status, approved_at = :approved_at, approved_by = :approved_by, approval_comments = :comments',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'APPROVED',
                ':approved_at': int(datetime.utcnow().timestamp()),
                ':approved_by': user_info['user_id'],
                ':comments': approval_data.get('comments', '')
            }
        )
        
        # Actualizar contrato
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        contracts_table.update_item(
            Key={'contract_id': approval['contract_id']},
            UpdateExpression='SET #status = :status, approved_at = :approved_at, approved_by = :approved_by, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'APPROVED',
                ':approved_at': int(datetime.utcnow().timestamp()),
                ':approved_by': user_info['user_id'],
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        
        logger.info(f"Contrato {approval['contract_id']} aprobado por {user_info['name']}")
        
        return create_response(200, {
            'message': 'Contrato aprobado exitosamente',
            'contract_id': approval['contract_id'],
            'approval_id': approval_id,
            'approved_by': user_info['name'],
            'approved_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error aprobando contrato: {str(e)}")
        return create_response(500, {'error': 'Error aprobando contrato'})

def reject_contract(user_info, approval_id, rejection_data):
    """Rechazar contrato"""
    try:
        # Verificar que el usuario es manager
        if 'FleetManagers' not in user_info['groups']:
            return create_response(403, {'error': 'Solo los managers pueden rechazar contratos'})
        
        rejection_reason = rejection_data.get('reason', '')
        if not rejection_reason:
            return create_response(400, {'error': 'Se requiere especificar el motivo del rechazo'})
        
        approvals_table = dynamodb.Table(os.environ['APPROVALS_TABLE'])
        
        # Obtener aprobación
        response = approvals_table.get_item(
            Key={'approval_id': approval_id}
        )
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Aprobación no encontrada'})
        
        approval = response['Item']
        
        # Verificar que está pendiente
        if approval['status'] != 'PENDING':
            return create_response(400, {'error': f'La aprobación ya está {approval["status"]}'})
        
        # Actualizar aprobación
        approvals_table.update_item(
            Key={'approval_id': approval_id},
            UpdateExpression='SET #status = :status, rejected_at = :rejected_at, rejected_by = :rejected_by, rejection_reason = :reason',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'REJECTED',
                ':rejected_at': int(datetime.utcnow().timestamp()),
                ':rejected_by': user_info['user_id'],
                ':reason': rejection_reason
            }
        )
        
        # Actualizar contrato
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        contracts_table.update_item(
            Key={'contract_id': approval['contract_id']},
            UpdateExpression='SET #status = :status, rejected_at = :rejected_at, rejected_by = :rejected_by, rejection_reason = :reason, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'REJECTED',
                ':rejected_at': int(datetime.utcnow().timestamp()),
                ':rejected_by': user_info['user_id'],
                ':reason': rejection_reason,
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        
        logger.info(f"Contrato {approval['contract_id']} rechazado por {user_info['name']}: {rejection_reason}")
        
        return create_response(200, {
            'message': 'Contrato rechazado',
            'contract_id': approval['contract_id'],
            'approval_id': approval_id,
            'rejected_by': user_info['name'],
            'rejection_reason': rejection_reason,
            'rejected_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error rechazando contrato: {str(e)}")
        return create_response(500, {'error': 'Error rechazando contrato'})

def get_pending_approvals(user_info, query_params):
    """Obtener aprobaciones pendientes para el manager"""
    try:
        # Verificar que el usuario es manager
        if 'FleetManagers' not in user_info['groups']:
            return create_response(403, {'error': 'Solo los managers pueden ver aprobaciones pendientes'})
        
        approvals_table = dynamodb.Table(os.environ['APPROVALS_TABLE'])
        
        # Obtener aprobaciones pendientes del usuario
        response = approvals_table.query(
            IndexName='ApproverIndex',
            KeyConditionExpression='approver_id = :approver_id',
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':approver_id': user_info['user_id'],
                ':status': 'PENDING'
            }
        )
        
        approvals = convert_decimals(response.get('Items', []))
        
        # Agregar información adicional
        for approval in approvals:
            approval['time_remaining_hours'] = max(0, (approval['expires_at'] - int(datetime.utcnow().timestamp())) // 3600)
            approval['is_expired'] = approval['expires_at'] < int(datetime.utcnow().timestamp())
        
        return create_response(200, {
            'pending_approvals': approvals,
            'total': len(approvals)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo aprobaciones pendientes: {str(e)}")
        return create_response(500, {'error': 'Error obteniendo aprobaciones pendientes'})

def get_contracts_dashboard(user_info, query_params):
    """Obtener dashboard de contratos"""
    try:
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        
        # Obtener estadísticas de contratos
        if 'FleetManagers' in user_info['groups']:
            # Managers ven estadísticas globales
            response = contracts_table.scan()
        else:
            # Usuarios ven solo sus contratos
            response = contracts_table.scan(
                FilterExpression='customer_id = :customer_id',
                ExpressionAttributeValues={':customer_id': user_info['user_id']}
            )
        
        contracts = response.get('Items', [])
        
        # Calcular estadísticas
        stats = {
            'total_contracts': len(contracts),
            'pending_approval': len([c for c in contracts if c.get('status') == 'PENDING_MANAGER_APPROVAL']),
            'approved': len([c for c in contracts if c.get('status') == 'APPROVED']),
            'rejected': len([c for c in contracts if c.get('status') == 'REJECTED']),
            'total_vehicles': sum(int(c.get('vehicle_count', 0)) for c in contracts if c.get('status') == 'APPROVED'),
            'total_value': float(sum(c.get('total_contract_value', 0) for c in contracts if c.get('status') == 'APPROVED')),
            'contracts_requiring_approval': len([c for c in contracts if c.get('requires_manager_approval', False)])
        }
        
        return create_response(200, {
            'dashboard': stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo dashboard: {str(e)}")
        return create_response(500, {'error': 'Error obteniendo dashboard'})

def get_approval_details(approval_id):
    """Obtener detalles de aprobación"""
    try:
        approvals_table = dynamodb.Table(os.environ['APPROVALS_TABLE'])
        
        response = approvals_table.get_item(
            Key={'approval_id': approval_id}
        )
        
        if 'Item' in response:
            return convert_decimals(response['Item'])
        return None
        
    except Exception as e:
        logger.error(f"Error obteniendo detalles de aprobación: {str(e)}")
        return None

def get_status_description(status):
    """Obtener descripción del estado"""
    descriptions = {
        'PENDING_VALIDATION': 'Pendiente de validación',
        'VALIDATION_FAILED': 'Validación fallida',
        'PENDING_MANAGER_APPROVAL': 'Pendiente de aprobación del manager',
        'APPROVED': 'Aprobado',
        'REJECTED': 'Rechazado',
        'PROCESSING': 'En procesamiento',
        'ACTIVE': 'Activo',
        'EXPIRED': 'Expirado'
    }
    return descriptions.get(status, status)

def get_next_action(contract):
    """Obtener próxima acción requerida"""
    status = contract.get('status')
    
    if status == 'PENDING_MANAGER_APPROVAL':
        return 'Esperando aprobación del manager'
    elif status == 'APPROVED':
        return 'Proceder con firma electrónica'
    elif status == 'REJECTED':
        return 'Revisar motivo de rechazo y crear nuevo contrato'
    elif status == 'VALIDATION_FAILED':
        return 'Corregir errores de validación'
    else:
        return 'Sin acciones pendientes'

def convert_decimals(obj):
    """Convertir objetos Decimal a float para serialización JSON"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

def create_response(status_code, body):
    """Crear respuesta HTTP estándar"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body, ensure_ascii=False)
    }
