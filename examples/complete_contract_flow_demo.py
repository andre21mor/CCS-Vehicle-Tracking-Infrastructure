#!/usr/bin/env python3
"""
Demo completo del flujo de contratos con DocuSign
Muestra todo el proceso desde creación hasta firma electrónica
"""

import requests
import json
import time
from datetime import datetime

class CompleteContractFlowDemo:
    def __init__(self, api_base_url, customer_token, manager_token):
        self.api_base_url = api_base_url.rstrip('/')
        self.customer_headers = {
            'Authorization': f'Bearer {customer_token}',
            'Content-Type': 'application/json'
        }
        self.manager_headers = {
            'Authorization': f'Bearer {manager_token}',
            'Content-Type': 'application/json'
        }
    
    def run_complete_demo(self):
        """Ejecutar demo completo del flujo de contratos"""
        print("🚀 DEMO COMPLETO: Flujo de Contratos con DocuSign")
        print("=" * 70)
        
        # Paso 1: Cliente crea contrato grande
        print("\n📋 PASO 1: Cliente crea contrato (75 vehículos)")
        contract_id = self.create_large_contract()
        
        if not contract_id:
            print("❌ No se pudo crear el contrato. Terminando demo.")
            return
        
        # Paso 2: Verificar que requiere aprobación
        print(f"\n🔍 PASO 2: Verificar estado del contrato {contract_id}")
        contract = self.check_contract_status(contract_id)
        
        if not contract or contract.get('status') != 'PENDING_MANAGER_APPROVAL':
            print("❌ El contrato no está en estado de aprobación pendiente")
            return
        
        # Paso 3: Manager ve aprobaciones pendientes
        print("\n👨‍💼 PASO 3: Manager revisa aprobaciones pendientes")
        pending_approvals = self.get_pending_approvals_as_manager()
        
        if not pending_approvals:
            print("❌ No hay aprobaciones pendientes")
            return
        
        # Encontrar la aprobación de nuestro contrato
        target_approval = None
        for approval in pending_approvals:
            if approval['contract_id'] == contract_id:
                target_approval = approval
                break
        
        if not target_approval:
            print(f"❌ No se encontró aprobación para contrato {contract_id}")
            return
        
        # Paso 4: Manager aprueba el contrato
        print(f"\n✅ PASO 4: Manager aprueba contrato {contract_id}")
        approval_success = self.approve_contract_as_manager(
            target_approval['approval_id'],
            "Contrato aprobado. Cliente tiene buen historial y los términos son aceptables."
        )
        
        if not approval_success:
            print("❌ No se pudo aprobar el contrato")
            return
        
        # Paso 5: Verificar que se inició el proceso de firma
        print(f"\n📝 PASO 5: Verificar inicio del proceso de firma")
        time.sleep(5)  # Esperar a que se procese
        
        contract = self.check_contract_status(contract_id)
        if contract and contract.get('status') == 'PENDING_SIGNATURE':
            print(f"✅ Contrato enviado a DocuSign para firma")
            print(f"   Envelope ID: {contract.get('envelope_id', 'N/A')}")
        else:
            print(f"⚠️  Estado actual: {contract.get('status', 'DESCONOCIDO')}")
        
        # Paso 6: Simular proceso de firma (en la vida real, esto sería manual)
        print(f"\n🖊️  PASO 6: Proceso de firma en DocuSign")
        print("   En la vida real:")
        print("   1. Cliente recibe email de DocuSign")
        print("   2. Cliente revisa y firma el contrato")
        print("   3. Representante legal firma el contrato")
        print("   4. DocuSign envía webhook de completado")
        print("   5. Sistema actualiza estado a 'SIGNED'")
        
        # Simular webhook de DocuSign (solo para demo)
        if contract.get('envelope_id'):
            print(f"\n🔄 PASO 7: Simular webhook de DocuSign")
            self.simulate_docusign_webhook(contract_id, contract['envelope_id'])
        
        # Paso 8: Verificar estado final
        print(f"\n🏁 PASO 8: Verificar estado final del contrato")
        time.sleep(2)
        final_contract = self.check_contract_status(contract_id)
        
        if final_contract:
            print(f"   Estado final: {final_contract.get('status', 'DESCONOCIDO')}")
            print(f"   Descripción: {final_contract.get('status_description', 'N/A')}")
            
            if final_contract.get('status') == 'SIGNED':
                print("🎉 ¡CONTRATO COMPLETADO EXITOSAMENTE!")
                print("   El servicio puede ser activado")
            else:
                print("⏳ Contrato aún en proceso...")
        
        # Paso 9: Dashboard final
        print(f"\n📊 PASO 9: Dashboard final del sistema")
        self.show_contracts_dashboard()
        
        print("\n" + "=" * 70)
        print("✅ DEMO COMPLETO FINALIZADO")
        print("   Flujo demostrado:")
        print("   Cliente → Contrato → Aprobación Manager → DocuSign → Firma → Activación")
    
    def create_large_contract(self):
        """Crear contrato que requiere aprobación"""
        contract_data = {
            "customer_name": "Logística Empresarial EIRL",
            "customer_email": "gerencia@logisticaempresarial.com",
            "customer_phone": "+51999888777",
            "company_name": "Logística Empresarial EIRL",
            "vehicle_count": 75,  # Más de 50 para requerir aprobación
            "contract_type": "ENTERPRISE",
            "monthly_fee": 185.00,
            "contract_duration_months": 36,
            "contract_terms": {
                "service_level": "PREMIUM",
                "support_hours": "24x7",
                "data_retention_months": 60,
                "sla_uptime": "99.95%",
                "backup_frequency": "daily"
            },
            "billing_address": {
                "street": "Av. Empresarial 789",
                "city": "Lima",
                "state": "Lima",
                "country": "Peru",
                "postal_code": "15047"
            },
            "technical_requirements": {
                "gps_accuracy": "1m",
                "update_frequency": "5s",
                "offline_storage": "168h",
                "video_storage": "60d",
                "panic_button": True,
                "driver_behavior_analysis": True,
                "fuel_monitoring": True,
                "maintenance_alerts": True
            },
            "special_conditions": [
                "Descuento por volumen del 20% aplicado",
                "Instalación gratuita en todas las unidades",
                "Capacitación incluida para 15 operadores",
                "Soporte técnico prioritario 24/7",
                "Garantía extendida de 3 años en hardware"
            ]
        }
        
        print("   Creando contrato empresarial...")
        print(f"   Cliente: {contract_data['customer_name']}")
        print(f"   Vehículos: {contract_data['vehicle_count']}")
        print(f"   Valor mensual: ${contract_data['monthly_fee'] * contract_data['vehicle_count']:,.2f}")
        print(f"   Valor total: ${contract_data['monthly_fee'] * contract_data['vehicle_count'] * contract_data['contract_duration_months']:,.2f}")
        
        response = requests.post(
            f"{self.api_base_url}/contracts",
            headers=self.customer_headers,
            json=contract_data
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Contrato creado: {result['contract_id']}")
            print(f"   Requiere aprobación: {result['requires_manager_approval']}")
            print(f"   Tiempo estimado: {result['estimated_processing_time']}")
            return result['contract_id']
        else:
            print(f"❌ Error creando contrato: {response.text}")
            return None
    
    def check_contract_status(self, contract_id):
        """Verificar estado del contrato"""
        response = requests.get(
            f"{self.api_base_url}/contracts/{contract_id}",
            headers=self.customer_headers
        )
        
        if response.status_code == 200:
            contract = response.json()
            print(f"   Estado: {contract['status']} - {contract['status_description']}")
            print(f"   Próxima acción: {contract['next_action']}")
            
            if contract.get('approval_details'):
                approval = contract['approval_details']
                print(f"   Aprobador: {approval['approver_name']} ({approval['approver_email']})")
                print(f"   Tiempo restante: {approval.get('time_remaining_hours', 0)} horas")
            
            return contract
        else:
            print(f"❌ Error obteniendo contrato: {response.text}")
            return None
    
    def get_pending_approvals_as_manager(self):
        """Obtener aprobaciones pendientes como manager"""
        response = requests.get(
            f"{self.api_base_url}/approvals/pending",
            headers=self.manager_headers
        )
        
        if response.status_code == 200:
            result = response.json()
            approvals = result['pending_approvals']
            
            print(f"   Total de aprobaciones pendientes: {result['total']}")
            
            for i, approval in enumerate(approvals, 1):
                print(f"\n   📄 Aprobación {i}:")
                print(f"      ID: {approval['approval_id']}")
                print(f"      Contrato: {approval['contract_id']}")
                print(f"      Cliente: {approval['contract_details']['customer_name']}")
                print(f"      Vehículos: {approval['contract_details']['vehicle_count']}")
                print(f"      Valor: ${approval['contract_details']['total_value']:,.2f}")
                print(f"      Riesgo: {approval['contract_details']['risk_level']}")
                print(f"      Tiempo restante: {approval['time_remaining_hours']} horas")
            
            return approvals
        else:
            print(f"❌ Error obteniendo aprobaciones: {response.text}")
            return []
    
    def approve_contract_as_manager(self, approval_id, comments):
        """Aprobar contrato como manager"""
        approval_data = {
            "comments": comments
        }
        
        print(f"   Aprobando con comentarios: {comments}")
        
        response = requests.post(
            f"{self.api_base_url}/approvals/{approval_id}/approve",
            headers=self.manager_headers,
            json=approval_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Contrato aprobado exitosamente")
            print(f"   Contrato: {result['contract_id']}")
            print(f"   Aprobado por: {result['approved_by']}")
            print(f"   Fecha: {result['approved_at']}")
            return True
        else:
            print(f"❌ Error aprobando contrato: {response.text}")
            return False
    
    def simulate_docusign_webhook(self, contract_id, envelope_id):
        """Simular webhook de DocuSign (solo para demo)"""
        print("   Simulando proceso de firma en DocuSign...")
        print("   1. Cliente recibe email y firma ✅")
        print("   2. Representante legal firma ✅")
        print("   3. DocuSign marca envelope como completado ✅")
        
        # En un entorno real, esto sería un webhook real de DocuSign
        webhook_data = {
            "event": "envelope-completed",
            "data": {
                "envelopeData": {
                    "envelopeId": envelope_id,
                    "envelopeStatus": "completed",
                    "completedDateTime": datetime.utcnow().isoformat()
                }
            }
        }
        
        # Simular llamada al webhook
        response = requests.post(
            f"{self.api_base_url}/docusign-webhook",
            headers={'Content-Type': 'application/json'},
            json=webhook_data
        )
        
        if response.status_code == 200:
            print("✅ Webhook de DocuSign procesado exitosamente")
        else:
            print(f"⚠️  Error simulando webhook: {response.status_code}")
    
    def show_contracts_dashboard(self):
        """Mostrar dashboard de contratos"""
        response = requests.get(
            f"{self.api_base_url}/contracts/dashboard",
            headers=self.manager_headers
        )
        
        if response.status_code == 200:
            result = response.json()
            dashboard = result['dashboard']
            
            print("   📊 Estadísticas del sistema:")
            print(f"      Total contratos: {dashboard['total_contracts']}")
            print(f"      Pendientes aprobación: {dashboard['pending_approval']}")
            print(f"      Aprobados: {dashboard['approved']}")
            print(f"      Firmados: {dashboard.get('signed', 0)}")
            print(f"      Rechazados: {dashboard['rejected']}")
            print(f"      Vehículos activos: {dashboard['total_vehicles']}")
            print(f"      Valor total: ${dashboard['total_value']:,.2f}")
        else:
            print(f"❌ Error obteniendo dashboard: {response.text}")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Demo completo del flujo de contratos con DocuSign')
    parser.add_argument('--api-url', required=True, help='URL base de la API')
    parser.add_argument('--customer-token', required=True, help='Token de cliente')
    parser.add_argument('--manager-token', required=True, help='Token de manager')
    
    args = parser.parse_args()
    
    # Crear instancia del demo
    demo = CompleteContractFlowDemo(args.api_url, args.customer_token, args.manager_token)
    
    # Ejecutar demo completo
    demo.run_complete_demo()

if __name__ == "__main__":
    main()
