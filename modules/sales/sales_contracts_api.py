import json
import boto3
import uuid
from datetime import datetime
import os

dynamodb = boto3.resource('dynamodb')
contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
clients_table = dynamodb.Table(os.environ['CLIENTS_TABLE'])
inventory_table = dynamodb.Table(os.environ['INVENTORY_TABLE'])

def handler(event, context):
    """
    API Lambda para gestión de contratos de venta
    Maneja operaciones CRUD para contratos
    """
    
    try:
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        if http_method == 'GET':
            if 'contractId' in path_parameters:
                return get_contract_by_id(path_parameters['contractId'])
            else:
                return get_all_contracts(query_parameters)
                
        elif http_method == 'POST':
            body = json.loads(event['body'])
            return create_contract(body)
            
        elif http_method == 'PUT':
            contract_id = path_parameters['contractId']
            body = json.loads(event['body'])
            return update_contract(contract_id, body)
            
        elif http_method == 'DELETE':
            contract_id = path_parameters['contractId']
            return delete_contract(contract_id)
            
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

def get_all_contracts(query_params):
    """Obtener todos los contratos con filtros opcionales"""
    try:
        # Parámetros de paginación
        limit = int(query_params.get('limit', 50))
        last_key = query_params.get('lastKey')
        
        # Filtros
        client_id = query_params.get('client_id')
        status = query_params.get('status')
        
        scan_kwargs = {
            'Limit': limit
        }
        
        if last_key:
            scan_kwargs['ExclusiveStartKey'] = {'contract_id': last_key}
            
        # Aplicar filtros
        filter_expressions = []
        expression_values = {}
        
        if client_id:
            filter_expressions.append('client_id = :client_id')
            expression_values[':client_id'] = client_id
            
        if status:
            filter_expressions.append('#status = :status')
            expression_values[':status'] = status
            scan_kwargs['ExpressionAttributeNames'] = {'#status': 'status'}
            
        if filter_expressions:
            scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_kwargs['ExpressionAttributeValues'] = expression_values
            
        response = contracts_table.scan(**scan_kwargs)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'contracts': response['Items'],
                'lastKey': response.get('LastEvaluatedKey', {}).get('contract_id'),
                'count': response['Count']
            }, default=str)
        }
        
    except Exception as e:
        print(f"Error getting contracts: {str(e)}")
        raise

def get_contract_by_id(contract_id):
    """Obtener un contrato específico por ID"""
    try:
        response = contracts_table.get_item(Key={'contract_id': contract_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Contract not found'})
            }
            
        contract = response['Item']
        
        # Enriquecer con información del cliente
        try:
            client_response = clients_table.get_item(Key={'client_id': contract['client_id']})
            if 'Item' in client_response:
                contract['client_info'] = client_response['Item']
        except Exception as e:
            print(f"Error getting client info: {str(e)}")
            
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(contract, default=str)
        }
        
    except Exception as e:
        print(f"Error getting contract {contract_id}: {str(e)}")
        raise

def create_contract(contract_data):
    """Crear un nuevo contrato"""
    try:
        contract_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp())
        
        # Validar campos requeridos
        required_fields = ['client_id', 'items', 'payment_terms']
        for field in required_fields:
            if field not in contract_data:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Missing required field: {field}'})
                }
        
        # Verificar que el cliente existe
        client_response = clients_table.get_item(Key={'client_id': contract_data['client_id']})
        if 'Item' not in client_response:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Client not found'})
            }
        
        # Calcular totales
        total_amount = 0
        validated_items = []
        
        for item in contract_data['items']:
            # Verificar inventario
            inventory_response = inventory_table.get_item(Key={'inventory_id': item['inventory_id']})
            if 'Item' not in inventory_response:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Inventory item {item["inventory_id"]} not found'})
                }
            
            inventory_item = inventory_response['Item']
            quantity = int(item['quantity'])
            unit_price = float(inventory_item['price'])
            item_total = quantity * unit_price
            
            validated_items.append({
                'inventory_id': item['inventory_id'],
                'vehicle_type': inventory_item['vehicle_type'],
                'model': inventory_item['model'],
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': item_total,
                'specifications': item.get('specifications', {})
            })
            
            total_amount += item_total
        
        # Aplicar descuentos si existen
        discount_percentage = float(contract_data.get('discount_percentage', 0))
        discount_amount = total_amount * (discount_percentage / 100)
        final_amount = total_amount - discount_amount
        
        contract = {
            'contract_id': contract_id,
            'client_id': contract_data['client_id'],
            'items': validated_items,
            'subtotal': total_amount,
            'discount_percentage': discount_percentage,
            'discount_amount': discount_amount,
            'total_amount': final_amount,
            'payment_terms': contract_data['payment_terms'],
            'delivery_terms': contract_data.get('delivery_terms', {}),
            'status': 'draft',
            'notes': contract_data.get('notes', ''),
            'created_at': timestamp,
            'updated_at': timestamp,
            'expires_at': timestamp + (30 * 24 * 60 * 60)  # 30 días
        }
        
        contracts_table.put_item(Item=contract)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(contract, default=str)
        }
        
    except Exception as e:
        print(f"Error creating contract: {str(e)}")
        raise

def update_contract(contract_id, contract_data):
    """Actualizar un contrato existente"""
    try:
        # Verificar que el contrato existe
        response = contracts_table.get_item(Key={'contract_id': contract_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Contract not found'})
            }
        
        current_contract = response['Item']
        
        # No permitir actualizar contratos firmados o cancelados
        if current_contract.get('status') in ['signed', 'cancelled']:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Cannot update signed or cancelled contract'})
            }
        
        timestamp = int(datetime.now().timestamp())
        
        # Construir expresión de actualización
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': timestamp}
        
        updatable_fields = [
            'payment_terms', 'delivery_terms', 'status', 'notes', 
            'discount_percentage', 'signed_at', 'signed_by'
        ]
        
        for field in updatable_fields:
            if field in contract_data:
                update_expression += f", {field} = :{field}"
                expression_values[f":{field}"] = contract_data[field]
        
        # Si se actualiza el estado a 'signed', agregar timestamp
        if contract_data.get('status') == 'signed' and 'signed_at' not in contract_data:
            update_expression += ", signed_at = :signed_at"
            expression_values[':signed_at'] = timestamp
        
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues='ALL_NEW'
        )
        
        # Obtener el contrato actualizado
        updated_response = contracts_table.get_item(Key={'contract_id': contract_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(updated_response['Item'], default=str)
        }
        
    except Exception as e:
        print(f"Error updating contract {contract_id}: {str(e)}")
        raise

def delete_contract(contract_id):
    """Cancelar un contrato"""
    try:
        # Verificar que el contrato existe
        response = contracts_table.get_item(Key={'contract_id': contract_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Contract not found'})
            }
        
        current_contract = response['Item']
        
        # No permitir cancelar contratos ya firmados
        if current_contract.get('status') == 'signed':
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Cannot cancel signed contract'})
            }
        
        timestamp = int(datetime.now().timestamp())
        
        # Cambiar status a 'cancelled'
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at, cancelled_at = :cancelled_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'cancelled',
                ':updated_at': timestamp,
                ':cancelled_at': timestamp
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Contract cancelled successfully'})
        }
        
    except Exception as e:
        print(f"Error cancelling contract {contract_id}: {str(e)}")
        raise
