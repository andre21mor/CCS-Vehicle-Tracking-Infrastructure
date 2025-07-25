#!/usr/bin/env python3
"""
Script para configurar usuarios y grupos en Cognito
"""

import boto3
import json
import argparse
from datetime import datetime

class CognitoSetup:
    def __init__(self, region, user_pool_id, client_id):
        self.region = region
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.cognito = boto3.client('cognito-idp', region_name=region)
    
    def create_user_groups(self):
        """Crear grupos de usuarios"""
        groups = [
            {
                'GroupName': 'FleetManagers',
                'Description': 'Administradores de flota con acceso completo',
                'Precedence': 1
            },
            {
                'GroupName': 'FleetOperators',
                'Description': 'Operadores de flota con acceso limitado',
                'Precedence': 2
            },
            {
                'GroupName': 'Drivers',
                'Description': 'Conductores con acceso básico',
                'Precedence': 3
            },
            {
                'GroupName': 'Customers',
                'Description': 'Clientes con acceso a sus vehículos',
                'Precedence': 4
            }
        ]
        
        for group in groups:
            try:
                response = self.cognito.create_group(
                    GroupName=group['GroupName'],
                    UserPoolId=self.user_pool_id,
                    Description=group['Description'],
                    Precedence=group['Precedence']
                )
                print(f"✅ Grupo creado: {group['GroupName']}")
            except self.cognito.exceptions.GroupExistsException:
                print(f"ℹ️  Grupo ya existe: {group['GroupName']}")
            except Exception as e:
                print(f"❌ Error creando grupo {group['GroupName']}: {str(e)}")
    
    def create_admin_user(self, email, password, company_name="Admin Company"):
        """Crear usuario administrador"""
        try:
            # Crear usuario
            response = self.cognito.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'},
                    {'Name': 'custom:company_name', 'Value': company_name},
                    {'Name': 'custom:fleet_size', 'Value': '100'}
                ],
                TemporaryPassword=password,
                MessageAction='SUPPRESS'  # No enviar email de bienvenida
            )
            
            # Establecer contraseña permanente
            self.cognito.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=email,
                Password=password,
                Permanent=True
            )
            
            # Agregar a grupo de administradores
            self.cognito.admin_add_user_to_group(
                UserPoolId=self.user_pool_id,
                Username=email,
                GroupName='FleetManagers'
            )
            
            print(f"✅ Usuario administrador creado: {email}")
            return True
            
        except self.cognito.exceptions.UsernameExistsException:
            print(f"ℹ️  Usuario ya existe: {email}")
            return False
        except Exception as e:
            print(f"❌ Error creando usuario administrador: {str(e)}")
            return False
    
    def create_test_users(self):
        """Crear usuarios de prueba"""
        test_users = [
            {
                'email': 'manager@vehicletracking.com',
                'password': 'TempPass123!',
                'group': 'FleetManagers',
                'attributes': {
                    'custom:company_name': 'Test Fleet Company',
                    'custom:fleet_size': '50'
                }
            },
            {
                'email': 'operator@vehicletracking.com',
                'password': 'TempPass123!',
                'group': 'FleetOperators',
                'attributes': {
                    'custom:company_name': 'Test Fleet Company',
                    'custom:fleet_size': '50'
                }
            },
            {
                'email': 'driver@vehicletracking.com',
                'password': 'TempPass123!',
                'group': 'Drivers',
                'attributes': {
                    'custom:license_number': 'DL123456789',
                    'custom:employee_id': 'EMP001'
                }
            },
            {
                'email': 'customer@vehicletracking.com',
                'password': 'TempPass123!',
                'group': 'Customers',
                'attributes': {
                    'custom:company_name': 'Customer Company',
                    'custom:fleet_size': '10'
                }
            }
        ]
        
        for user in test_users:
            try:
                # Preparar atributos
                user_attributes = [
                    {'Name': 'email', 'Value': user['email']},
                    {'Name': 'email_verified', 'Value': 'true'}
                ]
                
                for attr_name, attr_value in user['attributes'].items():
                    user_attributes.append({'Name': attr_name, 'Value': attr_value})
                
                # Crear usuario
                response = self.cognito.admin_create_user(
                    UserPoolId=self.user_pool_id,
                    Username=user['email'],
                    UserAttributes=user_attributes,
                    TemporaryPassword=user['password'],
                    MessageAction='SUPPRESS'
                )
                
                # Establecer contraseña permanente
                self.cognito.admin_set_user_password(
                    UserPoolId=self.user_pool_id,
                    Username=user['email'],
                    Password=user['password'],
                    Permanent=True
                )
                
                # Agregar a grupo
                self.cognito.admin_add_user_to_group(
                    UserPoolId=self.user_pool_id,
                    Username=user['email'],
                    GroupName=user['group']
                )
                
                print(f"✅ Usuario de prueba creado: {user['email']} ({user['group']})")
                
            except self.cognito.exceptions.UsernameExistsException:
                print(f"ℹ️  Usuario ya existe: {user['email']}")
            except Exception as e:
                print(f"❌ Error creando usuario {user['email']}: {str(e)}")
    
    def setup_mfa_for_drivers(self):
        """Configurar MFA obligatorio para conductores"""
        try:
            # Obtener usuarios del grupo Drivers
            response = self.cognito.list_users_in_group(
                UserPoolId=self.user_pool_id,
                GroupName='Drivers'
            )
            
            for user in response['Users']:
                username = user['Username']
                
                # Configurar MFA como obligatorio
                self.cognito.admin_set_user_mfa_preference(
                    UserPoolId=self.user_pool_id,
                    Username=username,
                    SoftwareTokenMfaSettings={
                        'Enabled': True,
                        'PreferredMfa': True
                    }
                )
                
                print(f"✅ MFA configurado para conductor: {username}")
                
        except Exception as e:
            print(f"❌ Error configurando MFA: {str(e)}")
    
    def create_api_test_token(self, username, password):
        """Crear token de prueba para APIs"""
        try:
            # Autenticar usuario
            response = self.cognito.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            if 'AuthenticationResult' in response:
                tokens = response['AuthenticationResult']
                
                print(f"✅ Tokens generados para {username}:")
                print(f"   Access Token: {tokens['AccessToken'][:50]}...")
                print(f"   ID Token: {tokens['IdToken'][:50]}...")
                print(f"   Refresh Token: {tokens['RefreshToken'][:50]}...")
                
                # Guardar tokens en archivo para pruebas
                token_data = {
                    'username': username,
                    'access_token': tokens['AccessToken'],
                    'id_token': tokens['IdToken'],
                    'refresh_token': tokens['RefreshToken'],
                    'expires_in': tokens['ExpiresIn'],
                    'generated_at': datetime.utcnow().isoformat()
                }
                
                with open(f'test_tokens_{username.replace("@", "_").replace(".", "_")}.json', 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                return tokens
            else:
                print(f"❌ No se pudieron generar tokens para {username}")
                return None
                
        except Exception as e:
            print(f"❌ Error generando tokens: {str(e)}")
            return None
    
    def list_users_and_groups(self):
        """Listar usuarios y sus grupos"""
        try:
            response = self.cognito.list_users(UserPoolId=self.user_pool_id)
            
            print("\n📋 Usuarios registrados:")
            print("-" * 80)
            
            for user in response['Users']:
                username = user['Username']
                email = next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'email'), 'N/A')
                status = user['UserStatus']
                
                # Obtener grupos del usuario
                try:
                    groups_response = self.cognito.admin_list_groups_for_user(
                        UserPoolId=self.user_pool_id,
                        Username=username
                    )
                    groups = [group['GroupName'] for group in groups_response['Groups']]
                except:
                    groups = []
                
                print(f"👤 {email} ({username})")
                print(f"   Estado: {status}")
                print(f"   Grupos: {', '.join(groups) if groups else 'Ninguno'}")
                print()
                
        except Exception as e:
            print(f"❌ Error listando usuarios: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Configurar autenticación Cognito')
    parser.add_argument('--region', required=True, help='Región de AWS')
    parser.add_argument('--user-pool-id', required=True, help='ID del User Pool')
    parser.add_argument('--client-id', required=True, help='ID del Client')
    parser.add_argument('--admin-email', help='Email del administrador')
    parser.add_argument('--admin-password', help='Contraseña del administrador')
    parser.add_argument('--create-test-users', action='store_true', help='Crear usuarios de prueba')
    parser.add_argument('--setup-mfa', action='store_true', help='Configurar MFA para conductores')
    parser.add_argument('--generate-tokens', help='Generar tokens para usuario (email)')
    parser.add_argument('--list-users', action='store_true', help='Listar usuarios')
    
    args = parser.parse_args()
    
    # Inicializar configuración
    setup = CognitoSetup(args.region, args.user_pool_id, args.client_id)
    
    print("🚀 Configurando autenticación Cognito...")
    print(f"   Región: {args.region}")
    print(f"   User Pool: {args.user_pool_id}")
    print(f"   Client ID: {args.client_id}")
    print()
    
    # Crear grupos
    print("📁 Creando grupos de usuarios...")
    setup.create_user_groups()
    print()
    
    # Crear administrador si se especifica
    if args.admin_email and args.admin_password:
        print("👨‍💼 Creando usuario administrador...")
        setup.create_admin_user(args.admin_email, args.admin_password)
        print()
    
    # Crear usuarios de prueba
    if args.create_test_users:
        print("🧪 Creando usuarios de prueba...")
        setup.create_test_users()
        print()
    
    # Configurar MFA
    if args.setup_mfa:
        print("🔐 Configurando MFA para conductores...")
        setup.setup_mfa_for_drivers()
        print()
    
    # Generar tokens
    if args.generate_tokens:
        print(f"🎫 Generando tokens para {args.generate_tokens}...")
        password = input("Ingrese la contraseña: ")
        setup.create_api_test_token(args.generate_tokens, password)
        print()
    
    # Listar usuarios
    if args.list_users:
        setup.list_users_and_groups()
    
    print("✅ Configuración completada!")

if __name__ == "__main__":
    main()
