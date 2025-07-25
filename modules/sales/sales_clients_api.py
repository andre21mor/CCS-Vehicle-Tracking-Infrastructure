import json
import boto3
import uuid
from datetime import datetime
import os

dynamodb = boto3.resource('dynamodb')
clients_table = dynamodb.Table(os.environ['CLIENTS_TABLE'])

def handler(event, context):
    """
    API Lambda para gestión de clientes de ventas
    Maneja operaciones CRUD para clientes
    """
    
    try:
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        if http_method == 'GET':
            if 'clientId' in path_parameters:
                return get_client_by_id(path_parameters['clientId'])
            else:
                return get_all_clients(query_parameters)
                
        elif http_method == 'POST':
            body = json.loads(event['body'])
            return create_client(body)
            
        elif http_method == 'PUT':
            client_id = path_parameters['clientId']
            body = json.loads(event['body'])
            return update_client(client_id, body)
            
        elif http_method == 'DELETE':
            client_id = path_parameters['clientId']
            return delete_client(client_id)
            
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

def get_all_clients(query_params):
    """Obtener todos los clientes con filtros opcionales"""
    try:
        # Parámetros de paginación
        limit = int(query_params.get('limit', 50))
        last_key = query_params.get('lastKey')
        
        # Filtros
        status = query_params.get('status')
        company = query_params.get('company')
        
        scan_kwargs = {
            'Limit': limit
        }
        
        if last_key:
            scan_kwargs['ExclusiveStartKey'] = {'client_id': last_key}
            
        if status:
            scan_kwargs['FilterExpression'] = 'attribute_exists(#status) AND #status = :status'
            scan_kwargs['ExpressionAttributeNames'] = {'#status': 'status'}
            scan_kwargs['ExpressionAttributeValues'] = {':status': status}
            
        response = clients_table.scan(**scan_kwargs)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'clients': response['Items'],
                'lastKey': response.get('LastEvaluatedKey', {}).get('client_id'),
                'count': response['Count']
            }, default=str)
        }
        
    except Exception as e:
        print(f"Error getting clients: {str(e)}")
        raise

def get_client_by_id(client_id):
    """Obtener un cliente específico por ID"""
    try:
        response = clients_table.get_item(Key={'client_id': client_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Client not found'})
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
        print(f"Error getting client {client_id}: {str(e)}")
        raise

def create_client(client_data):
    """Crear un nuevo cliente"""
    try:
        client_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp())
        
        # Validar campos requeridos
        required_fields = ['name', 'email', 'phone', 'company_name']
        for field in required_fields:
            if field not in client_data:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Missing required field: {field}'})
                }
        
        # Verificar si el email ya existe
        try:
            response = clients_table.query(
                IndexName='EmailIndex',
                KeyConditionExpression='email = :email',
                ExpressionAttributeValues={':email': client_data['email']}
            )
            if response['Items']:
                return {
                    'statusCode': 409,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Email already exists'})
                }
        except Exception as e:
            print(f"Error checking email: {str(e)}")
        
        item = {
            'client_id': client_id,
            'name': client_data['name'],
            'email': client_data['email'],
            'phone': client_data['phone'],
            'company_name': client_data['company_name'],
            'address': client_data.get('address', ''),
            'status': client_data.get('status', 'active'),
            'notes': client_data.get('notes', ''),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        clients_table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(item, default=str)
        }
        
    except Exception as e:
        print(f"Error creating client: {str(e)}")
        raise

def update_client(client_id, client_data):
    """Actualizar un cliente existente"""
    try:
        # Verificar que el cliente existe
        response = clients_table.get_item(Key={'client_id': client_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Client not found'})
            }
        
        timestamp = int(datetime.now().timestamp())
        
        # Construir expresión de actualización
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': timestamp}
        
        updatable_fields = ['name', 'email', 'phone', 'company_name', 'address', 'status', 'notes']
        
        for field in updatable_fields:
            if field in client_data:
                update_expression += f", {field} = :{field}"
                expression_values[f":{field}"] = client_data[field]
        
        clients_table.update_item(
            Key={'client_id': client_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )
        
        # Obtener el item actualizado
        updated_response = clients_table.get_item(Key={'client_id': client_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(updated_response['Item'], default=str)
        }
        
    except Exception as e:
        print(f"Error updating client {client_id}: {str(e)}")
        raise

def delete_client(client_id):
    """Eliminar un cliente (soft delete)"""
    try:
        # Verificar que el cliente existe
        response = clients_table.get_item(Key={'client_id': client_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Client not found'})
            }
        
        timestamp = int(datetime.now().timestamp())
        
        # Soft delete - cambiar status a 'deleted'
        clients_table.update_item(
            Key={'client_id': client_id},
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
            'body': json.dumps({'message': 'Client deleted successfully'})
        }
        
    except Exception as e:
        print(f"Error deleting client {client_id}: {str(e)}")
        raise
