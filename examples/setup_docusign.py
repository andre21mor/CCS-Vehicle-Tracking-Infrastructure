#!/usr/bin/env python3
"""
Script para configurar la integración con DocuSign
"""

import boto3
import json
import argparse
from datetime import datetime
import base64

class DocuSignSetup:
    def __init__(self, region, project_name, environment):
        self.region = region
        self.project_name = project_name
        self.environment = environment
        self.ssm = boto3.client('ssm', region_name=region)
    
    def configure_docusign_credentials(self, integration_key, user_id, account_id, private_key_file, base_url=None):
        """Configurar credenciales de DocuSign en SSM Parameter Store"""
        try:
            # Leer private key del archivo
            with open(private_key_file, 'r') as f:
                private_key = f.read()
            
            # Parámetros a configurar
            parameters = [
                {
                    'name': f"/{self.project_name}/{self.environment}/docusign/integration_key",
                    'value': integration_key,
                    'description': 'DocuSign Integration Key'
                },
                {
                    'name': f"/{self.project_name}/{self.environment}/docusign/user_id",
                    'value': user_id,
                    'description': 'DocuSign User ID'
                },
                {
                    'name': f"/{self.project_name}/{self.environment}/docusign/account_id",
                    'value': account_id,
                    'description': 'DocuSign Account ID'
                },
                {
                    'name': f"/{self.project_name}/{self.environment}/docusign/private_key",
                    'value': private_key,
                    'description': 'DocuSign Private Key for JWT'
                }
            ]
            
            # Agregar base URL si se proporciona
            if base_url:
                parameters.append({
                    'name': f"/{self.project_name}/{self.environment}/docusign/base_url",
                    'value': base_url,
                    'description': 'DocuSign API Base URL'
                })
            
            # Crear/actualizar parámetros
            for param in parameters:
                try:
                    self.ssm.put_parameter(
                        Name=param['name'],
                        Value=param['value'],
                        Type='SecureString',
                        Description=param['description'],
                        Overwrite=True,
                        Tags=[
                            {
                                'Key': 'Project',
                                'Value': self.project_name
                            },
                            {
                                'Key': 'Environment',
                                'Value': self.environment
                            },
                            {
                                'Key': 'Service',
                                'Value': 'DocuSign'
                            }
                        ]
                    )
                    print(f"✅ Parámetro configurado: {param['name']}")
                except Exception as e:
                    print(f"❌ Error configurando {param['name']}: {str(e)}")
            
            print(f"\n✅ Configuración de DocuSign completada para {self.project_name}-{self.environment}")
            
        except Exception as e:
            print(f"❌ Error configurando DocuSign: {str(e)}")
    
    def test_docusign_connection(self):
        """Probar conexión con DocuSign"""
        try:
            # Obtener parámetros configurados
            parameter_names = [
                f"/{self.project_name}/{self.environment}/docusign/integration_key",
                f"/{self.project_name}/{self.environment}/docusign/user_id",
                f"/{self.project_name}/{self.environment}/docusign/account_id",
                f"/{self.project_name}/{self.environment}/docusign/base_url"
            ]
            
            response = self.ssm.get_parameters(
                Names=parameter_names,
                WithDecryption=True
            )
            
            config = {}
            for param in response['Parameters']:
                key = param['Name'].split('/')[-1]
                config[key] = param['Value']
            
            print("🔍 Configuración actual de DocuSign:")
            print(f"   Integration Key: {config.get('integration_key', 'NO CONFIGURADO')[:20]}...")
            print(f"   User ID: {config.get('user_id', 'NO CONFIGURADO')}")
            print(f"   Account ID: {config.get('account_id', 'NO CONFIGURADO')}")
            print(f"   Base URL: {config.get('base_url', 'NO CONFIGURADO')}")
            
            # En un entorno real, aquí harías una llamada de prueba a la API de DocuSign
            print("\n⚠️  Para probar la conexión completamente, ejecute el test de integración después del despliegue")
            
        except Exception as e:
            print(f"❌ Error probando conexión: {str(e)}")
    
    def generate_sample_private_key(self):
        """Generar ejemplo de private key para desarrollo"""
        sample_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN
OPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP
QRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQR
STUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRST
UVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUV
WXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX
YZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ12
34567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234
567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456
7890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ12345678
90abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890
abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890ab
cdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcd
efghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdef
ghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefgh
ijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghij
klmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijkl
mnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmn
opqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnop
qrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqr
stuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrst
uvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuv
wxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwx
yzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz
-----END RSA PRIVATE KEY-----"""
        
        with open('docusign_sample_private_key.pem', 'w') as f:
            f.write(sample_key)
        
        print("📄 Archivo de ejemplo creado: docusign_sample_private_key.pem")
        print("⚠️  IMPORTANTE: Este es solo un ejemplo. Use su private key real de DocuSign.")
    
    def setup_webhook_configuration(self):
        """Mostrar configuración de webhook para DocuSign"""
        webhook_url = f"https://api.{self.project_name}-{self.environment}.com/docusign-webhook"
        
        print("🔗 Configuración de Webhook en DocuSign:")
        print(f"   URL del Webhook: {webhook_url}")
        print("   Eventos a suscribir:")
        print("   - envelope-completed")
        print("   - envelope-declined") 
        print("   - envelope-voided")
        print("   - recipient-completed")
        print("\n📋 Pasos para configurar en DocuSign:")
        print("1. Inicie sesión en su cuenta de DocuSign")
        print("2. Vaya a Settings > Connect")
        print("3. Agregue una nueva configuración de Connect")
        print(f"4. Configure la URL: {webhook_url}")
        print("5. Seleccione los eventos listados arriba")
        print("6. Habilite 'Include Certificate of Completion'")
        print("7. Guarde la configuración")
    
    def create_test_contract(self):
        """Crear contrato de prueba para DocuSign"""
        test_contract = {
            "customer_name": "Empresa de Prueba SAC",
            "customer_email": "test@empresaprueba.com",
            "customer_phone": "+51999123456",
            "company_name": "Empresa de Prueba SAC",
            "vehicle_count": 75,  # Más de 50 para requerir aprobación
            "contract_type": "ENTERPRISE",
            "monthly_fee": 180.00,
            "contract_duration_months": 18,
            "contract_terms": {
                "service_level": "PREMIUM",
                "support_hours": "24x7",
                "data_retention_months": 24
            },
            "billing_address": {
                "street": "Av. Test 123",
                "city": "Lima",
                "country": "Peru",
                "postal_code": "15001"
            },
            "technical_requirements": {
                "gps_accuracy": "1m",
                "update_frequency": "15s",
                "video_storage": "30d"
            }
        }
        
        with open('test_contract_docusign.json', 'w') as f:
            json.dump(test_contract, f, indent=2)
        
        print("📄 Contrato de prueba creado: test_contract_docusign.json")
        print("   Este contrato requiere aprobación del manager (>50 vehículos)")
        print("   Una vez aprobado, se enviará automáticamente a DocuSign para firma")

def main():
    parser = argparse.ArgumentParser(description='Configurar integración con DocuSign')
    parser.add_argument('--region', required=True, help='Región de AWS')
    parser.add_argument('--project-name', required=True, help='Nombre del proyecto')
    parser.add_argument('--environment', required=True, help='Ambiente (dev, staging, prod)')
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando para configurar credenciales
    config_parser = subparsers.add_parser('configure', help='Configurar credenciales de DocuSign')
    config_parser.add_argument('--integration-key', required=True, help='DocuSign Integration Key')
    config_parser.add_argument('--user-id', required=True, help='DocuSign User ID')
    config_parser.add_argument('--account-id', required=True, help='DocuSign Account ID')
    config_parser.add_argument('--private-key-file', required=True, help='Archivo con private key')
    config_parser.add_argument('--base-url', help='Base URL de DocuSign API')
    
    # Comando para probar conexión
    subparsers.add_parser('test', help='Probar configuración de DocuSign')
    
    # Comando para generar ejemplo de private key
    subparsers.add_parser('generate-sample-key', help='Generar ejemplo de private key')
    
    # Comando para mostrar configuración de webhook
    subparsers.add_parser('webhook-config', help='Mostrar configuración de webhook')
    
    # Comando para crear contrato de prueba
    subparsers.add_parser('create-test-contract', help='Crear contrato de prueba')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    setup = DocuSignSetup(args.region, args.project_name, args.environment)
    
    print(f"🚀 Configurando DocuSign para {args.project_name}-{args.environment}")
    print(f"   Región: {args.region}")
    print()
    
    if args.command == 'configure':
        setup.configure_docusign_credentials(
            args.integration_key,
            args.user_id,
            args.account_id,
            args.private_key_file,
            args.base_url
        )
    elif args.command == 'test':
        setup.test_docusign_connection()
    elif args.command == 'generate-sample-key':
        setup.generate_sample_private_key()
    elif args.command == 'webhook-config':
        setup.setup_webhook_configuration()
    elif args.command == 'create-test-contract':
        setup.create_test_contract()
    
    print("\n✅ Operación completada!")

if __name__ == "__main__":
    main()
