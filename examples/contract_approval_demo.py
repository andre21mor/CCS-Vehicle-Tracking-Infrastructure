#!/usr/bin/env python3
"""
Demo del sistema de aprobación de contratos
Muestra cómo funciona el flujo de aprobación para contratos de más de 50 vehículos
"""

import requests
import json
import time
from datetime import datetime

class ContractApprovalDemo:
    def __init__(self, api_base_url, auth_token):
        self.api_base_url = api_base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
    
    def create_small_contract(self):
        """Crear contrato pequeño (auto-aprobado)"""
        print("🚛 Creando contrato pequeño (25 vehículos)...")
        
        contract_data = {
            "customer_name": "Transportes Rápidos SAC",
            "customer_email": "contacto@transportesrapidos.com",
            "customer_phone": "+51999123456",
            "company_name": "Transportes Rápidos SAC",
            "vehicle_count": 25,
            "contract_type": "STANDARD",
            "monthly_fee": 150.00,
            "contract_duration_months": 12,
            "contract_terms": {
                "service_level": "BASIC",
                "support_hours": "8x5",
                "data_retention_months": 12
            },
            "billing_address": {
                "street": "Av. Industrial 123",
                "city": "Lima",
                "country": "Peru",
                "postal_code": "15001"
            },
            "technical_requirements": {
                "gps_accuracy": "3m",
                "update_frequency": "30s",
                "offline_storage": "24h"
            }
        }
        
        response = requests.post(
            f"{self.api_base_url}/contracts",
            headers=self.headers,
            json=contract_data
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Contrato creado: {result['contract_id']}")
            print(f"   Requiere aprobación del manager: {result['requires_manager_approval']}")
            print(f"   Tiempo estimado de procesamiento: {result['estimated_processing_time']}")
            return result['contract_id']
        else:
            print(f"❌ Error creando contrato: {response.text}")
            return None
    
    def create_large_contract(self):
        """Crear contrato grande (requiere aprobación)"""
        print("\n🏭 Creando contrato grande (75 vehículos)...")
        
        contract_data = {
            "customer_name": "Logística Nacional EIRL",
            "customer_email": "gerencia@logisticanacional.com",
            "customer_phone": "+51999654321",
            "company_name": "Logística Nacional EIRL",
            "vehicle_count": 75,
            "contract_type": "ENTERPRISE",
            "monthly_fee": 200.00,
            "contract_duration_months": 24,
            "contract_terms": {
                "service_level": "PREMIUM",
                "support_hours": "24x7",
                "data_retention_months": 36,
                "sla_uptime": "99.9%"
            },
            "billing_address": {
                "street": "Av. Javier Prado 456",
                "city": "Lima",
                "country": "Peru",
                "postal_code": "15036"
            },
            "technical_requirements": {
                "gps_accuracy": "1m",
                "update_frequency": "10s",
                "offline_storage": "72h",
                "video_storage": "30d",
                "panic_button": True,
                "driver_behavior_analysis": True
            },
            "special_conditions": [
                "Descuento por volumen del 15%",
                "Instalación gratuita en todas las unidades",
                "Capacitación incluida para 10 operadores"
            ]
        }
        
        response = requests.post(
            f"{self.api_base_url}/contracts",
            headers=self.headers,
            json=contract_data
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Contrato creado: {result['contract_id']}")
            print(f"   Requiere aprobación del manager: {result['requires_manager_approval']}")
            print(f"   Tiempo estimado de procesamiento: {result['estimated_processing_time']}")
            return result['contract_id']
        else:
            print(f"❌ Error creando contrato: {response.text}")
            return None
    
    def check_contract_status(self, contract_id):
        """Verificar estado del contrato"""
        print(f"\n🔍 Verificando estado del contrato {contract_id}...")
        
        response = requests.get(
            f"{self.api_base_url}/contracts/{contract_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            contract = response.json()
            print(f"   Estado: {contract['status']} - {contract['status_description']}")
            print(f"   Próxima acción: {contract['next_action']}")
            
            if contract.get('approval_details'):
                approval = contract['approval_details']
                print(f"   Aprobador asignado: {approval['approver_name']}")
                print(f"   Email del aprobador: {approval['approver_email']}")
                print(f"   Tiempo restante: {approval.get('time_remaining_hours', 0)} horas")
            
            return contract
        else:
            print(f"❌ Error obteniendo contrato: {response.text}")
            return None
    
    def get_pending_approvals(self):
        """Obtener aprobaciones pendientes (como manager)"""
        print("\n📋 Obteniendo aprobaciones pendientes...")
        
        response = requests.get(
            f"{self.api_base_url}/approvals/pending",
            headers=self.headers
        )
        
        if response.status_code == 200:
            result = response.json()
            approvals = result['pending_approvals']
            
            print(f"   Total de aprobaciones pendientes: {result['total']}")
            
            for approval in approvals:
                print(f"\n   📄 Aprobación ID: {approval['approval_id']}")
                print(f"      Contrato: {approval['contract_id']}")
                print(f"      Cliente: {approval['contract_details']['customer_name']}")
                print(f"      Vehículos: {approval['contract_details']['vehicle_count']}")
                print(f"      Valor total: ${approval['contract_details']['total_value']:,.2f}")
                print(f"      Nivel de riesgo: {approval['contract_details']['risk_level']}")
                print(f"      Tiempo restante: {approval['time_remaining_hours']} horas")
                print(f"      Expirado: {'Sí' if approval['is_expired'] else 'No'}")
            
            return approvals
        else:
            print(f"❌ Error obteniendo aprobaciones: {response.text}")
            return []
    
    def approve_contract(self, approval_id, comments=""):
        """Aprobar contrato"""
        print(f"\n✅ Aprobando contrato (ID de aprobación: {approval_id})...")
        
        approval_data = {
            "comments": comments or "Contrato aprobado después de revisión completa"
        }
        
        response = requests.post(
            f"{self.api_base_url}/approvals/{approval_id}/approve",
            headers=self.headers,
            json=approval_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Contrato aprobado exitosamente")
            print(f"   Contrato ID: {result['contract_id']}")
            print(f"   Aprobado por: {result['approved_by']}")
            print(f"   Fecha de aprobación: {result['approved_at']}")
            return True
        else:
            print(f"❌ Error aprobando contrato: {response.text}")
            return False
    
    def reject_contract(self, approval_id, reason):
        """Rechazar contrato"""
        print(f"\n❌ Rechazando contrato (ID de aprobación: {approval_id})...")
        
        rejection_data = {
            "reason": reason
        }
        
        response = requests.post(
            f"{self.api_base_url}/approvals/{approval_id}/reject",
            headers=self.headers,
            json=rejection_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"❌ Contrato rechazado")
            print(f"   Contrato ID: {result['contract_id']}")
            print(f"   Rechazado por: {result['rejected_by']}")
            print(f"   Motivo: {result['rejection_reason']}")
            return True
        else:
            print(f"❌ Error rechazando contrato: {response.text}")
            return False
    
    def get_contracts_dashboard(self):
        """Obtener dashboard de contratos"""
        print("\n📊 Dashboard de contratos...")
        
        response = requests.get(
            f"{self.api_base_url}/contracts/dashboard",
            headers=self.headers
        )
        
        if response.status_code == 200:
            result = response.json()
            dashboard = result['dashboard']
            
            print(f"   Total de contratos: {dashboard['total_contracts']}")
            print(f"   Pendientes de aprobación: {dashboard['pending_approval']}")
            print(f"   Aprobados: {dashboard['approved']}")
            print(f"   Rechazados: {dashboard['rejected']}")
            print(f"   Total de vehículos activos: {dashboard['total_vehicles']}")
            print(f"   Valor total de contratos: ${dashboard['total_value']:,.2f}")
            print(f"   Contratos que requieren aprobación: {dashboard['contracts_requiring_approval']}")
            
            return dashboard
        else:
            print(f"❌ Error obteniendo dashboard: {response.text}")
            return None
    
    def run_demo(self):
        """Ejecutar demo completo"""
        print("🚀 Iniciando demo del sistema de aprobación de contratos")
        print("=" * 60)
        
        # 1. Crear contrato pequeño (auto-aprobado)
        small_contract_id = self.create_small_contract()
        if small_contract_id:
            time.sleep(2)
            self.check_contract_status(small_contract_id)
        
        # 2. Crear contrato grande (requiere aprobación)
        large_contract_id = self.create_large_contract()
        if large_contract_id:
            time.sleep(2)
            self.check_contract_status(large_contract_id)
        
        # 3. Ver dashboard
        self.get_contracts_dashboard()
        
        # 4. Ver aprobaciones pendientes (como manager)
        pending_approvals = self.get_pending_approvals()
        
        # 5. Aprobar o rechazar contratos
        if pending_approvals:
            approval = pending_approvals[0]  # Tomar la primera aprobación
            
            # Simular decisión del manager
            vehicle_count = approval['contract_details']['vehicle_count']
            total_value = approval['contract_details']['total_value']
            risk_level = approval['contract_details']['risk_level']
            
            if risk_level == 'HIGH' or total_value > 300000:
                # Rechazar contratos de alto riesgo o muy costosos
                self.reject_contract(
                    approval['approval_id'],
                    "Contrato excede límites de riesgo establecidos. Requiere revisión adicional del comité ejecutivo."
                )
            else:
                # Aprobar contratos normales
                self.approve_contract(
                    approval['approval_id'],
                    "Contrato revisado y aprobado. Cliente tiene buen historial crediticio."
                )
            
            # Verificar estado final
            time.sleep(2)
            self.check_contract_status(approval['contract_id'])
        
        # 6. Dashboard final
        print("\n" + "=" * 60)
        print("📊 Estado final del sistema:")
        self.get_contracts_dashboard()
        
        print("\n✅ Demo completado exitosamente!")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Demo del sistema de aprobación de contratos')
    parser.add_argument('--api-url', required=True, help='URL base de la API')
    parser.add_argument('--token', required=True, help='Token de autenticación')
    
    args = parser.parse_args()
    
    # Crear instancia del demo
    demo = ContractApprovalDemo(args.api_url, args.token)
    
    # Ejecutar demo
    demo.run_demo()

if __name__ == "__main__":
    main()
