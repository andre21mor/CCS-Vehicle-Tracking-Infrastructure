import json
import boto3
import os
from datetime import datetime
import logging
import base64

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

def handler(event, context):
    """
    Procesa datos de video de vehículos y realiza análisis con Rekognition
    """
    try:
        logger.info(f"Procesando datos de video: {json.dumps(event)}")
        
        # Extraer datos del evento IoT
        vehicle_id = event.get('vehicle_id')
        video_data = event.get('video_data', {})
        timestamp = event.get('timestamp', datetime.utcnow().isoformat())
        video_type = event.get('video_type', 'CONTINUOUS')  # CONTINUOUS, EVENT, PANIC
        
        if not vehicle_id:
            raise ValueError("vehicle_id es requerido")
        
        bucket_name = os.environ['S3_BUCKET']
        
        # Procesar según el tipo de video
        if video_type == 'PANIC':
            # Video de emergencia - procesamiento prioritario
            result = process_emergency_video(vehicle_id, video_data, timestamp, bucket_name)
        elif video_type == 'EVENT':
            # Video de evento específico (frenado brusco, accidente, etc.)
            result = process_event_video(vehicle_id, video_data, timestamp, bucket_name)
        else:
            # Video continuo - procesamiento estándar
            result = process_continuous_video(vehicle_id, video_data, timestamp, bucket_name)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Video procesado exitosamente',
                'vehicle_id': vehicle_id,
                'video_type': video_type,
                'result': result,
                'timestamp': timestamp
            })
        }
        
    except Exception as e:
        logger.error(f"Error procesando video: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Error procesando video',
                'details': str(e)
            })
        }

def process_emergency_video(vehicle_id, video_data, timestamp, bucket_name):
    """
    Procesa video de emergencia con análisis inmediato
    """
    try:
        # Generar clave S3 para video de emergencia
        s3_key = f"emergency/{vehicle_id}/{timestamp}/video.mp4"
        
        # Si hay datos de video en base64, decodificar y subir
        if video_data.get('base64_data'):
            video_bytes = base64.b64decode(video_data['base64_data'])
            
            # Subir a S3 con metadatos de emergencia
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=video_bytes,
                ContentType='video/mp4',
                Metadata={
                    'vehicle_id': vehicle_id,
                    'video_type': 'EMERGENCY',
                    'timestamp': timestamp,
                    'priority': 'CRITICAL'
                },
                StorageClass='STANDARD_IA'  # Acceso inmediato pero costo optimizado
            )
            
            logger.info(f"Video de emergencia subido: s3://{bucket_name}/{s3_key}")
        
        # Análisis con Rekognition si hay frame de imagen
        analysis_result = {}
        if video_data.get('frame_image'):
            frame_bytes = base64.b64decode(video_data['frame_image'])
            
            # Detectar objetos y personas
            detection_response = rekognition.detect_labels(
                Image={'Bytes': frame_bytes},
                MaxLabels=20,
                MinConfidence=70
            )
            
            # Detectar caras para identificación
            face_response = rekognition.detect_faces(
                Image={'Bytes': frame_bytes},
                Attributes=['ALL']
            )
            
            analysis_result = {
                'objects_detected': [label['Name'] for label in detection_response['Labels']],
                'faces_detected': len(face_response['FaceDetails']),
                'confidence_scores': {label['Name']: label['Confidence'] for label in detection_response['Labels']},
                'emergency_indicators': identify_emergency_indicators(detection_response['Labels'])
            }
            
            logger.info(f"Análisis de emergencia completado: {analysis_result}")
        
        return {
            's3_location': f"s3://{bucket_name}/{s3_key}",
            'analysis': analysis_result,
            'processing_type': 'EMERGENCY_PRIORITY'
        }
        
    except Exception as e:
        logger.error(f"Error procesando video de emergencia: {str(e)}")
        raise

def process_event_video(vehicle_id, video_data, timestamp, bucket_name):
    """
    Procesa video de eventos específicos
    """
    try:
        event_type = video_data.get('event_type', 'UNKNOWN')
        s3_key = f"events/{vehicle_id}/{event_type}/{timestamp}/video.mp4"
        
        # Subir video si está disponible
        if video_data.get('base64_data'):
            video_bytes = base64.b64decode(video_data['base64_data'])
            
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=video_bytes,
                ContentType='video/mp4',
                Metadata={
                    'vehicle_id': vehicle_id,
                    'video_type': 'EVENT',
                    'event_type': event_type,
                    'timestamp': timestamp
                },
                StorageClass='STANDARD_IA'
            )
        
        return {
            's3_location': f"s3://{bucket_name}/{s3_key}",
            'event_type': event_type,
            'processing_type': 'EVENT_ANALYSIS'
        }
        
    except Exception as e:
        logger.error(f"Error procesando video de evento: {str(e)}")
        raise

def process_continuous_video(vehicle_id, video_data, timestamp, bucket_name):
    """
    Procesa video continuo con archivado optimizado
    """
    try:
        s3_key = f"continuous/{vehicle_id}/{timestamp[:10]}/{timestamp}/video.mp4"
        
        # Para video continuo, usar almacenamiento más económico
        if video_data.get('base64_data'):
            video_bytes = base64.b64decode(video_data['base64_data'])
            
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=video_bytes,
                ContentType='video/mp4',
                Metadata={
                    'vehicle_id': vehicle_id,
                    'video_type': 'CONTINUOUS',
                    'timestamp': timestamp
                },
                StorageClass='GLACIER'  # Archivado a largo plazo
            )
        
        return {
            's3_location': f"s3://{bucket_name}/{s3_key}",
            'processing_type': 'CONTINUOUS_ARCHIVE'
        }
        
    except Exception as e:
        logger.error(f"Error procesando video continuo: {str(e)}")
        raise

def identify_emergency_indicators(labels):
    """
    Identifica indicadores de emergencia en las etiquetas detectadas
    """
    emergency_keywords = [
        'Fire', 'Smoke', 'Accident', 'Crash', 'Blood', 'Weapon',
        'Police', 'Ambulance', 'Emergency', 'Danger', 'Violence'
    ]
    
    indicators = []
    for label in labels:
        if any(keyword.lower() in label['Name'].lower() for keyword in emergency_keywords):
            indicators.append({
                'indicator': label['Name'],
                'confidence': label['Confidence']
            })
    
    return indicators
