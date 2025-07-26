import json
import boto3
import logging
from datetime import datetime, timedelta
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Table references
hot_table = dynamodb.Table('vehicle-tracking-telemetry-hot')
warm_table = dynamodb.Table('vehicle-tracking-telemetry-warm')

def lambda_handler(event, context):
    """
    Process IoT telemetry data with hot/warm/cold storage strategy
    """
    try:
        for record in event['Records']:
            # Parse IoT message from Kinesis
            payload = json.loads(record['kinesis']['data'])
            
            # Process telemetry data
            process_telemetry(payload)
            
        return {
            'statusCode': 200,
            'body': json.dumps('Telemetry processed successfully')
        }
        
    except Exception as e:
        logger.error(f"Error processing telemetry: {str(e)}")
        raise

def process_telemetry(payload):
    """
    Process individual telemetry record
    """
    vehicle_id = payload['vehicle_id']
    timestamp = payload['timestamp']
    
    # 1. Hot Storage - Real-time access (48h TTL)
    store_hot_data(payload)
    
    # 2. Warm Storage - Recent analysis (30d TTL)
    store_warm_data(payload)
    
    # 3. Cold Storage - Historical analysis (S3)
    if should_archive_to_cold(payload):
        store_cold_data(payload)
    
    # 4. Process alerts if needed
    check_for_alerts(payload)

def store_hot_data(payload):
    """
    Store in DynamoDB hot table with TTL
    """
    try:
        # Calculate TTL (48 hours from now)
        ttl = int((datetime.now() + timedelta(hours=48)).timestamp())
        
        item = {
            'vehicle_id': payload['vehicle_id'],
            'timestamp': payload['timestamp'],
            'ttl': ttl,
            'location': payload.get('location', {}),
            'engine': payload.get('engine', {}),
            'diagnostics': payload.get('diagnostics', {}),
            'driver_behavior': payload.get('driver_behavior', {})
        }
        
        # Convert floats to Decimal for DynamoDB
        item = json.loads(json.dumps(item), parse_float=Decimal)
        
        hot_table.put_item(Item=item)
        logger.info(f"Stored hot data for vehicle {payload['vehicle_id']}")
        
    except Exception as e:
        logger.error(f"Error storing hot data: {str(e)}")
        raise

def store_warm_data(payload):
    """
    Store aggregated data for recent analysis
    """
    try:
        # Parse timestamp
        dt = datetime.fromisoformat(payload['timestamp'].replace('Z', '+00:00'))
        date_str = dt.strftime('%Y-%m-%d')
        hour_str = dt.strftime('%H')
        
        # Calculate TTL (30 days from now)
        ttl = int((datetime.now() + timedelta(days=30)).timestamp())
        
        # Create composite key for efficient querying
        vehicle_date = f"{payload['vehicle_id']}#{date_str}"
        
        # Aggregate data by hour
        aggregated_item = {
            'vehicle_date': vehicle_date,
            'timestamp': payload['timestamp'],
            'date': date_str,
            'hour': hour_str,
            'vehicle_id': payload['vehicle_id'],
            'ttl': ttl,
            'avg_speed': payload.get('location', {}).get('speed', 0),
            'max_rpm': payload.get('engine', {}).get('rpm', 0),
            'fuel_level': payload.get('engine', {}).get('fuel_level', 0),
            'events': extract_events(payload)
        }
        
        # Convert floats to Decimal
        aggregated_item = json.loads(json.dumps(aggregated_item), parse_float=Decimal)
        
        warm_table.put_item(Item=aggregated_item)
        logger.info(f"Stored warm data for vehicle {payload['vehicle_id']}")
        
    except Exception as e:
        logger.error(f"Error storing warm data: {str(e)}")
        raise

def should_archive_to_cold(payload):
    """
    Determine if data should be archived to S3
    Logic: Archive every 10th record or critical events
    """
    # Archive critical events immediately
    if has_critical_events(payload):
        return True
    
    # Archive every 10th record for sampling
    timestamp_hash = hash(payload['timestamp']) % 10
    return timestamp_hash == 0

def store_cold_data(payload):
    """
    Store in S3 for long-term analysis
    """
    try:
        # Parse timestamp for partitioning
        dt = datetime.fromisoformat(payload['timestamp'].replace('Z', '+00:00'))
        
        # Create S3 key with partitioning
        s3_key = f"telemetry/year={dt.year}/month={dt.month:02d}/day={dt.day:02d}/hour={dt.hour:02d}/{payload['vehicle_id']}_{payload['timestamp']}.json"
        
        # Store in S3
        s3.put_object(
            Bucket='vehicle-tracking-telemetry-cold',
            Key=s3_key,
            Body=json.dumps(payload),
            ContentType='application/json'
        )
        
        logger.info(f"Archived to cold storage: {s3_key}")
        
    except Exception as e:
        logger.error(f"Error storing cold data: {str(e)}")
        raise

def extract_events(payload):
    """
    Extract important events from telemetry data
    """
    events = []
    
    # Speed events
    speed = payload.get('location', {}).get('speed', 0)
    if speed > 80:  # Speed limit violation
        events.append('speed_violation')
    
    # Engine events
    engine = payload.get('engine', {})
    if engine.get('temperature', 0) > 100:
        events.append('engine_overheat')
    if engine.get('fuel_level', 100) < 10:
        events.append('low_fuel')
    
    # Driver behavior events
    behavior = payload.get('driver_behavior', {})
    if behavior.get('harsh_braking', 0) > 0:
        events.append('harsh_braking')
    if behavior.get('harsh_acceleration', 0) > 0:
        events.append('harsh_acceleration')
    
    return events

def has_critical_events(payload):
    """
    Check if payload contains critical events that need immediate archiving
    """
    events = extract_events(payload)
    critical_events = ['engine_overheat', 'panic_button', 'accident_detected']
    
    return any(event in critical_events for event in events)

def check_for_alerts(payload):
    """
    Check if alerts need to be triggered
    """
    events = extract_events(payload)
    
    if events:
        # Send to SNS for alert processing
        sns = boto3.client('sns')
        
        alert_message = {
            'vehicle_id': payload['vehicle_id'],
            'timestamp': payload['timestamp'],
            'events': events,
            'location': payload.get('location', {})
        }
        
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:vehicle-alerts',
            Message=json.dumps(alert_message),
            Subject=f"Vehicle Alert: {payload['vehicle_id']}"
        )
        
        logger.info(f"Alert sent for vehicle {payload['vehicle_id']}: {events}")
