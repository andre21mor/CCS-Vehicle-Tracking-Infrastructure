import json
import boto3
import os
from datetime import datetime, timedelta
import logging
import base64
import uuid
from decimal import Decimal

# DocuSign imports
try:
    from docusign_esign import ApiClient, EnvelopesApi, EnvelopeDefinition, Document, Signer, SignHere, Tabs, Recipients
    from docusign_esign.client.auth.oauth import OAuthToken
    import jwt
except ImportError:
    # Fallback para desarrollo local
    print("DocuSign SDK no disponible - usando mock")

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
ssm = boto3.client('ssm')
sns = boto3.client('sns')

class DocuSignManager:
    def __init__(self):
        self.config = self._load_docusign_config()
        self.api_client = None
        self._authenticate()
    
    def _load_docusign_config(self):
        """Cargar configuración de DocuSign desde SSM"""
        try:
            parameters = [
                os.environ['DOCUSIGN_INTEGRATION_KEY'],
                os.environ['DOCUSIGN_USER_ID'],
                os.environ['DOCUSIGN_ACCOUNT_ID'],
                os.environ['DOCUSIGN_PRIVATE_KEY'],
                os.environ['DOCUSIGN_BASE_URL']
            ]
            
            response = ssm.get_parameters(
                Names=parameters,
                WithDecryption=True
            )
            
            config = {}
            for param in response['Parameters']:
                key = param['Name'].split('/')[-1]
                config[key] = param['Value']
            
            return config
            
        except Exception as e:
            logger.error(f"Error cargando configuración DocuSign: {str(e)}")
            return {}
    
    def _authenticate(self):
        """Autenticar con DocuSign usando JWT"""
        try:
            if not self.config:
                raise Exception("Configuración de DocuSign no disponible")
            
            # Crear JWT token
            private_key = self.config['private_key'].replace('\\n', '\n')
            
            now = datetime.utcnow()
            token_payload = {
                'iss': self.config['integration_key'],
                'sub': self.config['user_id'],
                'aud': 'account-d.docusign.com',
                'iat': now,
                'exp': now + timedelta(hours=1),
                'scope': 'signature impersonation'
            }
            
            jwt_token = jwt.encode(token_payload, private_key, algorithm='RS256')
            
            # Configurar API client
            self.api_client = ApiClient()
            self.api_client.host = self.config['base_url']
            
            # Obtener access token
            oauth_token = self.api_client.request_jwt_user_token(
                client_id=self.config['integration_key'],
                user_id=self.config['user_id'],
                oauth_host_name='account-d.docusign.com',
                private_key_bytes=private_key.encode(),
                expires_in=3600
            )
            
            self.api_client.set_default_header('Authorization', f'Bearer {oauth_token.access_token}')
            
            logger.info("Autenticación con DocuSign exitosa")
            
        except Exception as e:
            logger.error(f"Error autenticando con DocuSign: {str(e)}")
            self.api_client = None
    
    def create_envelope_for_contract(self, contract_data):
        """Crear envelope de DocuSign para un contrato"""
        try:
            if not self.api_client:
                raise Exception("Cliente DocuSign no autenticado")
            
            # Generar documento PDF del contrato
            contract_pdf = self._generate_contract_pdf(contract_data)
            
            # Crear documento DocuSign
            document = Document(
                document_base64=base64.b64encode(contract_pdf).decode(),
                name=f"Contrato_{contract_data['contract_id']}.pdf",
                file_extension="pdf",
                document_id="1"
            )
            
            # Configurar firmantes
            signers = self._create_signers(contract_data)
            
            # Crear envelope
            envelope_definition = EnvelopeDefinition(
                email_subject=f"Firma de Contrato - {contract_data['customer_name']}",
                email_message=self._get_email_message(contract_data),
                documents=[document],
                recipients=Recipients(signers=signers),
                status="sent"
            )
            
            # Enviar envelope
            envelopes_api = EnvelopesApi(self.api_client)
            results = envelopes_api.create_envelope(
                account_id=self.config['account_id'],
                envelope_definition=envelope_definition
            )
            
            logger.info(f"Envelope creado: {results.envelope_id}")
            
            return {
                'envelope_id': results.envelope_id,
                'status': results.status,
                'uri': results.uri
            }
            
        except Exception as e:
            logger.error(f"Error creando envelope: {str(e)}")
            raise
    
    def _create_signers(self, contract_data):
        """Crear configuración de firmantes"""
        signers = []
        
        # Cliente firmante
        customer_signer = Signer(
            email=contract_data['customer_email'],
            name=contract_data['customer_name'],
            recipient_id="1",
            routing_order="1",
            tabs=Tabs(sign_here_tabs=[
                SignHere(
                    document_id="1",
                    page_number="1",
                    x_position="100",
                    y_position="200"
                )
            ])
        )
        signers.append(customer_signer)
        
        # Representante de la empresa firmante
        company_signer = Signer(
            email="contracts@vehicletracking.com",
            name="Representante Legal",
            recipient_id="2",
            routing_order="2",
            tabs=Tabs(sign_here_tabs=[
                SignHere(
                    document_id="1",
                    page_number="1",
                    x_position="400",
                    y_position="200"
                )
            ])
        )
        signers.append(company_signer)
        
        return signers
    
    def _generate_contract_pdf(self, contract_data):
        """Generar PDF del contrato"""
        # En un entorno real, usarías una librería como ReportLab o WeasyPrint
        # Por ahora, creamos un PDF simple con texto
        
        contract_content = f"""
CONTRATO DE SERVICIOS DE SEGUIMIENTO VEHICULAR

Contrato ID: {contract_data['contract_id']}
Fecha: {datetime.now().strftime('%Y-%m-%d')}

CLIENTE:
Nombre: {contract_data['customer_name']}
Email: {contract_data['customer_email']}
Empresa: {contract_data.get('company_name', 'N/A')}

SERVICIOS:
Tipo de Contrato: {contract_data['contract_type']}
Cantidad de Vehículos: {contract_data['vehicle_count']}
Tarifa Mensual: ${contract_data['monthly_fee']:.2f} por vehículo
Duración: {contract_data['contract_duration_months']} meses
Valor Total: ${contract_data['total_contract_value']:.2f}

TÉRMINOS Y CONDICIONES:
1. El cliente acepta los términos de servicio
2. El pago se realizará mensualmente
3. El servicio incluye monitoreo 24/7
4. Soporte técnico incluido

FIRMAS:
Cliente: ________________    Fecha: ________

Empresa: ________________   Fecha: ________
        """
        
        # Convertir a bytes (simulando PDF)
        return contract_content.encode('utf-8')
    
    def _get_email_message(self, contract_data):
        """Obtener mensaje de email para firma"""
        return f"""
Estimado/a {contract_data['customer_name']},

Por favor firme el contrato de servicios de seguimiento vehicular.

Detalles del contrato:
- Cantidad de vehículos: {contract_data['vehicle_count']}
- Valor mensual: ${contract_data['monthly_fee']:.2f} por vehículo
- Duración: {contract_data['contract_duration_months']} meses

Una vez firmado, procederemos con la activación de los servicios.

Gracias por confiar en nosotros.

Equipo de Seguimiento Vehicular
        """
    
    def get_envelope_status(self, envelope_id):
        """Obtener estado del envelope"""
        try:
            if not self.api_client:
                raise Exception("Cliente DocuSign no autenticado")
            
            envelopes_api = EnvelopesApi(self.api_client)
            envelope = envelopes_api.get_envelope(
                account_id=self.config['account_id'],
                envelope_id=envelope_id
            )
            
            return {
                'envelope_id': envelope_id,
                'status': envelope.status,
                'created': envelope.created_date_time,
                'completed': envelope.completed_date_time
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del envelope: {str(e)}")
            raise

def handler(event, context):
    """
    Handler principal para gestión de firmas DocuSign
    """
    try:
        logger.info(f"Evento recibido: {json.dumps(event)}")
        
        action = event.get('action')
        
        if action == 'create_envelope':
            return handle_create_envelope(event)
        elif action == 'get_status':
            return handle_get_status(event)
        elif action == 'process_signed_contract':
            return handle_process_signed_contract(event)
        else:
            raise ValueError(f"Acción no soportada: {action}")
            
    except Exception as e:
        logger.error(f"Error en docusign_signature_manager: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'action': event.get('action', 'unknown')
            })
        }

def handle_create_envelope(event):
    """Crear envelope para firma"""
    try:
        contract_id = event.get('contract_id')
        if not contract_id:
            raise ValueError("contract_id es requerido")
        
        # Obtener datos del contrato
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        response = contracts_table.get_item(Key={'contract_id': contract_id})
        
        if 'Item' not in response:
            raise ValueError(f"Contrato no encontrado: {contract_id}")
        
        contract_data = response['Item']
        
        # Verificar que el contrato está aprobado
        if contract_data.get('status') != 'APPROVED':
            raise ValueError(f"Contrato no está aprobado: {contract_data.get('status')}")
        
        # Crear envelope en DocuSign
        docusign_manager = DocuSignManager()
        envelope_result = docusign_manager.create_envelope_for_contract(contract_data)
        
        # Guardar información de firma en DynamoDB
        signatures_table = dynamodb.Table(os.environ['SIGNATURES_TABLE'])
        signature_record = {
            'signature_id': str(uuid.uuid4()),
            'contract_id': contract_id,
            'envelope_id': envelope_result['envelope_id'],
            'status': 'SENT',
            'created_at': int(datetime.utcnow().timestamp()),
            'docusign_uri': envelope_result.get('uri', ''),
            'signers': [
                {
                    'email': contract_data['customer_email'],
                    'name': contract_data['customer_name'],
                    'role': 'CUSTOMER',
                    'status': 'PENDING'
                },
                {
                    'email': 'contracts@vehicletracking.com',
                    'name': 'Representante Legal',
                    'role': 'COMPANY',
                    'status': 'PENDING'
                }
            ]
        }
        
        signatures_table.put_item(Item=signature_record)
        
        # Actualizar estado del contrato
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET #status = :status, envelope_id = :envelope_id, signature_sent_at = :sent_at, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PENDING_SIGNATURE',
                ':envelope_id': envelope_result['envelope_id'],
                ':sent_at': int(datetime.utcnow().timestamp()),
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        
        logger.info(f"Envelope creado para contrato {contract_id}: {envelope_result['envelope_id']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Envelope creado exitosamente',
                'contract_id': contract_id,
                'envelope_id': envelope_result['envelope_id'],
                'signature_id': signature_record['signature_id']
            })
        }
        
    except Exception as e:
        logger.error(f"Error creando envelope: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_get_status(event):
    """Obtener estado de firma"""
    try:
        envelope_id = event.get('envelope_id')
        if not envelope_id:
            raise ValueError("envelope_id es requerido")
        
        # Obtener estado de DocuSign
        docusign_manager = DocuSignManager()
        status = docusign_manager.get_envelope_status(envelope_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'envelope_status': status
            })
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estado: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_process_signed_contract(event):
    """Procesar contrato firmado"""
    try:
        contract_id = event.get('contract_id')
        envelope_id = event.get('envelope_id')
        
        if not contract_id or not envelope_id:
            raise ValueError("contract_id y envelope_id son requeridos")
        
        # Actualizar estado del contrato
        contracts_table = dynamodb.Table(os.environ['CONTRACTS_TABLE'])
        contracts_table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET #status = :status, signed_at = :signed_at, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'SIGNED',
                ':signed_at': int(datetime.utcnow().timestamp()),
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        
        # Actualizar registro de firma
        signatures_table = dynamodb.Table(os.environ['SIGNATURES_TABLE'])
        signatures_table.update_item(
            Key={'envelope_id': envelope_id},
            UpdateExpression='SET #status = :status, completed_at = :completed_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':completed_at': int(datetime.utcnow().timestamp())
            }
        )
        
        # Enviar notificación de contrato firmado
        sns.publish(
            TopicArn=os.environ.get('SNS_TOPIC_ARN', ''),
            Subject=f"Contrato Firmado - {contract_id}",
            Message=f"El contrato {contract_id} ha sido firmado exitosamente por todas las partes."
        )
        
        logger.info(f"Contrato {contract_id} procesado como firmado")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Contrato procesado como firmado',
                'contract_id': contract_id,
                'envelope_id': envelope_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error procesando contrato firmado: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

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
