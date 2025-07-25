import json
import boto3
import uuid
from datetime import datetime
import os

dynamodb = boto3.resource('dynamodb')
inventory_table = dynamodb.Table(os.environ['INVENTORY_TABLE'])

def handler(event, context):
    """
    API Lambda para gestión de inventario de ventas
    Maneja operaciones CRUD para inventario de vehículos
    """
    
    try:
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        if http_method == 'GET':
            if 'inventoryId' in path_parameters:
                return get_inventory_by_id(path_parameters['inventoryId'])
            else:
                return get_all_inventory(query_parameters)
                
        elif http_method == 'POST':
            body = json.loads(event['body'])
            return create_inventory_item(body)
            
        elif http_method == 'PUT':
            inventory_id = path_parameters['inventoryId']
            body = json.loads(event['body'])
            return update_inventory_item(inventory_id, body)
            
        elif http_method == 'DELETE':
            inventory_id = path_parameters['inventoryId']
            return delete_inventory_item(inventory_id)
            
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }

def get_all_inventory(query_params):
    """Obtener todo el inventario con filtros opcionales"""
    try:
        # Parámetros de paginación
        limit = int(query_params.get('limit', 50))
        last_key = query_params.get('lastKey')
        
        # Filtros
        vehicle_type = query_params.get('vehicle_type')
        status = query_params.get('status')
        price_range = query_params.get('price_range')
        
        scan_kwargs = {
            'Limit': limit
        }
        
        if last_key:
            scan_kwargs['ExclusiveStartKey'] = {'inventory_id': last_key}
            
        # Aplicar filtros
        filter_expressions = []
        expression_values = {}
        expression_names = {}
        
        if vehicle_type:
            filter_expressions.append('#vehicle_type = :vehicle_type')
            expression_names['#vehicle_type'] = 'vehicle_type'
            expression_values[':vehicle_type'] = vehicle_type
            
        if status:
            filter_expressions.append('#status = :status')
            expression_names['#status'] = 'status'
            expression_values[':status'] = status
            
        if price_range:
            filter_expressions.append('price_range = :price_range')
            expression_values[':price_range'] = price_range
            
        if filter_expressions:
            scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_kwargs['ExpressionAttributeValues'] = expression_values
            if expression_names:
                scan_kwargs['ExpressionAttributeNames'] = expression_names
            
        response = inventory_table.scan(**scan_kwargs)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'inventory': response['Items'],
                'lastKey': response.get('LastEvaluatedKey', {}).get('inventory_id'),
                'count': response['Count']
            }, default=str)
        }
        
    except Exception as e:
        print(f"Error getting inventory: {str(e)}")
        raise

def get_inventory_by_id(inventory_id):
    """Obtener un item de inventario específico por ID"""
    try:
        response = inventory_table.get_item(Key={'inventory_id': inventory_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Inventory item not found'})
            }
            
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response['Item'], default=str)
        }
        
    except Exception as e:
        print(f"Error getting inventory item {inventory_id}: {str(e)}")
        raise

def create_inventory_item(item_data):
    """Crear un nuevo item de inventario"""
    try:
        inventory_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp())
        
        # Validar campos requeridos
        required_fields = ['vehicle_type', 'model', 'year', 'price', 'quantity']
        for field in required_fields:
            if field not in item_data:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Missing required field: {field}'})
                }
        
        # Determinar rango de precio
        price = float(item_data['price'])
        if price < 20000:
            price_range = 'low'
        elif price < 50000:
            price_range = 'medium'
        else:
            price_range = 'high'
        
        item = {
            'inventory_id': inventory_id,
            'vehicle_type': item_data['vehicle_type'],
            'brand': item_data.get('brand', ''),
            'model': item_data['model'],
            'year': int(item_data['year']),
            'price': price,
            'price_range': price_range,
            'quantity': int(item_data['quantity']),
            'available_quantity': int(item_data['quantity']),
            'status': item_data.get('status', 'available'),
            'features': item_data.get('features', []),
            'description': item_data.get('description', ''),
            'images': item_data.get('images', []),
            'specifications': item_data.get('specifications', {}),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        inventory_table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(item, default=str)
        }
        
    except Exception as e:
        print(f"Error creating inventory item: {str(e)}")
        raise

def update_inventory_item(inventory_id, item_data):
    """Actualizar un item de inventario existente"""
    try:
        # Verificar que el item existe
        response = inventory_table.get_item(Key={'inventory_id': inventory_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Inventory item not found'})
            }
        
        timestamp = int(datetime.now().timestamp())
        
        # Construir expresión de actualización
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': timestamp}
        
        updatable_fields = [
            'vehicle_type', 'brand', 'model', 'year', 'price', 'quantity', 
            'available_quantity', 'status', 'features', 'description', 
            'images', 'specifications'
        ]
        
        for field in updatable_fields:
            if field in item_data:
                if field == 'price':
                    # Actualizar también el rango de precio
                    price = float(item_data['price'])
                    if price < 20000:
                        price_range = 'low'
                    elif price < 50000:
                        price_range = 'medium'
                    else:
                        price_range = 'high'
                    
                    update_expression += f", price = :price, price_range = :price_range"
                    expression_values[':price'] = price
                    expression_values[':price_range'] = price_range
                else:
                    update_expression += f", {field} = :{field}"
                    expression_values[f":{field}"] = item_data[field]
        
        inventory_table.update_item(
            Key={'inventory_id': inventory_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )
        
        # Obtener el item actualizado
        updated_response = inventory_table.get_item(Key={'inventory_id': inventory_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(updated_response['Item'], default=str)
        }
        
    except Exception as e:
        print(f"Error updating inventory item {inventory_id}: {str(e)}")
        raise

def delete_inventory_item(inventory_id):
    """Eliminar un item de inventario (soft delete)"""
    try:
        # Verificar que el item existe
        response = inventory_table.get_item(Key={'inventory_id': inventory_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Inventory item not found'})
            }
        
        timestamp = int(datetime.now().timestamp())
        
        # Soft delete - cambiar status a 'deleted'
        inventory_table.update_item(
            Key={'inventory_id': inventory_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'deleted',
                ':updated_at': timestamp
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Inventory item deleted successfully'})
        }
        
    except Exception as e:
        print(f"Error deleting inventory item {inventory_id}: {str(e)}")
        raise
