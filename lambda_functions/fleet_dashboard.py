import json
import boto3
import os
from datetime import datetime, timedelta
import logging
from decimal import Decimal

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """
    API para dashboard de flota - Estadísticas y métricas en tiempo real
    """
    try:
        logger.info(f"Evento recibido: {json.dumps(event)}")
        
        # Extraer información del usuario
        user_info = extract_user_info(event)
        query_parameters = event.get('queryStringParameters') or {}
        
        # Obtener métricas del dashboard
        dashboard_data = get_fleet_dashboard_data(user_info, query_parameters)
        
        return create_response(200, dashboard_data)
        
    except Exception as e:
        logger.error(f"Error en fleet_dashboard: {str(e)}")
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

def get_fleet_dashboard_data(user_info, query_params):
    """Obtener datos completos del dashboard de flota"""
    try:
        # Período de tiempo para las métricas
        time_range = query_params.get('timeRange', '24h')  # 1h, 24h, 7d, 30d
        
        # Obtener todas las métricas
        fleet_overview = get_fleet_overview(user_info)
        vehicle_status = get_vehicle_status_summary(user_info)
        real_time_metrics = get_real_time_metrics(user_info)
        alerts_summary = get_alerts_summary(user_info, time_range)
        performance_metrics = get_performance_metrics(user_info, time_range)
        fuel_analytics = get_fuel_analytics(user_info, time_range)
        route_efficiency = get_route_efficiency(user_info, time_range)
        maintenance_alerts = get_maintenance_alerts(user_info)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'user_info': {
                'company_name': user_info['company_name'],
                'fleet_size': user_info['fleet_size']
            },
            'fleet_overview': fleet_overview,
            'vehicle_status': vehicle_status,
            'real_time_metrics': real_time_metrics,
            'alerts_summary': alerts_summary,
            'performance_metrics': performance_metrics,
            'fuel_analytics': fuel_analytics,
            'route_efficiency': route_efficiency,
            'maintenance_alerts': maintenance_alerts,
            'time_range': time_range
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos del dashboard: {str(e)}")
        raise

def get_fleet_overview(user_info):
    """Resumen general de la flota"""
    try:
        vehicles_table = dynamodb.Table(f"{os.environ['DYNAMODB_TABLE']}")
        
        # Obtener todos los vehículos del usuario
        response = vehicles_table.scan(
            FilterExpression='owner_id = :owner_id AND #status <> :deleted',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':owner_id': user_info['user_id'],
                ':deleted': 'deleted'
            }
        )
        
        vehicles = response.get('Items', [])
        total_vehicles = len(vehicles)
        
        # Contar por estado
        active_vehicles = len([v for v in vehicles if v.get('status') == 'active'])
        inactive_vehicles = len([v for v in vehicles if v.get('status') == 'inactive'])
        maintenance_vehicles = len([v for v in vehicles if v.get('status') == 'maintenance'])
        
        # Contar por tipo
        vehicle_types = {}
        for vehicle in vehicles:
            vtype = vehicle.get('vehicle_type', 'unknown')
            vehicle_types[vtype] = vehicle_types.get(vtype, 0) + 1
        
        return {
            'total_vehicles': total_vehicles,
            'active_vehicles': active_vehicles,
            'inactive_vehicles': inactive_vehicles,
            'maintenance_vehicles': maintenance_vehicles,
            'vehicle_types': vehicle_types,
            'utilization_rate': round((active_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0, 2)
        }
        
    except Exception as e:
        logger.error(f"Error en fleet_overview: {str(e)}")
        return {}

def get_vehicle_status_summary(user_info):
    """Resumen del estado de vehículos en tiempo real"""
    try:
        status_table = dynamodb.Table(f"{os.environ['DYNAMODB_TABLE'].replace('vehicles', 'vehicle-status')}")
        
        # Obtener estados recientes (últimos 5 minutos)
        five_minutes_ago = int((datetime.utcnow() - timedelta(minutes=5)).timestamp())
        
        response = status_table.scan(
            FilterExpression='#timestamp > :timestamp',
            ExpressionAttributeNames={'#timestamp': 'timestamp'},
            ExpressionAttributeValues={':timestamp': five_minutes_ago}
        )
        
        recent_statuses = response.get('Items', [])
        
        # Agrupar por vehículo y obtener el más reciente
        vehicle_latest_status = {}
        for status in recent_statuses:
            vehicle_id = status['vehicle_id']
            timestamp = status['timestamp']
            
            if vehicle_id not in vehicle_latest_status or timestamp > vehicle_latest_status[vehicle_id]['timestamp']:
                vehicle_latest_status[vehicle_id] = status
        
        # Calcular métricas
        online_vehicles = len(vehicle_latest_status)
        moving_vehicles = len([s for s in vehicle_latest_status.values() if s.get('speed', 0) > 5])
        idle_vehicles = len([s for s in vehicle_latest_status.values() if s.get('speed', 0) <= 5])
        
        # Alertas activas
        speed_alerts = len([s for s in vehicle_latest_status.values() if s.get('speed', 0) > 120])
        fuel_alerts = len([s for s in vehicle_latest_status.values() if s.get('fuel_level', 100) < 15])
        temp_alerts = len([s for s in vehicle_latest_status.values() if s.get('engine_temp', 70) > 100])
        
        return {
            'online_vehicles': online_vehicles,
            'moving_vehicles': moving_vehicles,
            'idle_vehicles': idle_vehicles,
            'offline_vehicles': max(0, int(user_info.get('fleet_size', 0)) - online_vehicles),
            'active_alerts': {
                'speed_violations': speed_alerts,
                'low_fuel': fuel_alerts,
                'high_temperature': temp_alerts,
                'total': speed_alerts + fuel_alerts + temp_alerts
            }
        }
        
    except Exception as e:
        logger.error(f"Error en vehicle_status_summary: {str(e)}")
        return {}

def get_real_time_metrics(user_info):
    """Métricas en tiempo real de la flota"""
    try:
        status_table = dynamodb.Table(f"{os.environ['DYNAMODB_TABLE'].replace('vehicles', 'vehicle-status')}")
        
        # Obtener datos de la última hora
        one_hour_ago = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        
        response = status_table.scan(
            FilterExpression='#timestamp > :timestamp',
            ExpressionAttributeNames={'#timestamp': 'timestamp'},
            ExpressionAttributeValues={':timestamp': one_hour_ago}
        )
        
        statuses = response.get('Items', [])
        
        if not statuses:
            return {}
        
        # Calcular promedios
        speeds = [float(s.get('speed', 0)) for s in statuses if s.get('speed') is not None]
        fuel_levels = [float(s.get('fuel_level', 0)) for s in statuses if s.get('fuel_level') is not None]
        engine_temps = [float(s.get('engine_temp', 0)) for s in statuses if s.get('engine_temp') is not None]
        
        return {
            'average_speed': round(sum(speeds) / len(speeds) if speeds else 0, 2),
            'max_speed': max(speeds) if speeds else 0,
            'average_fuel_level': round(sum(fuel_levels) / len(fuel_levels) if fuel_levels else 0, 2),
            'min_fuel_level': min(fuel_levels) if fuel_levels else 0,
            'average_engine_temp': round(sum(engine_temps) / len(engine_temps) if engine_temps else 0, 2),
            'max_engine_temp': max(engine_temps) if engine_temps else 0,
            'total_distance_today': calculate_total_distance(statuses),
            'active_routes': count_active_routes(statuses)
        }
        
    except Exception as e:
        logger.error(f"Error en real_time_metrics: {str(e)}")
        return {}

def get_alerts_summary(user_info, time_range):
    """Resumen de alertas por período"""
    try:
        # Calcular timestamp de inicio según el rango
        if time_range == '1h':
            start_time = datetime.utcnow() - timedelta(hours=1)
        elif time_range == '24h':
            start_time = datetime.utcnow() - timedelta(days=1)
        elif time_range == '7d':
            start_time = datetime.utcnow() - timedelta(days=7)
        elif time_range == '30d':
            start_time = datetime.utcnow() - timedelta(days=30)
        else:
            start_time = datetime.utcnow() - timedelta(days=1)
        
        # Consultar tabla de eventos de pánico y alertas
        panic_table = dynamodb.Table(f"{os.environ['DYNAMODB_TABLE'].replace('vehicles', 'panic-events')}")
        
        start_timestamp = int(start_time.timestamp())
        
        response = panic_table.scan(
            FilterExpression='#timestamp > :start_time',
            ExpressionAttributeNames={'#timestamp': 'timestamp'},
            ExpressionAttributeValues={':start_time': start_timestamp}
        )
        
        panic_events = response.get('Items', [])
        
        # Categorizar alertas
        critical_alerts = len([e for e in panic_events if e.get('alert_data', {}).get('priority') == 'CRITICAL'])
        warning_alerts = len([e for e in panic_events if e.get('alert_data', {}).get('priority') == 'WARNING'])
        info_alerts = len([e for e in panic_events if e.get('alert_data', {}).get('priority') == 'INFO'])
        
        return {
            'total_alerts': len(panic_events),
            'critical_alerts': critical_alerts,
            'warning_alerts': warning_alerts,
            'info_alerts': info_alerts,
            'resolved_alerts': len([e for e in panic_events if e.get('status') == 'RESOLVED']),
            'pending_alerts': len([e for e in panic_events if e.get('status') == 'NOTIFIED']),
            'alert_trend': calculate_alert_trend(panic_events, time_range)
        }
        
    except Exception as e:
        logger.error(f"Error en alerts_summary: {str(e)}")
        return {}

def get_performance_metrics(user_info, time_range):
    """Métricas de rendimiento de la flota"""
    try:
        # Simular métricas de rendimiento
        # En producción, estos datos vendrían de análisis de telemetría histórica
        
        return {
            'fuel_efficiency': {
                'average_mpg': 8.5,
                'best_performer': 'VH20240724001',
                'worst_performer': 'VH20240724005',
                'trend': '+2.3%'
            },
            'driver_performance': {
                'safe_driving_score': 87.5,
                'harsh_braking_events': 12,
                'speeding_violations': 8,
                'idle_time_percentage': 15.2
            },
            'route_optimization': {
                'on_time_deliveries': 92.3,
                'average_delay_minutes': 8.5,
                'route_deviation_percentage': 5.1
            },
            'maintenance_efficiency': {
                'scheduled_maintenance_compliance': 95.0,
                'unplanned_maintenance_events': 3,
                'vehicle_uptime_percentage': 97.8
            }
        }
        
    except Exception as e:
        logger.error(f"Error en performance_metrics: {str(e)}")
        return {}

def get_fuel_analytics(user_info, time_range):
    """Análisis de consumo de combustible"""
    try:
        return {
            'total_fuel_consumed_liters': 2450.5,
            'average_fuel_efficiency': 8.2,
            'fuel_cost_estimate': 3675.75,
            'top_consumers': [
                {'vehicle_id': 'VH20240724001', 'consumption': 245.5},
                {'vehicle_id': 'VH20240724002', 'consumption': 198.3},
                {'vehicle_id': 'VH20240724003', 'consumption': 187.9}
            ],
            'fuel_savings_opportunities': {
                'idle_reduction': 125.5,
                'route_optimization': 89.2,
                'driver_training': 67.8
            }
        }
        
    except Exception as e:
        logger.error(f"Error en fuel_analytics: {str(e)}")
        return {}

def get_route_efficiency(user_info, time_range):
    """Análisis de eficiencia de rutas"""
    try:
        return {
            'total_routes_completed': 156,
            'average_route_time_minutes': 125.5,
            'on_time_percentage': 92.3,
            'route_deviations': 8,
            'traffic_delay_minutes': 245,
            'most_efficient_routes': [
                {'route_id': 'RT001', 'efficiency_score': 95.2},
                {'route_id': 'RT003', 'efficiency_score': 91.8},
                {'route_id': 'RT007', 'efficiency_score': 89.5}
            ],
            'optimization_suggestions': [
                'Ruta RT005: Considerar horario alternativo para evitar tráfico',
                'Ruta RT012: Revisar puntos de parada innecesarios',
                'Ruta RT018: Evaluar ruta alternativa más corta'
            ]
        }
        
    except Exception as e:
        logger.error(f"Error en route_efficiency: {str(e)}")
        return {}

def get_maintenance_alerts(user_info):
    """Alertas de mantenimiento"""
    try:
        return {
            'vehicles_due_maintenance': [
                {
                    'vehicle_id': 'VH20240724001',
                    'maintenance_type': 'Cambio de aceite',
                    'due_date': '2024-08-15',
                    'priority': 'HIGH'
                },
                {
                    'vehicle_id': 'VH20240724003',
                    'maintenance_type': 'Revisión de frenos',
                    'due_date': '2024-08-20',
                    'priority': 'MEDIUM'
                }
            ],
            'overdue_maintenance': [
                {
                    'vehicle_id': 'VH20240724007',
                    'maintenance_type': 'Inspección técnica',
                    'overdue_days': 5,
                    'priority': 'CRITICAL'
                }
            ],
            'maintenance_costs_month': 15750.00,
            'scheduled_maintenance_next_week': 3
        }
        
    except Exception as e:
        logger.error(f"Error en maintenance_alerts: {str(e)}")
        return {}

def calculate_total_distance(statuses):
    """Calcular distancia total recorrida"""
    # Implementación simplificada
    # En producción, calcularía basándose en coordenadas GPS
    return round(len(statuses) * 0.5, 2)  # Estimación

def count_active_routes(statuses):
    """Contar rutas activas"""
    routes = set()
    for status in statuses:
        if status.get('speed', 0) > 5:  # Vehículo en movimiento
            routes.add(status.get('route_id', 'unknown'))
    return len(routes)

def calculate_alert_trend(events, time_range):
    """Calcular tendencia de alertas"""
    if not events:
        return "0%"
    
    # Implementación simplificada
    return "+15%" if len(events) > 10 else "-5%"

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
        'body': json.dumps(convert_decimals(body), ensure_ascii=False)
    }
