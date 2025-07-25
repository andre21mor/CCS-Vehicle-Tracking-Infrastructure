import json
import boto3
import os
from datetime import datetime
import logging

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
sns = boto3.client('sns')

def handler(event, context):
    """
    Procesar contrato aprobado e iniciar proceso de firma electrónica
    """
    try:
        logger.info(f"Procesando contrato aprobado: {json.dumps(event)}")
        
        contract_id = event.get('contract_id')
        if not contract_id:
            raise ValueError("contract_id es requerido")
        
        # Obtener datos del contrato
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        response = contracts_table.get_item(Key={'contract_id': contract_id})
        
        if 'Item' not in response:
            raise ValueError(f"Contrato no encontrado: {contract_id}")
        
        contract = response['Item']
        
        # Verificar que el contrato está aprobado
        if contract.get('status') != 'APPROVED':
            raise ValueError(f"Contrato no está aprobado: {contract.get('status')}")
        
        # Actualizar estado del contrato
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET #status = :status, processing_started_at = :started_at, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PROCESSING_APPROVED',
                ':started_at': int(datetime.utcnow().timestamp()),
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        
        # Iniciar proceso de firma electrónica con DocuSign
        signature_result = initiate_docusign_signature(contract_id, contract)
        
        if signature_result['success']:
            # Actualizar estado a pendiente de firma
            contracts_table.update_item(
                Key={'contract_id': contract_id},
                UpdateExpression='SET #status = :status, envelope_id = :envelope_id, signature_initiated_at = :initiated_at, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'PENDING_SIGNATURE',
                    ':envelope_id': signature_result['envelope_id'],
                    ':initiated_at': int(datetime.utcnow().timestamp()),
                    ':updated_at': int(datetime.utcnow().timestamp())
                }
            )
            
            # Enviar notificación al cliente
            send_signature_notification(contract)
            
            logger.info(f"Proceso de firma iniciado para contrato {contract_id}")
            
            return {
                'contract_id': contract_id,
                'status': 'PENDING_SIGNATURE',
                'envelope_id': signature_result['envelope_id'],
                'signature_initiated': True,
                'next_step': 'Esperando firmas electrónicas'
            }
        else:
            # Error iniciando firma
            contracts_table.update_item(
                Key={'contract_id': contract_id},
                UpdateExpression='SET #status = :status, signature_error = :error, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'SIGNATURE_INITIATION_FAILED',
                    ':error': signature_result['error'],
                    ':updated_at': int(datetime.utcnow().timestamp())
                }
            )
            
            raise Exception(f"Error iniciando firma: {signature_result['error']}")
        
    except Exception as e:
        logger.error(f"Error procesando contrato aprobado: {str(e)}")
        
        # Actualizar contrato con error
        if 'contract_id' in locals():
            try:
                contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
                contracts_table.update_item(
                    Key={'contract_id': contract_id},
                    UpdateExpression='SET #status = :status, processing_error = :error, updated_at = :updated_at',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'PROCESSING_FAILED',
                        ':error': str(e),
                        ':updated_at': int(datetime.utcnow().timestamp())
                    }
                )
            except:
                pass
        
        return {
            'contract_id': event.get('contract_id', 'unknown'),
            'status': 'ERROR',
            'error': str(e),
            'signature_initiated': False
        }

def initiate_docusign_signature(contract_id, contract_data):
    """Iniciar proceso de firma con DocuSign"""
    try:
        # Invocar función Lambda de DocuSign
        docusign_function_name = f"{os.environ.get('PROJECT_NAME', 'vehicle-tracking')}-{os.environ['ENVIRONMENT']}-docusign-signature-manager"
        
        payload = {
            'action': 'create_envelope',
            'contract_id': contract_id
        }
        
        response = lambda_client.invoke(
            FunctionName=docusign_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            return {
                'success': True,
                'envelope_id': body['envelope_id'],
                'signature_id': body['signature_id']
            }
        else:
            error_body = json.loads(result['body'])
            return {
                'success': False,
                'error': error_body.get('error', 'Error desconocido en DocuSign')
            }
            
    except Exception as e:
        logger.error(f"Error invocando función DocuSign: {str(e)}")
        return {
            'success': False,
            'error': f"Error técnico: {str(e)}"
        }

def send_signature_notification(contract_data):
    """Enviar notificación al cliente sobre el proceso de firma"""
    try:
        customer_name = contract_data.get('customer_name', 'Cliente')
        customer_email = contract_data.get('customer_email', '')
        contract_id = contract_data.get('contract_id', '')
        vehicle_count = contract_data.get('vehicle_count', 0)
        
        message = f"""
Estimado/a {customer_name},

¡Excelentes noticias! Su contrato de servicios de seguimiento vehicular ha sido APROBADO.

📋 DETALLES DEL CONTRATO:
• ID del Contrato: {contract_id}
• Cantidad de Vehículos: {vehicle_count}
• Estado: APROBADO - Pendiente de Firma

📝 PRÓXIMOS PASOS:
1. Recibirá un email de DocuSign con el contrato para firmar
2. Revise los términos y condiciones
3. Firme electrónicamente el documento
4. Una vez firmado, procederemos con la activación del servicio

⏰ TIEMPO LÍMITE:
Por favor firme el contrato dentro de los próximos 7 días para mantener las condiciones acordadas.

📞 SOPORTE:
Si tiene alguna pregunta, contáctenos:
• Email: soporte@vehicletracking.com
• Teléfono: +51-1-234-5678

¡Gracias por confiar en nuestros servicios!

Equipo de Seguimiento Vehicular
        """
        
        # Enviar notificación por SNS
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN', '')
        if sns_topic_arn:
            sns.publish(
                TopicArn=sns_topic_arn,
                Subject=f"Contrato Aprobado - Pendiente de Firma - {contract_id}",
                Message=message,
                MessageAttributes={
                    'contract_id': {
                        'DataType': 'String',
                        'StringValue': contract_id
                    },
                    'customer_email': {
                        'DataType': 'String',
                        'StringValue': customer_email
                    },
                    'event_type': {
                        'DataType': 'String',
                        'StringValue': 'CONTRACT_APPROVED_PENDING_SIGNATURE'
                    },
                    'priority': {
                        'DataType': 'String',
                        'StringValue': 'HIGH'
                    }
                }
            )
        
        logger.info(f"Notificación de firma enviada para contrato {contract_id}")
        
    except Exception as e:
        logger.error(f"Error enviando notificación de firma: {str(e)}")

def prepare_contract_for_signature(contract_data):
    """Preparar datos del contrato para DocuSign"""
    try:
        # Calcular valores adicionales
        monthly_total = float(contract_data.get('monthly_fee', 0)) * int(contract_data.get('vehicle_count', 0))
        total_contract_value = monthly_total * int(contract_data.get('contract_duration_months', 0))
        
        # Preparar datos estructurados para DocuSign
        signature_data = {
            'contract_id': contract_data.get('contract_id'),
            'customer_name': contract_data.get('customer_name'),
            'customer_email': contract_data.get('customer_email'),
            'customer_phone': contract_data.get('customer_phone', ''),
            'company_name': contract_data.get('company_name', ''),
            'vehicle_count': int(contract_data.get('vehicle_count', 0)),
            'contract_type': contract_data.get('contract_type'),
            'monthly_fee': float(contract_data.get('monthly_fee', 0)),
            'monthly_total': monthly_total,
            'contract_duration_months': int(contract_data.get('contract_duration_months', 0)),
            'total_contract_value': total_contract_value,
            'contract_terms': contract_data.get('contract_terms', {}),
            'billing_address': contract_data.get('billing_address', {}),
            'technical_requirements': contract_data.get('technical_requirements', {}),
            'special_conditions': contract_data.get('special_conditions', []),
            'created_at': contract_data.get('created_at'),
            'approved_at': contract_data.get('approved_at'),
            'approved_by': contract_data.get('approved_by', '')
        }
        
        return signature_data
        
    except Exception as e:
        logger.error(f"Error preparando contrato para firma: {str(e)}")
        return contract_data

def validate_contract_for_signature(contract_data):
    """Validar que el contrato tiene todos los datos necesarios para firma"""
    required_fields = [
        'contract_id', 'customer_name', 'customer_email',
        'vehicle_count', 'monthly_fee', 'contract_duration_months'
    ]
    
    missing_fields = []
    for field in required_fields:
        if not contract_data.get(field):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Campos requeridos faltantes para firma: {', '.join(missing_fields)}")
    
    return True
