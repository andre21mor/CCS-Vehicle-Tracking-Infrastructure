import json
import boto3
import os
from datetime import datetime
import logging
from decimal import Decimal

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """
    Validar contrato y extraer información relevante para el flujo de aprobación
    """
    try:
        logger.info(f"Validando contrato: {json.dumps(event)}")
        
        # Extraer datos del contrato
        contract_data = event.get('contract_data', {})
        contract_id = contract_data.get('contract_id')
        
        if not contract_id:
            raise ValueError("contract_id es requerido")
        
        # Validar datos obligatorios del contrato
        required_fields = [
            'customer_id', 'customer_name', 'customer_email',
            'vehicle_count', 'contract_type', 'monthly_fee',
            'contract_duration_months'
        ]
        
        for field in required_fields:
            if field not in contract_data:
                raise ValueError(f"Campo requerido faltante: {field}")
        
        # Validaciones de negocio
        vehicle_count = int(contract_data['vehicle_count'])
        monthly_fee = float(contract_data['monthly_fee'])
        duration = int(contract_data['contract_duration_months'])
        
        if vehicle_count <= 0:
            raise ValueError("La cantidad de vehículos debe ser mayor a 0")
        
        if monthly_fee <= 0:
            raise ValueError("La tarifa mensual debe ser mayor a 0")
        
        if duration < 1 or duration > 60:
            raise ValueError("La duración del contrato debe estar entre 1 y 60 meses")
        
        # Calcular métricas del contrato
        total_contract_value = monthly_fee * duration * vehicle_count
        
        # Determinar nivel de riesgo
        risk_level = calculate_risk_level(vehicle_count, total_contract_value, duration)
        
        # Guardar contrato en DynamoDB
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        
        contract_item = {
            'contract_id': contract_id,
            'customer_id': contract_data['customer_id'],
            'customer_name': contract_data['customer_name'],
            'customer_email': contract_data['customer_email'],
            'customer_phone': contract_data.get('customer_phone', ''),
            'company_name': contract_data.get('company_name', ''),
            'vehicle_count': vehicle_count,
            'contract_type': contract_data['contract_type'],
            'monthly_fee': Decimal(str(monthly_fee)),
            'contract_duration_months': duration,
            'total_contract_value': Decimal(str(total_contract_value)),
            'risk_level': risk_level,
            'status': 'PENDING_VALIDATION',
            'created_at': int(datetime.utcnow().timestamp()),
            'updated_at': int(datetime.utcnow().timestamp()),
            'requires_manager_approval': vehicle_count > 50,
            'validation_status': 'VALIDATED',
            'contract_terms': contract_data.get('contract_terms', {}),
            'billing_address': contract_data.get('billing_address', {}),
            'technical_requirements': contract_data.get('technical_requirements', {}),
            'special_conditions': contract_data.get('special_conditions', [])
        }
        
        contracts_table.put_item(Item=contract_item)
        
        logger.info(f"Contrato validado y guardado: {contract_id}")
        
        # Preparar respuesta para Step Functions
        response = {
            'contract_id': contract_id,
            'customer_id': contract_data['customer_id'],
            'customer_name': contract_data['customer_name'],
            'customer_email': contract_data['customer_email'],
            'vehicle_count': vehicle_count,
            'monthly_fee': monthly_fee,
            'contract_duration_months': duration,
            'total_contract_value': total_contract_value,
            'risk_level': risk_level,
            'requires_manager_approval': vehicle_count > 50,
            'validation_status': 'SUCCESS',
            'validation_timestamp': datetime.utcnow().isoformat(),
            'contract_type': contract_data['contract_type']
        }
        
        return response
        
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        
        # Actualizar estado del contrato como inválido
        if 'contract_id' in locals():
            try:
                contracts_table.update_item(
                    Key={'contract_id': contract_id},
                    UpdateExpression='SET #status = :status, validation_status = :validation_status, validation_error = :error, updated_at = :updated_at',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'VALIDATION_FAILED',
                        ':validation_status': 'FAILED',
                        ':error': str(e),
                        ':updated_at': int(datetime.utcnow().timestamp())
                    }
                )
            except:
                pass
        
        return {
            'validation_status': 'FAILED',
            'error': str(e),
            'contract_id': contract_data.get('contract_id', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Error interno en validación: {str(e)}")
        return {
            'validation_status': 'ERROR',
            'error': 'Error interno del sistema',
            'contract_id': contract_data.get('contract_id', 'unknown')
        }

def calculate_risk_level(vehicle_count, total_value, duration):
    """Calcular nivel de riesgo del contrato"""
    risk_score = 0
    
    # Riesgo por cantidad de vehículos
    if vehicle_count > 100:
        risk_score += 3
    elif vehicle_count > 50:
        risk_score += 2
    elif vehicle_count > 20:
        risk_score += 1
    
    # Riesgo por valor total
    if total_value > 500000:  # $500K
        risk_score += 3
    elif total_value > 100000:  # $100K
        risk_score += 2
    elif total_value > 50000:   # $50K
        risk_score += 1
    
    # Riesgo por duración
    if duration > 36:  # Más de 3 años
        risk_score += 2
    elif duration > 24:  # Más de 2 años
        risk_score += 1
    
    # Determinar nivel de riesgo
    if risk_score >= 6:
        return 'HIGH'
    elif risk_score >= 3:
        return 'MEDIUM'
    else:
        return 'LOW'
