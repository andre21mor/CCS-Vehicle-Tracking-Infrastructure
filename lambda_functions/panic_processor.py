import json
import boto3
import os
from datetime import datetime
import logging

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """
    Procesa alertas críticas del botón de pánico de vehículos
    """
    try:
        logger.info(f"Procesando evento de pánico: {json.dumps(event)}")
        
        # Extraer datos del evento IoT
        vehicle_id = event.get('vehicle_id')
        location = event.get('location', {})
        timestamp = event.get('timestamp', datetime.utcnow().isoformat())
        panic_type = event.get('panic_type', 'EMERGENCY')
        driver_info = event.get('driver_info', {})
        
        if not vehicle_id:
            raise ValueError("vehicle_id es requerido")
        
        # Preparar mensaje de alerta
        alert_message = {
            "alert_type": "PANIC_BUTTON",
            "vehicle_id": vehicle_id,
            "timestamp": timestamp,
            "location": {
                "latitude": location.get('lat'),
                "longitude": location.get('lng'),
                "address": location.get('address', 'Dirección no disponible')
            },
            "panic_type": panic_type,
            "driver": {
                "name": driver_info.get('name', 'No identificado'),
                "license": driver_info.get('license', 'N/A')
            },
            "priority": "CRITICAL",
            "requires_immediate_response": True
        }
        
        # Enviar notificación SNS a autoridades
        sns_topic_arn = os.environ['SNS_TOPIC_ARN']
        
        sns_response = sns.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps(alert_message, indent=2),
            Subject=f"🚨 ALERTA CRÍTICA - Botón de Pánico Activado - Vehículo {vehicle_id}",
            MessageAttributes={
                'alert_type': {
                    'DataType': 'String',
                    'StringValue': 'PANIC_BUTTON'
                },
                'priority': {
                    'DataType': 'String',
                    'StringValue': 'CRITICAL'
                },
                'vehicle_id': {
                    'DataType': 'String',
                    'StringValue': vehicle_id
                }
            }
        )
        
        logger.info(f"Notificación SNS enviada: {sns_response['MessageId']}")
        
        # Registrar en DynamoDB para auditoría
        table_name = f"vehicle-tracking-{os.environ['ENVIRONMENT']}-panic-events"
        table = dynamodb.Table(table_name)
        
        panic_record = {
            'vehicle_id': vehicle_id,
            'timestamp': int(datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()),
            'alert_data': alert_message,
            'sns_message_id': sns_response['MessageId'],
            'processed_at': datetime.utcnow().isoformat(),
            'status': 'NOTIFIED'
        }
        
        table.put_item(Item=panic_record)
        
        # Respuesta exitosa
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Alerta de pánico procesada exitosamente',
                'vehicle_id': vehicle_id,
                'sns_message_id': sns_response['MessageId'],
                'timestamp': timestamp
            })
        }
        
    except Exception as e:
        logger.error(f"Error procesando alerta de pánico: {str(e)}")
        
        # En caso de error, aún intentar enviar una notificación básica
        try:
            emergency_message = f"ERROR: Fallo al procesar alerta de pánico del vehículo {event.get('vehicle_id', 'DESCONOCIDO')}. Error: {str(e)}"
            sns.publish(
                TopicArn=os.environ['SNS_TOPIC_ARN'],
                Message=emergency_message,
                Subject="🚨 ERROR CRÍTICO - Fallo en procesamiento de pánico"
            )
        except:
            pass
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Error procesando alerta de pánico',
                'details': str(e)
            })
        }
