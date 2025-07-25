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
kinesis = boto3.client('kinesis')

def handler(event, context):
    """
    API para gestión de vehículos
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
        if http_method == 'GET' and path == '/vehicles':
            return list_vehicles(user_info, query_parameters)
        elif http_method == 'GET' and path.startswith('/vehicles/') and len(path.split('/')) == 3:
            vehicle_id = path_parameters.get('vehicleId')
            return get_vehicle_by_id(user_info, vehicle_id)
        elif http_method == 'POST' and path == '/vehicles':
            return create_vehicle(user_info, json.loads(body) if body else {})
        elif http_method == 'PUT' and path.startswith('/vehicles/'):
            vehicle_id = path_parameters.get('vehicleId')
            return update_vehicle(user_info, vehicle_id, json.loads(body) if body else {})
        elif http_method == 'DELETE' and path.startswith('/vehicles/'):
            vehicle_id = path_parameters.get('vehicleId')
            return delete_vehicle(user_info, vehicle_id)
        else:
            return create_response(404, {'error': 'Endpoint no encontrado'})
            
    except Exception as e:
        logger.error(f"Error en vehicle_management: {str(e)}")
        return create_response(500, {'error': 'Error interno del servidor'})

def extract_user_info(event):
    """Extraer información del usuario desde el contexto de Cognito"""
    try:
        claims = event['requestContext']['authorizer']['claims']
        return {
            'user_id': claims['sub'],
            'email': claims['email'],
            'company_name': claims.get('custom:company_name', 'N/A'),
            'fleet_size': claims.get('custom:fleet_size', '0')
        }
    except:
        return {
            'user_id': 'anonymous',
            'email': 'anonymous@example.com',
            'company_name': 'Test Company',
            'fleet_size': '0'
        }

def list_vehicles(user_info, query_params):
    """Listar vehículos del usuario"""
    try:
        table_name = os.environ['DYNAMODB_TABLE']
        table = dynamodb.Table(table_name)
        
        # Parámetros de consulta
        limit = int(query_params.get('limit', 50))
        offset = int(query_params.get('offset', 0))
        status_filter = query_params.get('status')
        
        # Consultar vehículos del usuario
        response = table.scan(
            FilterExpression='owner_id = :owner_id',
            ExpressionAttributeValues={
                ':owner_id': user_info['user_id']
            },
            Limit=limit
        )
        
        vehicles = response.get('Items', [])
        
        # Filtrar por estado si se especifica
        if status_filter:
            vehicles = [v for v in vehicles if v.get('status') == status_filter]
        
        # Convertir Decimal a float para JSON
        vehicles = convert_decimals(vehicles)
        
        # Agregar información de estado en tiempo real
        for vehicle in vehicles:
            vehicle['real_time_status'] = get_vehicle_real_time_status(vehicle['vehicle_id'])
        
        return create_response(200, {
            'vehicles': vehicles[offset:offset+limit],
            'total': len(vehicles),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error listando vehículos: {str(e)}")
        return create_response(500, {'error': 'Error obteniendo vehículos'})

def get_vehicle_by_id(user_info, vehicle_id):
    """Obtener vehículo específico"""
    try:
        table_name = os.environ['DYNAMODB_TABLE']
        table = dynamodb.Table(table_name)
        
        response = table.get_item(
            Key={'vehicle_id': vehicle_id}
        )
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Vehículo no encontrado'})
        
        vehicle = response['Item']
        
        # Verificar que el vehículo pertenece al usuario
        if vehicle.get('owner_id') != user_info['user_id']:
            return create_response(403, {'error': 'Acceso denegado'})
        
        # Convertir Decimal a float
        vehicle = convert_decimals(vehicle)
        
        # Agregar información en tiempo real
        vehicle['real_time_status'] = get_vehicle_real_time_status(vehicle_id)
        vehicle['recent_telemetry'] = get_recent_telemetry(vehicle_id)
        
        return create_response(200, vehicle)
        
    except Exception as e:
        logger.error(f"Error obteniendo vehículo {vehicle_id}: {str(e)}")
        return create_response(500, {'error': 'Error obteniendo vehículo'})

def create_vehicle(user_info, vehicle_data):
    """Crear nuevo vehículo"""
    try:
        table_name = os.environ['DYNAMODB_TABLE']
        table = dynamodb.Table(table_name)
        
        # Generar ID único para el vehículo
        vehicle_id = f"VH{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Datos del vehículo
        vehicle = {
            'vehicle_id': vehicle_id,
            'owner_id': user_info['user_id'],
            'license_plate': vehicle_data.get('license_plate', ''),
            'make': vehicle_data.get('make', ''),
            'model': vehicle_data.get('model', ''),
            'year': vehicle_data.get('year', 2024),
            'vin': vehicle_data.get('vin', ''),
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'driver_assigned': vehicle_data.get('driver_assigned', ''),
            'route_assigned': vehicle_data.get('route_assigned', ''),
            'fuel_capacity': vehicle_data.get('fuel_capacity', 100),
            'max_speed': vehicle_data.get('max_speed', 120),
            'vehicle_type': vehicle_data.get('vehicle_type', 'truck'),
            'insurance_policy': vehicle_data.get('insurance_policy', ''),
            'maintenance_schedule': vehicle_data.get('maintenance_schedule', {}),
            'iot_device_id': f"IOT_{vehicle_id}",
            'alerts_enabled': True,
            'tracking_enabled': True
        }
        
        # Guardar en DynamoDB
        table.put_item(Item=vehicle)
        
        # Convertir Decimal a float
        vehicle = convert_decimals(vehicle)
        
        logger.info(f"Vehículo creado: {vehicle_id}")
        
        return create_response(201, {
            'message': 'Vehículo creado exitosamente',
            'vehicle': vehicle
        })
        
    except Exception as e:
        logger.error(f"Error creando vehículo: {str(e)}")
        return create_response(500, {'error': 'Error creando vehículo'})

def update_vehicle(user_info, vehicle_id, update_data):
    """Actualizar vehículo existente"""
    try:
        table_name = os.environ['DYNAMODB_TABLE']
        table = dynamodb.Table(table_name)
        
        # Verificar que el vehículo existe y pertenece al usuario
        response = table.get_item(Key={'vehicle_id': vehicle_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Vehículo no encontrado'})
        
        vehicle = response['Item']
        if vehicle.get('owner_id') != user_info['user_id']:
            return create_response(403, {'error': 'Acceso denegado'})
        
        # Campos actualizables
        updatable_fields = [
            'license_plate', 'make', 'model', 'year', 'vin', 'status',
            'driver_assigned', 'route_assigned', 'fuel_capacity', 'max_speed',
            'vehicle_type', 'insurance_policy', 'maintenance_schedule',
            'alerts_enabled', 'tracking_enabled'
        ]
        
        # Construir expresión de actualización
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': datetime.utcnow().isoformat()}
        
        for field in updatable_fields:
            if field in update_data:
                update_expression += f", {field} = :{field}"
                expression_values[f":{field}"] = update_data[field]
        
        # Actualizar en DynamoDB
        response = table.update_item(
            Key={'vehicle_id': vehicle_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )
        
        updated_vehicle = convert_decimals(response['Attributes'])
        
        logger.info(f"Vehículo actualizado: {vehicle_id}")
        
        return create_response(200, {
            'message': 'Vehículo actualizado exitosamente',
            'vehicle': updated_vehicle
        })
        
    except Exception as e:
        logger.error(f"Error actualizando vehículo {vehicle_id}: {str(e)}")
        return create_response(500, {'error': 'Error actualizando vehículo'})

def delete_vehicle(user_info, vehicle_id):
    """Eliminar vehículo (soft delete)"""
    try:
        table_name = os.environ['DYNAMODB_TABLE']
        table = dynamodb.Table(table_name)
        
        # Verificar que el vehículo existe y pertenece al usuario
        response = table.get_item(Key={'vehicle_id': vehicle_id})
        if 'Item' not in response:
            return create_response(404, {'error': 'Vehículo no encontrado'})
        
        vehicle = response['Item']
        if vehicle.get('owner_id') != user_info['user_id']:
            return create_response(403, {'error': 'Acceso denegado'})
        
        # Soft delete - cambiar estado a 'deleted'
        table.update_item(
            Key={'vehicle_id': vehicle_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at, deleted_at = :deleted_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'deleted',
                ':updated_at': datetime.utcnow().isoformat(),
                ':deleted_at': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Vehículo eliminado: {vehicle_id}")
        
        return create_response(200, {
            'message': 'Vehículo eliminado exitosamente',
            'vehicle_id': vehicle_id
        })
        
    except Exception as e:
        logger.error(f"Error eliminando vehículo {vehicle_id}: {str(e)}")
        return create_response(500, {'error': 'Error eliminando vehículo'})

def get_vehicle_real_time_status(vehicle_id):
    """Obtener estado en tiempo real del vehículo"""
    try:
        # Consultar tabla de estado en tiempo real
        status_table = dynamodb.Table(f"{os.environ['DYNAMODB_TABLE'].replace('vehicles', 'vehicle-status')}")
        
        response = status_table.query(
            KeyConditionExpression='vehicle_id = :vehicle_id',
            ExpressionAttributeValues={':vehicle_id': vehicle_id},
            ScanIndexForward=False,  # Orden descendente por timestamp
            Limit=1
        )
        
        if response['Items']:
            latest_status = convert_decimals(response['Items'][0])
            return {
                'is_online': True,
                'last_seen': latest_status.get('timestamp'),
                'location': latest_status.get('location', {}),
                'speed': latest_status.get('speed', 0),
                'fuel_level': latest_status.get('fuel_level', 0),
                'engine_temp': latest_status.get('engine_temp', 0),
                'status': 'active'
            }
        else:
            return {
                'is_online': False,
                'last_seen': None,
                'location': {},
                'speed': 0,
                'fuel_level': 0,
                'engine_temp': 0,
                'status': 'offline'
            }
            
    except Exception as e:
        logger.error(f"Error obteniendo estado en tiempo real: {str(e)}")
        return {
            'is_online': False,
            'status': 'unknown',
            'error': 'No se pudo obtener estado'
        }

def get_recent_telemetry(vehicle_id, limit=10):
    """Obtener telemetría reciente del vehículo"""
    try:
        status_table = dynamodb.Table(f"{os.environ['DYNAMODB_TABLE'].replace('vehicles', 'vehicle-status')}")
        
        response = status_table.query(
            KeyConditionExpression='vehicle_id = :vehicle_id',
            ExpressionAttributeValues={':vehicle_id': vehicle_id},
            ScanIndexForward=False,
            Limit=limit
        )
        
        return convert_decimals(response.get('Items', []))
        
    except Exception as e:
        logger.error(f"Error obteniendo telemetría reciente: {str(e)}")
        return []

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
