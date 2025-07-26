import json
import boto3
import logging
import uuid
from datetime import datetime, timedelta
from urllib.parse import unquote_plus

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# Environment variables
RESULTS_TABLE = os.environ['RESULTS_TABLE']
ALERTS_TOPIC = os.environ['ALERTS_TOPIC']

# DynamoDB table
results_table = dynamodb.Table(RESULTS_TABLE)

def lambda_handler(event, context):
    """
    Process vehicle images/video frames with Amazon Rekognition
    """
    try:
        for record in event['Records']:
            # Parse S3 event
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            
            logger.info(f"Processing image: s3://{bucket}/{key}")
            
            # Extract metadata from S3 key
            metadata = extract_metadata_from_key(key)
            
            # Process image with Rekognition
            analysis_results = process_image(bucket, key, metadata)
            
            # Store results in DynamoDB
            store_analysis_results(analysis_results)
            
            # Check for alerts
            check_and_send_alerts(analysis_results)
            
        return {
            'statusCode': 200,
            'body': json.dumps('Rekognition processing completed successfully')
        }
        
    except Exception as e:
        logger.error(f"Error processing Rekognition: {str(e)}")
        raise

def extract_metadata_from_key(s3_key):
    """
    Extract vehicle and timestamp info from S3 key
    Expected format: analysis-required/VH001/2025/01/25/10/frame_103000.jpg
    """
    try:
        parts = s3_key.split('/')
        
        return {
            'vehicle_id': parts[1],
            'year': parts[2],
            'month': parts[3],
            'day': parts[4],
            'hour': parts[5],
            'filename': parts[6],
            'timestamp': f"{parts[2]}-{parts[3]}-{parts[4]}T{parts[5]}:30:00Z"
        }
    except Exception as e:
        logger.error(f"Error extracting metadata from key {s3_key}: {str(e)}")
        return {
            'vehicle_id': 'unknown',
            'timestamp': datetime.now().isoformat()
        }

def process_image(bucket, key, metadata):
    """
    Process image with multiple Rekognition services
    """
    analysis_id = str(uuid.uuid4())
    
    results = {
        'analysis_id': analysis_id,
        'vehicle_id': metadata['vehicle_id'],
        'timestamp': metadata['timestamp'],
        's3_location': f"s3://{bucket}/{key}",
        'ttl': int((datetime.now() + timedelta(days=90)).timestamp()),
        'analyses': {}
    }
    
    try:
        # 1. Driver Behavior Analysis - Face Detection
        face_analysis = analyze_driver_behavior(bucket, key)
        results['analyses']['driver_behavior'] = face_analysis
        
        # 2. Safety Analysis - Object Detection
        safety_analysis = analyze_safety_conditions(bucket, key)
        results['analyses']['safety'] = safety_analysis
        
        # 3. Text Recognition - License plates, signs
        text_analysis = analyze_text_content(bucket, key)
        results['analyses']['text'] = text_analysis
        
        # 4. Scene Analysis - General labels
        scene_analysis = analyze_scene_content(bucket, key)
        results['analyses']['scene'] = scene_analysis
        
        logger.info(f"Completed analysis for {analysis_id}")
        
    except Exception as e:
        logger.error(f"Error in Rekognition analysis: {str(e)}")
        results['error'] = str(e)
    
    return results

def analyze_driver_behavior(bucket, key):
    """
    Analyze driver behavior using face detection
    """
    try:
        response = rekognition.detect_faces(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            Attributes=['ALL']
        )
        
        behavior_analysis = {
            'faces_detected': len(response['FaceDetails']),
            'driver_alerts': []
        }
        
        for face in response['FaceDetails']:
            # Check for drowsiness indicators
            if face['EyesOpen']['Value'] == False and face['EyesOpen']['Confidence'] > 80:
                behavior_analysis['driver_alerts'].append({
                    'type': 'eyes_closed',
                    'confidence': face['EyesOpen']['Confidence'],
                    'severity': 'high'
                })
            
            # Check for distraction (looking away)
            pose = face['Pose']
            if abs(pose['Yaw']) > 30 or abs(pose['Pitch']) > 20:
                behavior_analysis['driver_alerts'].append({
                    'type': 'looking_away',
                    'confidence': 85,
                    'severity': 'medium',
                    'yaw': pose['Yaw'],
                    'pitch': pose['Pitch']
                })
            
            # Check emotions for stress/anger
            emotions = face.get('Emotions', [])
            for emotion in emotions:
                if emotion['Type'] in ['ANGRY', 'DISGUSTED'] and emotion['Confidence'] > 70:
                    behavior_analysis['driver_alerts'].append({
                        'type': 'negative_emotion',
                        'emotion': emotion['Type'],
                        'confidence': emotion['Confidence'],
                        'severity': 'medium'
                    })
        
        return behavior_analysis
        
    except Exception as e:
        logger.error(f"Error in driver behavior analysis: {str(e)}")
        return {'error': str(e)}

def analyze_safety_conditions(bucket, key):
    """
    Analyze safety conditions using object detection
    """
    try:
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=50,
            MinConfidence=70
        )
        
        safety_analysis = {
            'safety_alerts': [],
            'detected_objects': []
        }
        
        for label in response['Labels']:
            label_name = label['Name'].lower()
            confidence = label['Confidence']
            
            # Store all detected objects
            safety_analysis['detected_objects'].append({
                'name': label['Name'],
                'confidence': confidence
            })
            
            # Check for safety violations
            if label_name in ['mobile phone', 'cell phone', 'smartphone']:
                safety_analysis['safety_alerts'].append({
                    'type': 'phone_usage',
                    'confidence': confidence,
                    'severity': 'high'
                })
            
            elif label_name in ['alcohol', 'beer', 'wine']:
                safety_analysis['safety_alerts'].append({
                    'type': 'alcohol_detected',
                    'confidence': confidence,
                    'severity': 'critical'
                })
            
            elif label_name in ['cigarette', 'smoking']:
                safety_analysis['safety_alerts'].append({
                    'type': 'smoking',
                    'confidence': confidence,
                    'severity': 'medium'
                })
            
            # Check for emergency situations
            elif label_name in ['fire', 'smoke', 'accident']:
                safety_analysis['safety_alerts'].append({
                    'type': 'emergency_situation',
                    'detected': label['Name'],
                    'confidence': confidence,
                    'severity': 'critical'
                })
        
        return safety_analysis
        
    except Exception as e:
        logger.error(f"Error in safety analysis: {str(e)}")
        return {'error': str(e)}

def analyze_text_content(bucket, key):
    """
    Analyze text content for license plates, signs, etc.
    """
    try:
        response = rekognition.detect_text(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        text_analysis = {
            'license_plates': [],
            'traffic_signs': [],
            'other_text': []
        }
        
        for text_detection in response['TextDetections']:
            if text_detection['Type'] == 'LINE':
                detected_text = text_detection['DetectedText']
                confidence = text_detection['Confidence']
                
                # License plate pattern detection (simplified)
                if is_license_plate_pattern(detected_text):
                    text_analysis['license_plates'].append({
                        'text': detected_text,
                        'confidence': confidence,
                        'bounding_box': text_detection['Geometry']['BoundingBox']
                    })
                
                # Traffic sign keywords
                elif any(keyword in detected_text.upper() for keyword in ['STOP', 'SPEED', 'LIMIT', 'YIELD', 'NO']):
                    text_analysis['traffic_signs'].append({
                        'text': detected_text,
                        'confidence': confidence
                    })
                
                else:
                    text_analysis['other_text'].append({
                        'text': detected_text,
                        'confidence': confidence
                    })
        
        return text_analysis
        
    except Exception as e:
        logger.error(f"Error in text analysis: {str(e)}")
        return {'error': str(e)}

def analyze_scene_content(bucket, key):
    """
    General scene analysis for context
    """
    try:
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=20,
            MinConfidence=80
        )
        
        scene_analysis = {
            'environment': 'unknown',
            'weather_conditions': [],
            'road_conditions': [],
            'time_of_day': 'unknown'
        }
        
        for label in response['Labels']:
            label_name = label['Name'].lower()
            
            # Environment detection
            if label_name in ['highway', 'road', 'street']:
                scene_analysis['environment'] = 'urban'
            elif label_name in ['countryside', 'field', 'mountain']:
                scene_analysis['environment'] = 'rural'
            
            # Weather conditions
            if label_name in ['rain', 'snow', 'fog']:
                scene_analysis['weather_conditions'].append(label['Name'])
            
            # Time of day
            if label_name in ['sunset', 'sunrise', 'night']:
                scene_analysis['time_of_day'] = label['Name']
        
        return scene_analysis
        
    except Exception as e:
        logger.error(f"Error in scene analysis: {str(e)}")
        return {'error': str(e)}

def is_license_plate_pattern(text):
    """
    Simple license plate pattern detection
    """
    import re
    
    # Common license plate patterns (adjust for your region)
    patterns = [
        r'^[A-Z]{3}-\d{3}$',  # ABC-123
        r'^\d{3}-[A-Z]{3}$',  # 123-ABC
        r'^[A-Z]{2}\d{4}$',   # AB1234
        r'^\d{3}[A-Z]{3}$'    # 123ABC
    ]
    
    for pattern in patterns:
        if re.match(pattern, text.upper()):
            return True
    
    return False

def store_analysis_results(results):
    """
    Store analysis results in DynamoDB
    """
    try:
        # Convert any float values to Decimal for DynamoDB
        item = json.loads(json.dumps(results), parse_float=Decimal)
        
        results_table.put_item(Item=item)
        logger.info(f"Stored analysis results for {results['analysis_id']}")
        
    except Exception as e:
        logger.error(f"Error storing results: {str(e)}")
        raise

def check_and_send_alerts(results):
    """
    Check analysis results and send alerts if needed
    """
    try:
        alerts_to_send = []
        
        # Check driver behavior alerts
        driver_behavior = results['analyses'].get('driver_behavior', {})
        for alert in driver_behavior.get('driver_alerts', []):
            if alert['severity'] in ['high', 'critical']:
                alerts_to_send.append({
                    'type': 'driver_behavior',
                    'subtype': alert['type'],
                    'severity': alert['severity'],
                    'confidence': alert['confidence']
                })
        
        # Check safety alerts
        safety = results['analyses'].get('safety', {})
        for alert in safety.get('safety_alerts', []):
            if alert['severity'] in ['high', 'critical']:
                alerts_to_send.append({
                    'type': 'safety_violation',
                    'subtype': alert['type'],
                    'severity': alert['severity'],
                    'confidence': alert['confidence']
                })
        
        # Send alerts via SNS
        if alerts_to_send:
            alert_message = {
                'vehicle_id': results['vehicle_id'],
                'timestamp': results['timestamp'],
                'analysis_id': results['analysis_id'],
                'alerts': alerts_to_send,
                's3_location': results['s3_location']
            }
            
            sns.publish(
                TopicArn=ALERTS_TOPIC,
                Message=json.dumps(alert_message),
                Subject=f"Vehicle Safety Alert: {results['vehicle_id']}"
            )
            
            logger.info(f"Sent {len(alerts_to_send)} alerts for vehicle {results['vehicle_id']}")
        
    except Exception as e:
        logger.error(f"Error sending alerts: {str(e)}")
        raise
