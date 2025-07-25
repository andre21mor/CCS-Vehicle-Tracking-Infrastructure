#!/usr/bin/env python3
"""
Calculadora de costos para la plataforma de seguimiento vehicular
"""

import argparse
import json
from datetime import datetime

class VehicleTrackingCostCalculator:
    def __init__(self):
        # Precios de AWS (USD) - actualizados a 2024
        self.pricing = {
            'iot_core': {
                'connectivity': 0.08,  # por dispositivo/mes
                'messaging': 1.00,     # por 1M mensajes
                'device_shadow': 1.25, # por 1M operaciones
                'rules_engine': 0.15   # por 1M mensajes
            },
            'kinesis': {
                'shard_hour': 0.015,   # por shard/hora
                'put_payload': 0.014,  # por 1M records
                'extended_retention': 0.02  # por shard/hora
            },
            'lambda': {
                'requests': 0.20,      # por 1M requests
                'duration_gb_second': 0.0000166667  # por GB-segundo
            },
            'dynamodb': {
                'read_request': 0.25,  # por 1M RRU
                'write_request': 1.25, # por 1M WRU
                'storage': 0.25        # por GB/mes
            },
            's3': {
                'standard': 0.023,     # por GB/mes
                'intelligent_tiering': 0.0125,  # por GB/mes
                'put_requests': 0.0005, # por 1K requests
                'get_requests': 0.0004, # por 1K requests
                'data_transfer': 0.09   # por GB
            },
            'api_gateway': {
                'rest_calls': 3.50     # por 1M calls
            },
            'cognito': {
                'mau': 0.0055,         # por MAU
                'advanced_security': 0.05  # por MAU
            },
            'step_functions': {
                'state_transitions': 0.025  # por 1K transiciones
            },
            'sns': {
                'notifications': 0.50, # por 1M notificaciones
                'sms': 0.75           # por SMS
            },
            'elasticache': {
                't3_micro': 0.017     # por hora
            },
            'cloudwatch': {
                'logs_ingestion': 0.50, # por GB
                'logs_storage': 0.03,   # por GB/mes
                'custom_metrics': 0.30, # por métrica/mes
                'dashboards': 3.00      # por dashboard/mes
            },
            'data_transfer': {
                'inter_az': 0.01,      # por GB
                'internet': 0.09       # por GB
            }
        }
    
    def calculate_iot_core_cost(self, vehicles, messages_per_vehicle_per_hour=12):
        """Calcular costo de AWS IoT Core"""
        # Conectividad
        connectivity_cost = vehicles * self.pricing['iot_core']['connectivity']
        
        # Mensajería (30 días × 24 horas)
        total_messages = vehicles * messages_per_vehicle_per_hour * 24 * 30
        messaging_cost = (total_messages / 1_000_000) * self.pricing['iot_core']['messaging']
        
        # Device Shadow (estimado 100 operaciones/día por vehículo)
        shadow_operations = vehicles * 100 * 30
        shadow_cost = (shadow_operations / 1_000_000) * self.pricing['iot_core']['device_shadow']
        
        # Rules Engine
        rules_cost = (total_messages / 1_000_000) * self.pricing['iot_core']['rules_engine']
        
        return {
            'connectivity': connectivity_cost,
            'messaging': messaging_cost,
            'device_shadow': shadow_cost,
            'rules_engine': rules_cost,
            'total': connectivity_cost + messaging_cost + shadow_cost + rules_cost
        }
    
    def calculate_kinesis_cost(self, vehicles, signals_per_second_peak=None):
        """Calcular costo de Kinesis Data Streams"""
        if signals_per_second_peak is None:
            signals_per_second_peak = vehicles  # Asumimos 1 señal/segundo/vehículo en pico
        
        # Número de shards necesarios (1000 records/segundo por shard)
        shards_needed = max(1, (signals_per_second_peak // 1000) + 1)
        
        # Shard hours
        shard_hours_cost = shards_needed * 24 * 30 * self.pricing['kinesis']['shard_hour']
        
        # PUT payload units (estimado 43.2M records/mes para 5K vehículos)
        records_per_month = vehicles * 12 * 24 * 30  # 12 records/hora promedio
        put_cost = (records_per_month / 1_000_000) * self.pricing['kinesis']['put_payload']
        
        # Extended retention
        retention_cost = shards_needed * 24 * self.pricing['kinesis']['extended_retention']
        
        return {
            'shards_needed': shards_needed,
            'shard_hours': shard_hours_cost,
            'put_payload': put_cost,
            'extended_retention': retention_cost,
            'total': shard_hours_cost + put_cost + retention_cost
        }
    
    def calculate_lambda_cost(self, vehicles):
        """Calcular costo de Lambda Functions"""
        # Estimaciones basadas en uso típico
        invocations_per_month = vehicles * 1000  # 1000 invocaciones/vehículo/mes
        avg_duration_seconds = 2
        avg_memory_mb = 512
        
        # Requests cost
        requests_cost = (invocations_per_month / 1_000_000) * self.pricing['lambda']['requests']
        
        # Duration cost
        gb_seconds = invocations_per_month * avg_duration_seconds * (avg_memory_mb / 1024)
        duration_cost = gb_seconds * self.pricing['lambda']['duration_gb_second']
        
        return {
            'invocations': invocations_per_month,
            'requests_cost': requests_cost,
            'duration_cost': duration_cost,
            'total': requests_cost + duration_cost
        }
    
    def calculate_dynamodb_cost(self, vehicles):
        """Calcular costo de DynamoDB"""
        # Estimaciones de uso
        reads_per_month = vehicles * 20_000  # 20K lecturas/vehículo/mes
        writes_per_month = vehicles * 10_000  # 10K escrituras/vehículo/mes
        storage_gb = vehicles * 0.1  # 100MB por vehículo
        
        read_cost = (reads_per_month / 1_000_000) * self.pricing['dynamodb']['read_request']
        write_cost = (writes_per_month / 1_000_000) * self.pricing['dynamodb']['write_request']
        storage_cost = storage_gb * self.pricing['dynamodb']['storage']
        
        return {
            'reads': reads_per_month,
            'writes': writes_per_month,
            'storage_gb': storage_gb,
            'read_cost': read_cost,
            'write_cost': write_cost,
            'storage_cost': storage_cost,
            'total': read_cost + write_cost + storage_cost
        }
    
    def calculate_s3_cost(self, vehicles):
        """Calcular costo de S3"""
        # Estimaciones de almacenamiento de video
        video_gb_per_vehicle_per_month = 2  # 2GB de video por vehículo/mes
        documents_gb = 0.1  # 100MB de documentos total
        
        total_video_gb = vehicles * video_gb_per_vehicle_per_month
        
        # 10% en Standard, 90% en Intelligent Tiering
        standard_gb = total_video_gb * 0.1
        intelligent_gb = total_video_gb * 0.9
        
        standard_cost = standard_gb * self.pricing['s3']['standard']
        intelligent_cost = intelligent_gb * self.pricing['s3']['intelligent_tiering']
        documents_cost = documents_gb * self.pricing['s3']['standard']
        
        # Requests (estimado)
        put_requests = vehicles * 1000  # 1K PUT requests/vehículo/mes
        get_requests = vehicles * 10000  # 10K GET requests/vehículo/mes
        
        put_cost = (put_requests / 1000) * self.pricing['s3']['put_requests']
        get_cost = (get_requests / 1000) * self.pricing['s3']['get_requests']
        
        # Data transfer (estimado 40% del almacenamiento)
        transfer_gb = total_video_gb * 0.4
        transfer_cost = transfer_gb * self.pricing['s3']['data_transfer']
        
        return {
            'storage_gb': total_video_gb + documents_gb,
            'standard_cost': standard_cost,
            'intelligent_cost': intelligent_cost,
            'documents_cost': documents_cost,
            'requests_cost': put_cost + get_cost,
            'transfer_cost': transfer_cost,
            'total': standard_cost + intelligent_cost + documents_cost + put_cost + get_cost + transfer_cost
        }
    
    def calculate_other_services_cost(self, vehicles):
        """Calcular costo de otros servicios"""
        # API Gateway
        api_calls = vehicles * 2000  # 2K calls/vehículo/mes
        api_cost = (api_calls / 1_000_000) * self.pricing['api_gateway']['rest_calls']
        
        # Cognito (estimado 20% de vehículos = usuarios activos)
        active_users = max(100, vehicles * 0.2)
        cognito_cost = active_users * self.pricing['cognito']['mau']
        
        # Step Functions (solo para contratos)
        step_functions_cost = 10 * self.pricing['step_functions']['state_transitions'] / 1000  # 10K transiciones/mes
        
        # SNS
        notifications = vehicles * 200  # 200 notificaciones/vehículo/mes
        sns_cost = (notifications / 1_000_000) * self.pricing['sns']['notifications']
        
        # ElastiCache (2 nodos)
        elasticache_cost = 2 * self.pricing['elasticache']['t3_micro'] * 24 * 30
        
        # CloudWatch
        logs_gb = vehicles * 0.02  # 20MB logs/vehículo/mes
        metrics_count = min(1000, vehicles * 0.2)  # Máximo 1K métricas
        
        cloudwatch_cost = (
            logs_gb * self.pricing['cloudwatch']['logs_ingestion'] +
            logs_gb * self.pricing['cloudwatch']['logs_storage'] +
            metrics_count * self.pricing['cloudwatch']['custom_metrics'] +
            5 * self.pricing['cloudwatch']['dashboards']  # 5 dashboards
        )
        
        # Data Transfer
        inter_az_gb = vehicles * 0.2  # 200MB inter-AZ/vehículo/mes
        internet_gb = vehicles * 0.1   # 100MB internet/vehículo/mes
        
        transfer_cost = (
            inter_az_gb * self.pricing['data_transfer']['inter_az'] +
            internet_gb * self.pricing['data_transfer']['internet']
        )
        
        return {
            'api_gateway': api_cost,
            'cognito': cognito_cost,
            'step_functions': step_functions_cost,
            'sns': sns_cost,
            'elasticache': elasticache_cost,
            'cloudwatch': cloudwatch_cost,
            'data_transfer': transfer_cost,
            'total': api_cost + cognito_cost + step_functions_cost + sns_cost + elasticache_cost + cloudwatch_cost + transfer_cost
        }
    
    def calculate_total_cost(self, vehicles, include_optimizations=False):
        """Calcular costo total"""
        iot_cost = self.calculate_iot_core_cost(vehicles)
        kinesis_cost = self.calculate_kinesis_cost(vehicles)
        lambda_cost = self.calculate_lambda_cost(vehicles)
        dynamodb_cost = self.calculate_dynamodb_cost(vehicles)
        s3_cost = self.calculate_s3_cost(vehicles)
        other_cost = self.calculate_other_services_cost(vehicles)
        
        total_monthly = (
            iot_cost['total'] +
            kinesis_cost['total'] +
            lambda_cost['total'] +
            dynamodb_cost['total'] +
            s3_cost['total'] +
            other_cost['total']
        )
        
        # Aplicar optimizaciones si se solicita
        if include_optimizations:
            # Descuentos típicos con optimizaciones
            optimization_factor = 0.75  # 25% de ahorro
            total_monthly *= optimization_factor
        
        cost_per_vehicle = total_monthly / vehicles if vehicles > 0 else 0
        
        return {
            'vehicles': vehicles,
            'breakdown': {
                'iot_core': iot_cost,
                'kinesis': kinesis_cost,
                'lambda': lambda_cost,
                'dynamodb': dynamodb_cost,
                's3': s3_cost,
                'other_services': other_cost
            },
            'total_monthly': total_monthly,
            'cost_per_vehicle': cost_per_vehicle,
            'annual_cost': total_monthly * 12,
            'optimized': include_optimizations
        }
    
    def generate_cost_report(self, vehicle_counts, include_optimizations=False):
        """Generar reporte de costos para múltiples escalas"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'currency': 'USD',
            'optimizations_applied': include_optimizations,
            'scenarios': []
        }
        
        for vehicles in vehicle_counts:
            cost_analysis = self.calculate_total_cost(vehicles, include_optimizations)
            report['scenarios'].append(cost_analysis)
        
        return report
    
    def print_cost_summary(self, vehicles, include_optimizations=False):
        """Imprimir resumen de costos"""
        cost_analysis = self.calculate_total_cost(vehicles, include_optimizations)
        
        print(f"\n{'='*60}")
        print(f"ANÁLISIS DE COSTOS - {vehicles:,} VEHÍCULOS")
        if include_optimizations:
            print("(CON OPTIMIZACIONES APLICADAS)")
        print(f"{'='*60}")
        
        print(f"\n📊 RESUMEN EJECUTIVO:")
        print(f"   Costo mensual total: ${cost_analysis['total_monthly']:,.2f}")
        print(f"   Costo por vehículo:  ${cost_analysis['cost_per_vehicle']:.2f}/mes")
        print(f"   Costo anual:         ${cost_analysis['annual_cost']:,.2f}")
        
        print(f"\n💰 DESGLOSE POR SERVICIO:")
        breakdown = cost_analysis['breakdown']
        
        services = [
            ('AWS IoT Core', breakdown['iot_core']['total']),
            ('Kinesis Streams', breakdown['kinesis']['total']),
            ('Lambda Functions', breakdown['lambda']['total']),
            ('DynamoDB', breakdown['dynamodb']['total']),
            ('S3 Storage', breakdown['s3']['total']),
            ('Otros Servicios', breakdown['other_services']['total'])
        ]
        
        for service_name, cost in services:
            percentage = (cost / cost_analysis['total_monthly']) * 100
            print(f"   {service_name:<20} ${cost:>8.2f} ({percentage:>5.1f}%)")
        
        print(f"\n📈 ESCALABILIDAD:")
        if vehicles >= 1000:
            smaller_cost = self.calculate_total_cost(vehicles // 2, include_optimizations)
            larger_cost = self.calculate_total_cost(vehicles * 2, include_optimizations)
            
            print(f"   {vehicles//2:,} vehículos: ${smaller_cost['cost_per_vehicle']:.2f}/vehículo")
            print(f"   {vehicles:,} vehículos: ${cost_analysis['cost_per_vehicle']:.2f}/vehículo")
            print(f"   {vehicles*2:,} vehículos: ${larger_cost['cost_per_vehicle']:.2f}/vehículo")
        
        print(f"\n💡 COMPARACIÓN CON COMPETENCIA:")
        competitor_cost_per_vehicle = 4.0  # Promedio de competidores
        savings_per_vehicle = competitor_cost_per_vehicle - cost_analysis['cost_per_vehicle']
        total_savings = savings_per_vehicle * vehicles
        
        print(f"   Competencia promedio: ${competitor_cost_per_vehicle:.2f}/vehículo/mes")
        print(f"   Nuestra solución:     ${cost_analysis['cost_per_vehicle']:.2f}/vehículo/mes")
        print(f"   Ahorro por vehículo:  ${savings_per_vehicle:.2f}/mes")
        print(f"   Ahorro total mensual: ${total_savings:,.2f}")
        print(f"   Ahorro anual:         ${total_savings * 12:,.2f}")

def main():
    parser = argparse.ArgumentParser(description='Calculadora de costos para plataforma de seguimiento vehicular')
    parser.add_argument('--vehicles', type=int, default=5000, help='Número de vehículos')
    parser.add_argument('--optimized', action='store_true', help='Incluir optimizaciones de costo')
    parser.add_argument('--scenarios', action='store_true', help='Mostrar múltiples escenarios')
    parser.add_argument('--export-json', help='Exportar resultados a archivo JSON')
    
    args = parser.parse_args()
    
    calculator = VehicleTrackingCostCalculator()
    
    if args.scenarios:
        # Múltiples escenarios
        vehicle_counts = [500, 1000, 2500, 5000, 10000, 25000, 50000]
        
        print("🚀 ANÁLISIS DE COSTOS - MÚLTIPLES ESCENARIOS")
        print("=" * 80)
        
        for vehicles in vehicle_counts:
            calculator.print_cost_summary(vehicles, args.optimized)
        
        if args.export_json:
            report = calculator.generate_cost_report(vehicle_counts, args.optimized)
            with open(args.export_json, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Reporte exportado a: {args.export_json}")
    
    else:
        # Escenario único
        calculator.print_cost_summary(args.vehicles, args.optimized)
        
        if args.export_json:
            cost_analysis = calculator.calculate_total_cost(args.vehicles, args.optimized)
            with open(args.export_json, 'w') as f:
                json.dump(cost_analysis, f, indent=2)
            print(f"\n📄 Análisis exportado a: {args.export_json}")

if __name__ == "__main__":
    main()
