import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import os

dynamodb = boto3.resource('dynamodb')
contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
clients_table = dynamodb.Table(os.environ['CLIENTS_TABLE'])
inventory_table = dynamodb.Table(os.environ['INVENTORY_TABLE'])
quotations_table = dynamodb.Table(os.environ['QUOTATIONS_TABLE'])

def handler(event, context):
    """
    API Lambda para dashboard de ventas
    Proporciona métricas y estadísticas de ventas
    """
    
    try:
        query_parameters = event.get('queryStringParameters') or {}
        
        # Parámetros de tiempo
        period = query_parameters.get('period', '30')  # días
        start_date = query_parameters.get('start_date')
        end_date = query_parameters.get('end_date')
        
        # Calcular rango de fechas
        if start_date and end_date:
            start_timestamp = int(datetime.fromisoformat(start_date).timestamp())
            end_timestamp = int(datetime.fromisoformat(end_date).timestamp())
        else:
            end_timestamp = int(datetime.now().timestamp())
            start_timestamp = end_timestamp - (int(period) * 24 * 60 * 60)
        
        # Obtener métricas
        dashboard_data = {
            'period': {
                'start_date': datetime.fromtimestamp(start_timestamp).isoformat(),
                'end_date': datetime.fromtimestamp(end_timestamp).isoformat(),
                'days': int((end_timestamp - start_timestamp) / (24 * 60 * 60))
            },
            'sales_metrics': get_sales_metrics(start_timestamp, end_timestamp),
            'client_metrics': get_client_metrics(start_timestamp, end_timestamp),
            'inventory_metrics': get_inventory_metrics(),
            'contract_status': get_contract_status_metrics(start_timestamp, end_timestamp),
            'top_performers': get_top_performers(start_timestamp, end_timestamp),
            'recent_activity': get_recent_activity(limit=10)
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(dashboard_data, default=decimal_default)
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

def get_sales_metrics(start_timestamp, end_timestamp):
    """Obtener métricas de ventas"""
    try:
        # Escanear contratos en el período
        response = contracts_table.scan(
            FilterExpression='created_at BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':start': start_timestamp,
                ':end': end_timestamp
            }
        )
        
        contracts = response['Items']
        
        # Calcular métricas
        total_contracts = len(contracts)
        total_revenue = sum(float(contract.get('total_amount', 0)) for contract in contracts)
        signed_contracts = [c for c in contracts if c.get('status') == 'signed']
        signed_revenue = sum(float(contract.get('total_amount', 0)) for contract in signed_contracts)
        
        # Calcular promedio por contrato
        avg_contract_value = total_revenue / total_contracts if total_contracts > 0 else 0
        
        # Tasa de conversión
        conversion_rate = (len(signed_contracts) / total_contracts * 100) if total_contracts > 0 else 0
        
        return {
            'total_contracts': total_contracts,
            'signed_contracts': len(signed_contracts),
            'total_revenue': total_revenue,
            'signed_revenue': signed_revenue,
            'avg_contract_value': avg_contract_value,
            'conversion_rate': conversion_rate
        }
        
    except Exception as e:
        print(f"Error getting sales metrics: {str(e)}")
        return {
            'total_contracts': 0,
            'signed_contracts': 0,
            'total_revenue': 0,
            'signed_revenue': 0,
            'avg_contract_value': 0,
            'conversion_rate': 0
        }

def get_client_metrics(start_timestamp, end_timestamp):
    """Obtener métricas de clientes"""
    try:
        # Escanear clientes creados en el período
        response = clients_table.scan(
            FilterExpression='created_at BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':start': start_timestamp,
                ':end': end_timestamp
            }
        )
        
        new_clients = response['Items']
        
        # Total de clientes activos
        total_response = clients_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'active'}
        )
        
        total_active_clients = len(total_response['Items'])
        
        # Clientes por empresa (top 5)
        company_counts = {}
        for client in total_response['Items']:
            company = client.get('company_name', 'Unknown')
            company_counts[company] = company_counts.get(company, 0) + 1
        
        top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'new_clients': len(new_clients),
            'total_active_clients': total_active_clients,
            'top_companies': [{'company': company, 'count': count} for company, count in top_companies]
        }
        
    except Exception as e:
        print(f"Error getting client metrics: {str(e)}")
        return {
            'new_clients': 0,
            'total_active_clients': 0,
            'top_companies': []
        }

def get_inventory_metrics():
    """Obtener métricas de inventario"""
    try:
        response = inventory_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'available'}
        )
        
        inventory_items = response['Items']
        
        # Métricas básicas
        total_items = len(inventory_items)
        total_quantity = sum(int(item.get('available_quantity', 0)) for item in inventory_items)
        total_value = sum(float(item.get('price', 0)) * int(item.get('available_quantity', 0)) for item in inventory_items)
        
        # Por tipo de vehículo
        vehicle_type_counts = {}
        vehicle_type_values = {}
        
        for item in inventory_items:
            vehicle_type = item.get('vehicle_type', 'Unknown')
            quantity = int(item.get('available_quantity', 0))
            value = float(item.get('price', 0)) * quantity
            
            vehicle_type_counts[vehicle_type] = vehicle_type_counts.get(vehicle_type, 0) + quantity
            vehicle_type_values[vehicle_type] = vehicle_type_values.get(vehicle_type, 0) + value
        
        # Items con bajo stock (menos de 5 unidades)
        low_stock_items = [
            {
                'inventory_id': item['inventory_id'],
                'vehicle_type': item.get('vehicle_type'),
                'model': item.get('model'),
                'available_quantity': item.get('available_quantity')
            }
            for item in inventory_items 
            if int(item.get('available_quantity', 0)) < 5
        ]
        
        return {
            'total_items': total_items,
            'total_quantity': total_quantity,
            'total_value': total_value,
            'by_vehicle_type': [
                {
                    'vehicle_type': vtype,
                    'quantity': vehicle_type_counts[vtype],
                    'value': vehicle_type_values[vtype]
                }
                for vtype in vehicle_type_counts.keys()
            ],
            'low_stock_items': low_stock_items[:10]  # Top 10
        }
        
    except Exception as e:
        print(f"Error getting inventory metrics: {str(e)}")
        return {
            'total_items': 0,
            'total_quantity': 0,
            'total_value': 0,
            'by_vehicle_type': [],
            'low_stock_items': []
        }

def get_contract_status_metrics(start_timestamp, end_timestamp):
    """Obtener métricas por estado de contrato"""
    try:
        response = contracts_table.scan(
            FilterExpression='created_at BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':start': start_timestamp,
                ':end': end_timestamp
            }
        )
        
        contracts = response['Items']
        
        # Contar por estado
        status_counts = {}
        status_values = {}
        
        for contract in contracts:
            status = contract.get('status', 'unknown')
            value = float(contract.get('total_amount', 0))
            
            status_counts[status] = status_counts.get(status, 0) + 1
            status_values[status] = status_values.get(status, 0) + value
        
        return [
            {
                'status': status,
                'count': status_counts[status],
                'total_value': status_values[status]
            }
            for status in status_counts.keys()
        ]
        
    except Exception as e:
        print(f"Error getting contract status metrics: {str(e)}")
        return []

def get_top_performers(start_timestamp, end_timestamp):
    """Obtener top performers (por ahora simulado)"""
    try:
        # En una implementación real, esto vendría de una tabla de usuarios/vendedores
        # Por ahora retornamos datos simulados
        return [
            {'name': 'Juan Pérez', 'contracts': 15, 'revenue': 450000},
            {'name': 'María García', 'contracts': 12, 'revenue': 380000},
            {'name': 'Carlos López', 'contracts': 10, 'revenue': 320000},
            {'name': 'Ana Martínez', 'contracts': 8, 'revenue': 280000},
            {'name': 'Luis Rodríguez', 'contracts': 6, 'revenue': 210000}
        ]
        
    except Exception as e:
        print(f"Error getting top performers: {str(e)}")
        return []

def get_recent_activity(limit=10):
    """Obtener actividad reciente"""
    try:
        # Obtener contratos recientes
        contracts_response = contracts_table.scan(
            Limit=limit,
            ScanIndexForward=False
        )
        
        # Obtener clientes recientes
        clients_response = clients_table.scan(
            Limit=limit,
            ScanIndexForward=False
        )
        
        activities = []
        
        # Agregar contratos recientes
        for contract in contracts_response['Items']:
            activities.append({
                'type': 'contract',
                'action': f"Contrato {contract.get('status', 'creado')}",
                'description': f"Contrato {contract['contract_id'][:8]}... por ${contract.get('total_amount', 0)}",
                'timestamp': contract.get('updated_at', contract.get('created_at')),
                'id': contract['contract_id']
            })
        
        # Agregar clientes recientes
        for client in clients_response['Items']:
            activities.append({
                'type': 'client',
                'action': 'Cliente registrado',
                'description': f"Nuevo cliente: {client.get('name', 'Unknown')} - {client.get('company_name', '')}",
                'timestamp': client.get('created_at'),
                'id': client['client_id']
            })
        
        # Ordenar por timestamp y limitar
        activities.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return activities[:limit]
        
    except Exception as e:
        print(f"Error getting recent activity: {str(e)}")
        return []

def decimal_default(obj):
    """JSON serializer para objetos Decimal"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError
