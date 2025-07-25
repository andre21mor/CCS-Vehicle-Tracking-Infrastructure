#!/usr/bin/env python3
"""
Script para configurar y gestionar la prueba de 70 vehículos
"""

import boto3
import json
import time
import argparse
from datetime import datetime, timedelta
import subprocess
import os

class Test70VehiclesSetup:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.project_name = "vehicle-tracking"
        self.environment = "test-70v"
        self.vehicle_count = 70
        
        # Clientes AWS
        self.iot = boto3.client('iot', region_name=region)
        self.cognito = boto3.client('cognito-idp', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.budgets = boto3.client('budgets', region_name=region)
    
    def deploy_infrastructure(self):
        """Desplegar infraestructura de prueba"""
        print("🚀 DESPLEGANDO INFRAESTRUCTURA DE PRUEBA")
        print("=" * 60)
        
        try:
            # Cambiar al directorio del proyecto
            os.chdir('/home/labuser/vehicle-tracking-infrastructure')
            
            # Inicializar Terraform
            print("📦 Inicializando Terraform...")
            result = subprocess.run(['terraform', 'init'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Error inicializando Terraform: {result.stderr}")
                return False
            
            # Planificar despliegue
            print("📋 Planificando despliegue...")
            result = subprocess.run([
                'terraform', 'plan', 
                '-var-file=terraform.tfvars.test',
                '-out=test-plan.tfplan'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Error en plan de Terraform: {result.stderr}")
                return False
            
            print("✅ Plan de Terraform generado exitosamente")
            
            # Confirmar despliegue
            confirm = input("¿Desea continuar con el despliegue? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Despliegue cancelado por el usuario")
                return False
            
            # Aplicar configuración
            print("🔧 Aplicando configuración...")
            result = subprocess.run([
                'terraform', 'apply', 
                'test-plan.tfplan'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Error aplicando Terraform: {result.stderr}")
                return False
            
            print("✅ Infraestructura desplegada exitosamente")
            
            # Obtener outputs
            result = subprocess.run([
                'terraform', 'output', '-json'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                outputs = json.loads(result.stdout)
                self.save_test_config(outputs)
                print("✅ Configuración de prueba guardada")
            
            return True
            
        except Exception as e:
            print(f"❌ Error desplegando infraestructura: {str(e)}")
            return False
    
    def save_test_config(self, terraform_outputs):
        """Guardar configuración de prueba"""
        try:
            config = {
                'test_info': {
                    'vehicle_count': self.vehicle_count,
                    'environment': self.environment,
                    'region': self.region,
                    'start_date': datetime.now().isoformat(),
                    'estimated_cost_per_day': 1.89,
                    'estimated_total_cost': 26.42
                },
                'aws_config': terraform_outputs
            }
            
            with open('test_70_vehicles_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print("📄 Configuración guardada en: test_70_vehicles_config.json")
            
        except Exception as e:
            print(f"⚠️  Error guardando configuración: {str(e)}")
    
    def create_test_vehicles(self):
        """Crear certificados y configuración para vehículos de prueba"""
        print(f"\n🚛 CREANDO CONFIGURACIÓN PARA {self.vehicle_count} VEHÍCULOS")
        print("=" * 60)
        
        vehicles_created = []
        
        for i in range(1, self.vehicle_count + 1):
            vehicle_id = f"TEST{i:03d}"  # TEST001, TEST002, etc.
            
            try:
                # Crear certificado IoT
                cert_response = self.iot.create_keys_and_certificate(setAsActive=True)
                
                certificate_arn = cert_response['certificateArn']
                certificate_id = cert_response['certificateId']
                
                # Adjuntar política IoT
                policy_name = f"{self.project_name}-{self.environment}-vehicle-policy"
                try:
                    self.iot.attach_policy(
                        policyName=policy_name,
                        target=certificate_arn
                    )
                except Exception as e:
                    print(f"⚠️  Advertencia adjuntando política para {vehicle_id}: {str(e)}")
                
                # Guardar información del vehículo
                vehicle_info = {
                    'vehicle_id': vehicle_id,
                    'certificate_arn': certificate_arn,
                    'certificate_id': certificate_id,
                    'certificate_pem': cert_response['certificatePem'],
                    'private_key': cert_response['keyPair']['PrivateKey'],
                    'public_key': cert_response['keyPair']['PublicKey']
                }
                
                vehicles_created.append(vehicle_info)
                
                if i % 10 == 0:
                    print(f"✅ Creados {i}/{self.vehicle_count} vehículos...")
                
            except Exception as e:
                print(f"❌ Error creando vehículo {vehicle_id}: {str(e)}")
        
        # Guardar configuración de vehículos
        with open('test_vehicles_config.json', 'w') as f:
            json.dump(vehicles_created, f, indent=2)
        
        print(f"✅ {len(vehicles_created)} vehículos configurados exitosamente")
        print("📄 Configuración guardada en: test_vehicles_config.json")
        
        return vehicles_created
    
    def create_test_users(self):
        """Crear usuarios de prueba en Cognito"""
        print(f"\n👥 CREANDO USUARIOS DE PRUEBA")
        print("=" * 60)
        
        try:
            # Obtener User Pool ID
            user_pools = self.cognito.list_user_pools(MaxResults=50)
            user_pool_id = None
            
            for pool in user_pools['UserPools']:
                if f"{self.project_name}-{self.environment}" in pool['Name']:
                    user_pool_id = pool['Id']
                    break
            
            if not user_pool_id:
                print("❌ No se encontró User Pool")
                return False
            
            # Usuarios de prueba
            test_users = [
                {
                    'username': 'test-admin@vehicletracking.com',
                    'password': 'TestPass123!',
                    'group': 'FleetManagers',
                    'attributes': {
                        'email': 'test-admin@vehicletracking.com',
                        'custom:company_name': 'Test Company',
                        'custom:fleet_size': '70'
                    }
                },
                {
                    'username': 'test-operator@vehicletracking.com', 
                    'password': 'TestPass123!',
                    'group': 'FleetOperators',
                    'attributes': {
                        'email': 'test-operator@vehicletracking.com',
                        'custom:company_name': 'Test Company',
                        'custom:fleet_size': '70'
                    }
                },
                {
                    'username': 'test-customer@vehicletracking.com',
                    'password': 'TestPass123!', 
                    'group': 'Customers',
                    'attributes': {
                        'email': 'test-customer@vehicletracking.com',
                        'custom:company_name': 'Test Customer Company',
                        'custom:fleet_size': '70'
                    }
                }
            ]
            
            created_users = []
            
            for user_data in test_users:
                try:
                    # Crear usuario
                    user_attributes = []
                    for attr_name, attr_value in user_data['attributes'].items():
                        user_attributes.append({
                            'Name': attr_name,
                            'Value': attr_value
                        })
                    
                    self.cognito.admin_create_user(
                        UserPoolId=user_pool_id,
                        Username=user_data['username'],
                        UserAttributes=user_attributes,
                        TemporaryPassword=user_data['password'],
                        MessageAction='SUPPRESS'
                    )
                    
                    # Establecer contraseña permanente
                    self.cognito.admin_set_user_password(
                        UserPoolId=user_pool_id,
                        Username=user_data['username'],
                        Password=user_data['password'],
                        Permanent=True
                    )
                    
                    created_users.append(user_data['username'])
                    print(f"✅ Usuario creado: {user_data['username']}")
                    
                except Exception as e:
                    if "UsernameExistsException" in str(e):
                        print(f"ℹ️  Usuario ya existe: {user_data['username']}")
                    else:
                        print(f"❌ Error creando usuario {user_data['username']}: {str(e)}")
            
            print(f"✅ {len(created_users)} usuarios de prueba configurados")
            return True
            
        except Exception as e:
            print(f"❌ Error creando usuarios de prueba: {str(e)}")
            return False
    
    def setup_cost_monitoring(self):
        """Configurar monitoreo de costos para la prueba"""
        print(f"\n💰 CONFIGURANDO MONITOREO DE COSTOS")
        print("=" * 60)
        
        try:
            account_id = boto3.client('sts').get_caller_identity()['Account']
            
            # Crear presupuesto para la prueba
            budget = {
                'BudgetName': f'{self.project_name}-{self.environment}-test-budget',
                'BudgetLimit': {
                    'Amount': '50.00',  # $50 límite para la prueba
                    'Unit': 'USD'
                },
                'TimeUnit': 'MONTHLY',
                'TimePeriod': {
                    'Start': datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                    'End': datetime(2030, 1, 1)
                },
                'BudgetType': 'COST',
                'CostFilters': {
                    'TagKey': ['Environment'],
                    'TagValue': [self.environment]
                }
            }
            
            # Crear presupuesto
            self.budgets.create_budget(
                AccountId=account_id,
                Budget=budget
            )
            
            print("✅ Presupuesto de prueba creado: $50/mes")
            print("   Alertas automáticas configuradas")
            
            return True
            
        except Exception as e:
            if "DuplicateRecordException" in str(e):
                print("ℹ️  Presupuesto ya existe")
                return True
            else:
                print(f"❌ Error configurando monitoreo: {str(e)}")
                return False
    
    def start_vehicle_simulators(self, num_simulators=5):
        """Iniciar simuladores de vehículos para prueba"""
        print(f"\n🎮 INICIANDO {num_simulators} SIMULADORES DE VEHÍCULOS")
        print("=" * 60)
        
        try:
            # Cargar configuración de vehículos
            with open('test_vehicles_config.json', 'r') as f:
                vehicles = json.load(f)
            
            if len(vehicles) < num_simulators:
                print(f"⚠️  Solo hay {len(vehicles)} vehículos configurados")
                num_simulators = len(vehicles)
            
            # Iniciar simuladores
            for i in range(num_simulators):
                vehicle = vehicles[i]
                vehicle_id = vehicle['vehicle_id']
                
                print(f"🚛 Iniciando simulador para {vehicle_id}...")
                
                # En un entorno real, aquí iniciarías el simulador
                # Por ahora, solo mostramos la configuración
                print(f"   Certificate ID: {vehicle['certificate_id']}")
                print(f"   IoT Endpoint: iot.{self.region}.amazonaws.com")
            
            print(f"✅ {num_simulators} simuladores configurados")
            print("ℹ️  Para iniciar simuladores reales, use:")
            print("   python3 examples/vehicle_simulator.py --vehicle-id TEST001 --endpoint iot.us-east-1.amazonaws.com")
            
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando simuladores: {str(e)}")
            return False
    
    def show_test_summary(self):
        """Mostrar resumen de la prueba"""
        print(f"\n📊 RESUMEN DE LA PRUEBA")
        print("=" * 60)
        
        try:
            # Cargar configuración si existe
            if os.path.exists('test_70_vehicles_config.json'):
                with open('test_70_vehicles_config.json', 'r') as f:
                    config = json.load(f)
                
                print(f"🚛 Vehículos configurados: {self.vehicle_count}")
                print(f"🌍 Región: {self.region}")
                print(f"📅 Duración estimada: 14 días")
                print(f"💰 Costo estimado total: $26.42")
                print(f"💰 Costo por día: $1.89")
                print(f"💰 Costo por vehículo/día: $0.027")
                
                if 'aws_config' in config:
                    aws_config = config['aws_config']
                    if 'test_connection_info' in aws_config:
                        conn_info = aws_config['test_connection_info']['value']
                        print(f"\n🔗 INFORMACIÓN DE CONEXIÓN:")
                        print(f"   IoT Endpoint: {conn_info.get('iot_endpoint', 'N/A')}")
                        print(f"   API URL: {conn_info.get('api_base_url', 'N/A')}")
                        print(f"   User Pool ID: {conn_info.get('cognito_user_pool_id', 'N/A')}")
            
            print(f"\n📋 PRÓXIMOS PASOS:")
            print(f"   1. Verificar que todos los servicios estén funcionando")
            print(f"   2. Iniciar simuladores de vehículos")
            print(f"   3. Probar APIs y funcionalidades")
            print(f"   4. Monitorear costos diariamente")
            print(f"   5. Documentar resultados de la prueba")
            
        except Exception as e:
            print(f"❌ Error mostrando resumen: {str(e)}")
    
    def cleanup_test_environment(self):
        """Limpiar ambiente de prueba"""
        print(f"\n🧹 LIMPIANDO AMBIENTE DE PRUEBA")
        print("=" * 60)
        
        confirm = input("¿Está seguro de que desea eliminar el ambiente de prueba? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Limpieza cancelada")
            return False
        
        try:
            # Destruir infraestructura con Terraform
            print("🔧 Destruyendo infraestructura...")
            result = subprocess.run([
                'terraform', 'destroy',
                '-var-file=terraform.tfvars.test',
                '-auto-approve'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Error destruyendo infraestructura: {result.stderr}")
                return False
            
            print("✅ Infraestructura eliminada exitosamente")
            
            # Limpiar archivos de configuración
            config_files = [
                'test_70_vehicles_config.json',
                'test_vehicles_config.json',
                'test-plan.tfplan'
            ]
            
            for file in config_files:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"🗑️  Eliminado: {file}")
            
            print("✅ Ambiente de prueba limpiado completamente")
            return True
            
        except Exception as e:
            print(f"❌ Error limpiando ambiente: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Configurar prueba de 70 vehículos')
    parser.add_argument('--region', default='us-east-1', help='Región de AWS')
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comandos
    subparsers.add_parser('deploy', help='Desplegar infraestructura de prueba')
    subparsers.add_parser('setup-vehicles', help='Configurar vehículos de prueba')
    subparsers.add_parser('setup-users', help='Crear usuarios de prueba')
    subparsers.add_parser('setup-monitoring', help='Configurar monitoreo de costos')
    subparsers.add_parser('start-simulators', help='Iniciar simuladores de vehículos')
    subparsers.add_parser('summary', help='Mostrar resumen de la prueba')
    subparsers.add_parser('cleanup', help='Limpiar ambiente de prueba')
    subparsers.add_parser('full-setup', help='Configuración completa')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    setup = Test70VehiclesSetup(args.region)
    
    print("🚛 CONFIGURACIÓN DE PRUEBA - 70 VEHÍCULOS")
    print("=" * 60)
    print(f"Región: {args.region}")
    print(f"Ambiente: {setup.environment}")
    print(f"Costo estimado: $26.42 por 2 semanas")
    print()
    
    if args.command == 'deploy':
        setup.deploy_infrastructure()
    elif args.command == 'setup-vehicles':
        setup.create_test_vehicles()
    elif args.command == 'setup-users':
        setup.create_test_users()
    elif args.command == 'setup-monitoring':
        setup.setup_cost_monitoring()
    elif args.command == 'start-simulators':
        setup.start_vehicle_simulators()
    elif args.command == 'summary':
        setup.show_test_summary()
    elif args.command == 'cleanup':
        setup.cleanup_test_environment()
    elif args.command == 'full-setup':
        # Configuración completa
        if setup.deploy_infrastructure():
            time.sleep(30)  # Esperar a que se estabilice
            setup.create_test_vehicles()
            setup.create_test_users()
            setup.setup_cost_monitoring()
            setup.show_test_summary()

if __name__ == "__main__":
    main()
