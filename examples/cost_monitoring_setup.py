#!/usr/bin/env python3
"""
Script para configurar monitoreo de costos en AWS
"""

import boto3
import json
from datetime import datetime, timedelta

class CostMonitoringSetup:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.budgets = boto3.client('budgets', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.ce = boto3.client('ce', region_name=region)  # Cost Explorer
    
    def create_cost_budget(self, project_name, environment, monthly_limit=3500):
        """Crear presupuesto de costos"""
        try:
            account_id = boto3.client('sts').get_caller_identity()['Account']
            
            # Crear topic SNS para alertas
            topic_name = f"{project_name}-{environment}-cost-alerts"
            try:
                topic_response = self.sns.create_topic(Name=topic_name)
                topic_arn = topic_response['TopicArn']
                print(f"✅ Topic SNS creado: {topic_arn}")
            except Exception as e:
                print(f"⚠️  Error creando topic SNS: {e}")
                topic_arn = f"arn:aws:sns:{self.region}:{account_id}:{topic_name}"
            
            # Configuración del presupuesto
            budget = {
                'BudgetName': f'{project_name}-{environment}-monthly-budget',
                'BudgetLimit': {
                    'Amount': str(monthly_limit),
                    'Unit': 'USD'
                },
                'TimeUnit': 'MONTHLY',
                'TimePeriod': {
                    'Start': datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                    'End': datetime(2030, 1, 1)
                },
                'BudgetType': 'COST',
                'CostFilters': {
                    'TagKey': ['Project', 'Environment'],
                    'TagValue': [project_name, environment]
                }
            }
            
            # Notificaciones
            notifications = [
                {
                    'Notification': {
                        'NotificationType': 'ACTUAL',
                        'ComparisonOperator': 'GREATER_THAN',
                        'Threshold': 80.0,
                        'ThresholdType': 'PERCENTAGE'
                    },
                    'Subscribers': [
                        {
                            'SubscriptionType': 'SNS',
                            'Address': topic_arn
                        }
                    ]
                },
                {
                    'Notification': {
                        'NotificationType': 'FORECASTED',
                        'ComparisonOperator': 'GREATER_THAN',
                        'Threshold': 100.0,
                        'ThresholdType': 'PERCENTAGE'
                    },
                    'Subscribers': [
                        {
                            'SubscriptionType': 'SNS',
                            'Address': topic_arn
                        }
                    ]
                }
            ]
            
            # Crear presupuesto
            self.budgets.create_budget(
                AccountId=account_id,
                Budget=budget,
                NotificationsWithSubscribers=notifications
            )
            
            print(f"✅ Presupuesto creado: ${monthly_limit}/mes")
            print(f"   Alertas: 80% actual, 100% proyectado")
            
            return topic_arn
            
        except Exception as e:
            print(f"❌ Error creando presupuesto: {e}")
            return None
    
    def create_cost_dashboard(self, project_name, environment):
        """Crear dashboard de costos en CloudWatch"""
        try:
            dashboard_name = f"{project_name}-{environment}-cost-dashboard"
            
            dashboard_body = {
                "widgets": [
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["AWS/Billing", "EstimatedCharges", "Currency", "USD"]
                            ],
                            "view": "timeSeries",
                            "stacked": False,
                            "region": "us-east-1",
                            "title": "Costo Total Estimado",
                            "period": 86400,
                            "stat": "Maximum"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 12,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["AWS/IoT", "PublishIn.Success"],
                                ["AWS/IoT", "PublishOut.Success"],
                                ["AWS/IoT", "Connect.Success"]
                            ],
                            "view": "timeSeries",
                            "stacked": False,
                            "region": self.region,
                            "title": "Métricas IoT Core",
                            "period": 300
                        }
                    },
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 6,
                        "width": 8,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["AWS/Kinesis", "IncomingRecords", "StreamName", f"{project_name}-{environment}-telemetry"],
                                ["AWS/Kinesis", "OutgoingRecords", "StreamName", f"{project_name}-{environment}-telemetry"]
                            ],
                            "view": "timeSeries",
                            "stacked": False,
                            "region": self.region,
                            "title": "Kinesis Throughput",
                            "period": 300
                        }
                    },
                    {
                        "type": "metric",
                        "x": 8,
                        "y": 6,
                        "width": 8,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["AWS/Lambda", "Invocations", "FunctionName", f"{project_name}-{environment}-panic-processor"],
                                ["AWS/Lambda", "Duration", "FunctionName", f"{project_name}-{environment}-panic-processor"],
                                ["AWS/Lambda", "Errors", "FunctionName", f"{project_name}-{environment}-panic-processor"]
                            ],
                            "view": "timeSeries",
                            "stacked": False,
                            "region": self.region,
                            "title": "Lambda Performance",
                            "period": 300
                        }
                    },
                    {
                        "type": "metric",
                        "x": 16,
                        "y": 6,
                        "width": 8,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", f"{project_name}-{environment}-vehicle-status"],
                                ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", f"{project_name}-{environment}-vehicle-status"]
                            ],
                            "view": "timeSeries",
                            "stacked": False,
                            "region": self.region,
                            "title": "DynamoDB Capacity",
                            "period": 300
                        }
                    }
                ]
            }
            
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            
            dashboard_url = f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard_name}"
            print(f"✅ Dashboard creado: {dashboard_name}")
            print(f"   URL: {dashboard_url}")
            
            return dashboard_url
            
        except Exception as e:
            print(f"❌ Error creando dashboard: {e}")
            return None
    
    def create_cost_alarms(self, project_name, environment, topic_arn):
        """Crear alarmas de costo por servicio"""
        try:
            alarms_created = []
            
            # Alarma para IoT Core
            alarm_name = f"{project_name}-{environment}-iot-cost-alarm"
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='EstimatedCharges',
                Namespace='AWS/Billing',
                Period=86400,
                Statistic='Maximum',
                Threshold=500.0,
                ActionsEnabled=True,
                AlarmActions=[topic_arn],
                AlarmDescription='Alarma cuando el costo de IoT Core excede $500',
                Dimensions=[
                    {
                        'Name': 'ServiceName',
                        'Value': 'AmazonIoT'
                    },
                    {
                        'Name': 'Currency',
                        'Value': 'USD'
                    }
                ]
            )
            alarms_created.append(alarm_name)
            
            # Alarma para Lambda
            alarm_name = f"{project_name}-{environment}-lambda-cost-alarm"
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='EstimatedCharges',
                Namespace='AWS/Billing',
                Period=86400,
                Statistic='Maximum',
                Threshold=1000.0,
                ActionsEnabled=True,
                AlarmActions=[topic_arn],
                AlarmDescription='Alarma cuando el costo de Lambda excede $1000',
                Dimensions=[
                    {
                        'Name': 'ServiceName',
                        'Value': 'AWSLambda'
                    },
                    {
                        'Name': 'Currency',
                        'Value': 'USD'
                    }
                ]
            )
            alarms_created.append(alarm_name)
            
            print(f"✅ Alarmas de costo creadas: {len(alarms_created)}")
            for alarm in alarms_created:
                print(f"   - {alarm}")
            
            return alarms_created
            
        except Exception as e:
            print(f"❌ Error creando alarmas: {e}")
            return []
    
    def get_current_costs(self, project_name, environment):
        """Obtener costos actuales"""
        try:
            end_date = datetime.now().date()
            start_date = end_date.replace(day=1)  # Primer día del mes
            
            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ],
                Filter={
                    'Tags': {
                        'Key': 'Project',
                        'Values': [project_name]
                    }
                }
            )
            
            print(f"\n💰 COSTOS ACTUALES ({start_date} - {end_date}):")
            
            total_cost = 0
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    if cost > 0:
                        print(f"   {service:<30} ${cost:>8.2f}")
                        total_cost += cost
            
            print(f"   {'TOTAL':<30} ${total_cost:>8.2f}")
            
            return total_cost
            
        except Exception as e:
            print(f"❌ Error obteniendo costos actuales: {e}")
            return 0
    
    def setup_complete_monitoring(self, project_name, environment, monthly_limit=3500, email=None):
        """Configurar monitoreo completo de costos"""
        print(f"🚀 Configurando monitoreo de costos para {project_name}-{environment}")
        print("=" * 60)
        
        # 1. Crear presupuesto
        print("\n📊 Creando presupuesto mensual...")
        topic_arn = self.create_cost_budget(project_name, environment, monthly_limit)
        
        # 2. Suscribir email si se proporciona
        if email and topic_arn:
            try:
                self.sns.subscribe(
                    TopicArn=topic_arn,
                    Protocol='email',
                    Endpoint=email
                )
                print(f"✅ Suscripción de email configurada: {email}")
            except Exception as e:
                print(f"⚠️  Error configurando email: {e}")
        
        # 3. Crear dashboard
        print("\n📈 Creando dashboard de costos...")
        dashboard_url = self.create_cost_dashboard(project_name, environment)
        
        # 4. Crear alarmas
        if topic_arn:
            print("\n🚨 Creando alarmas de costo...")
            alarms = self.create_cost_alarms(project_name, environment, topic_arn)
        
        # 5. Mostrar costos actuales
        print("\n💸 Obteniendo costos actuales...")
        current_cost = self.get_current_costs(project_name, environment)
        
        # 6. Resumen final
        print(f"\n{'='*60}")
        print("✅ CONFIGURACIÓN COMPLETADA")
        print(f"{'='*60}")
        print(f"   Presupuesto mensual: ${monthly_limit}")
        print(f"   Costo actual del mes: ${current_cost:.2f}")
        print(f"   Utilización: {(current_cost/monthly_limit)*100:.1f}%")
        
        if dashboard_url:
            print(f"   Dashboard: {dashboard_url}")
        
        print(f"\n📋 PRÓXIMOS PASOS:")
        print(f"   1. Confirmar suscripción de email (si configurado)")
        print(f"   2. Revisar dashboard diariamente")
        print(f"   3. Ajustar presupuesto según uso real")
        print(f"   4. Implementar optimizaciones si es necesario")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Configurar monitoreo de costos')
    parser.add_argument('--project-name', required=True, help='Nombre del proyecto')
    parser.add_argument('--environment', required=True, help='Ambiente')
    parser.add_argument('--region', default='us-east-1', help='Región de AWS')
    parser.add_argument('--monthly-limit', type=float, default=3500, help='Límite mensual en USD')
    parser.add_argument('--email', help='Email para alertas')
    
    args = parser.parse_args()
    
    monitor = CostMonitoringSetup(args.region)
    monitor.setup_complete_monitoring(
        args.project_name,
        args.environment,
        args.monthly_limit,
        args.email
    )

if __name__ == "__main__":
    main()
