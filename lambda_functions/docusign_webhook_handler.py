import json
import boto3
import os
from datetime import datetime
import logging
import hmac
import hashlib
import base64

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
lambda_client = boto3.client('lambda')

def handler(event, context):
    """
    Handler para webhooks de DocuSign
    Procesa eventos de firma, rechazo, etc.
    """
    try:
        logger.info(f"Webhook recibido: {json.dumps(event)}")
        
        # Extraer datos del webhook
        body = event.get('body', '{}')
        headers = event.get('headers', {})
        
        # Verificar autenticidad del webhook (opcional)
        if not verify_webhook_signature(body, headers):
            logger.warning("Webhook signature verification failed")
            # En producción, podrías rechazar el webhook aquí
        
        # Parsear datos del webhook
        webhook_data = json.loads(body) if isinstance(body, str) else body
        
        # Procesar evento según el tipo
        event_type = webhook_data.get('event')
        envelope_data = webhook_data.get('data', {}).get('envelopeData', {})
        
        if event_type == 'envelope-completed':
            return handle_envelope_completed(envelope_data)
        elif event_type == 'envelope-declined':
            return handle_envelope_declined(envelope_data)
        elif event_type == 'envelope-voided':
            return handle_envelope_voided(envelope_data)
        elif event_type == 'recipient-completed':
            return handle_recipient_completed(envelope_data)
        else:
            logger.info(f"Evento no procesado: {event_type}")
            return create_response(200, {'message': f'Evento {event_type} recibido pero no procesado'})
            
    except Exception as e:
        logger.error(f"Error procesando webhook: {str(e)}")
        return create_response(500, {'error': 'Error procesando webhook'})

def verify_webhook_signature(body, headers):
    """Verificar firma del webhook de DocuSign"""
    try:
        # DocuSign envía la firma en el header X-DocuSign-Signature-1
        signature = headers.get('X-DocuSign-Signature-1') or headers.get('x-docusign-signature-1')
        
        if not signature:
            logger.warning("No se encontró firma en el webhook")
            return True  # Por ahora, permitir sin verificación
        
        # En producción, verificarías la firma usando tu webhook secret
        # webhook_secret = get_webhook_secret()
        # expected_signature = hmac.new(
        #     webhook_secret.encode(),
        #     body.encode(),
        #     hashlib.sha256
        # ).hexdigest()
        
        # return hmac.compare_digest(signature, expected_signature)
        
        return True  # Simplificado para demo
        
    except Exception as e:
        logger.error(f"Error verificando firma del webhook: {str(e)}")
        return False

def handle_envelope_completed(envelope_data):
    """Manejar envelope completado (todas las firmas obtenidas)"""
    try:
        envelope_id = envelope_data.get('envelopeId')
        envelope_status = envelope_data.get('envelopeStatus')
        
        logger.info(f"Envelope completado: {envelope_id}")
        
        # Buscar contrato asociado
        contract_id = find_contract_by_envelope(envelope_id)
        if not contract_id:
            logger.error(f"No se encontró contrato para envelope {envelope_id}")
            return create_response(404, {'error': 'Contrato no encontrado'})
        
        # Actualizar estado del contrato
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET #status = :status, signed_at = :signed_at, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'SIGNED',
                ':signed_at': int(datetime.utcnow().timestamp()),
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        
        # Actualizar registro de firmas
        signatures_table = dynamodb.Table(os.environ['SIGNATURES_TABLE'])
        
        # Buscar registro de firma por envelope_id
        response = signatures_table.scan(
            FilterExpression='envelope_id = :envelope_id',
            ExpressionAttributeValues={':envelope_id': envelope_id}
        )
        
        if response['Items']:
            signature_record = response['Items'][0]
            
            # Actualizar estado de todos los firmantes
            updated_signers = []
            for signer in signature_record.get('signers', []):
                signer['status'] = 'COMPLETED'
                signer['signed_at'] = int(datetime.utcnow().timestamp())
                updated_signers.append(signer)
            
            signatures_table.update_item(
                Key={'signature_id': signature_record['signature_id']},
                UpdateExpression='SET #status = :status, completed_at = :completed_at, signers = :signers',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'COMPLETED',
                    ':completed_at': int(datetime.utcnow().timestamp()),
                    ':signers': updated_signers
                }
            )
        
        # Enviar notificación
        send_contract_notification(
            contract_id,
            'SIGNED',
            f'El contrato {contract_id} ha sido firmado exitosamente por todas las partes.'
        )
        
        # Iniciar proceso de activación del servicio
        initiate_service_activation(contract_id)
        
        logger.info(f"Contrato {contract_id} marcado como firmado")
        
        return create_response(200, {
            'message': 'Envelope completado procesado exitosamente',
            'contract_id': contract_id,
            'envelope_id': envelope_id
        })
        
    except Exception as e:
        logger.error(f"Error procesando envelope completado: {str(e)}")
        return create_response(500, {'error': str(e)})

def handle_envelope_declined(envelope_data):
    """Manejar envelope rechazado"""
    try:
        envelope_id = envelope_data.get('envelopeId')
        decline_reason = envelope_data.get('declineReason', 'No especificado')
        
        logger.info(f"Envelope rechazado: {envelope_id}, razón: {decline_reason}")
        
        # Buscar contrato asociado
        contract_id = find_contract_by_envelope(envelope_id)
        if not contract_id:
            return create_response(404, {'error': 'Contrato no encontrado'})
        
        # Actualizar estado del contrato
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET #status = :status, declined_at = :declined_at, decline_reason = :reason, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'SIGNATURE_DECLINED',
                ':declined_at': int(datetime.utcnow().timestamp()),
                ':reason': decline_reason,
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        
        # Actualizar registro de firmas
        update_signature_status(envelope_id, 'DECLINED', decline_reason)
        
        # Enviar notificación
        send_contract_notification(
            contract_id,
            'DECLINED',
            f'El contrato {contract_id} ha sido rechazado. Razón: {decline_reason}'
        )
        
        return create_response(200, {
            'message': 'Envelope rechazado procesado',
            'contract_id': contract_id,
            'decline_reason': decline_reason
        })
        
    except Exception as e:
        logger.error(f"Error procesando envelope rechazado: {str(e)}")
        return create_response(500, {'error': str(e)})

def handle_envelope_voided(envelope_data):
    """Manejar envelope anulado"""
    try:
        envelope_id = envelope_data.get('envelopeId')
        void_reason = envelope_data.get('voidReason', 'No especificado')
        
        logger.info(f"Envelope anulado: {envelope_id}, razón: {void_reason}")
        
        # Buscar contrato asociado
        contract_id = find_contract_by_envelope(envelope_id)
        if not contract_id:
            return create_response(404, {'error': 'Contrato no encontrado'})
        
        # Actualizar estado del contrato
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET #status = :status, voided_at = :voided_at, void_reason = :reason, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'SIGNATURE_VOIDED',
                ':voided_at': int(datetime.utcnow().timestamp()),
                ':reason': void_reason,
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        
        # Actualizar registro de firmas
        update_signature_status(envelope_id, 'VOIDED', void_reason)
        
        # Enviar notificación
        send_contract_notification(
            contract_id,
            'VOIDED',
            f'El contrato {contract_id} ha sido anulado. Razón: {void_reason}'
        )
        
        return create_response(200, {
            'message': 'Envelope anulado procesado',
            'contract_id': contract_id,
            'void_reason': void_reason
        })
        
    except Exception as e:
        logger.error(f"Error procesando envelope anulado: {str(e)}")
        return create_response(500, {'error': str(e)})

def handle_recipient_completed(envelope_data):
    """Manejar firmante individual completado"""
    try:
        envelope_id = envelope_data.get('envelopeId')
        recipients = envelope_data.get('recipients', {})
        
        logger.info(f"Firmante completado en envelope: {envelope_id}")
        
        # Actualizar estado del firmante específico
        signatures_table = dynamodb.Table(os.environ['SIGNATURES_TABLE'])
        
        response = signatures_table.scan(
            FilterExpression='envelope_id = :envelope_id',
            ExpressionAttributeValues={':envelope_id': envelope_id}
        )
        
        if response['Items']:
            signature_record = response['Items'][0]
            
            # Actualizar firmantes completados
            updated_signers = []
            for signer in signature_record.get('signers', []):
                # Verificar si este firmante completó
                for recipient_type, recipient_list in recipients.items():
                    for recipient in recipient_list:
                        if recipient.get('email') == signer['email'] and recipient.get('status') == 'completed':
                            signer['status'] = 'COMPLETED'
                            signer['signed_at'] = int(datetime.utcnow().timestamp())
                
                updated_signers.append(signer)
            
            signatures_table.update_item(
                Key={'signature_id': signature_record['signature_id']},
                UpdateExpression='SET signers = :signers, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':signers': updated_signers,
                    ':updated_at': int(datetime.utcnow().timestamp())
                }
            )
        
        return create_response(200, {
            'message': 'Firmante completado procesado',
            'envelope_id': envelope_id
        })
        
    except Exception as e:
        logger.error(f"Error procesando firmante completado: {str(e)}")
        return create_response(500, {'error': str(e)})

def find_contract_by_envelope(envelope_id):
    """Buscar contrato por envelope ID"""
    try:
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        
        response = contracts_table.scan(
            FilterExpression='envelope_id = :envelope_id',
            ExpressionAttributeValues={':envelope_id': envelope_id}
        )
        
        if response['Items']:
            return response['Items'][0]['contract_id']
        
        return None
        
    except Exception as e:
        logger.error(f"Error buscando contrato por envelope: {str(e)}")
        return None

def update_signature_status(envelope_id, status, reason=None):
    """Actualizar estado del registro de firma"""
    try:
        signatures_table = dynamodb.Table(os.environ['SIGNATURES_TABLE'])
        
        response = signatures_table.scan(
            FilterExpression='envelope_id = :envelope_id',
            ExpressionAttributeValues={':envelope_id': envelope_id}
        )
        
        if response['Items']:
            signature_record = response['Items'][0]
            
            update_expression = 'SET #status = :status, updated_at = :updated_at'
            expression_values = {
                ':status': status,
                ':updated_at': int(datetime.utcnow().timestamp())
            }
            
            if reason:
                update_expression += ', reason = :reason'
                expression_values[':reason'] = reason
            
            signatures_table.update_item(
                Key={'signature_id': signature_record['signature_id']},
                UpdateExpression=update_expression,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=expression_values
            )
            
    except Exception as e:
        logger.error(f"Error actualizando estado de firma: {str(e)}")

def send_contract_notification(contract_id, event_type, message):
    """Enviar notificación sobre evento del contrato"""
    try:
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Subject=f'Contrato {contract_id} - {event_type}',
            Message=message,
            MessageAttributes={
                'contract_id': {
                    'DataType': 'String',
                    'StringValue': contract_id
                },
                'event_type': {
                    'DataType': 'String',
                    'StringValue': event_type
                }
            }
        )
        
        logger.info(f"Notificación enviada para contrato {contract_id}: {event_type}")
        
    except Exception as e:
        logger.error(f"Error enviando notificación: {str(e)}")

def initiate_service_activation(contract_id):
    """Iniciar proceso de activación del servicio"""
    try:
        # En un sistema real, esto podría:
        # 1. Crear registros de vehículos en el sistema
        # 2. Generar certificados IoT para dispositivos
        # 3. Configurar usuarios y permisos
        # 4. Programar instalación de dispositivos
        # 5. Enviar kits de bienvenida
        
        logger.info(f"Iniciando activación de servicio para contrato {contract_id}")
        
        # Por ahora, solo actualizamos el estado
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET service_activation_initiated = :initiated, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':initiated': int(datetime.utcnow().timestamp()),
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        
    except Exception as e:
        logger.error(f"Error iniciando activación de servicio: {str(e)}")

def create_response(status_code, body):
    """Crear respuesta HTTP estándar"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }
