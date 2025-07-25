#!/usr/bin/env python3
"""
Simulador de dispositivo IoT para vehículo
Simula el envío de datos de telemetría, video y alertas de pánico
"""

import json
import time
import random
import ssl
import paho.mqtt.client as mqtt
from datetime import datetime
import base64

class VehicleSimulator:
    def __init__(self, vehicle_id, iot_endpoint, cert_file, key_file, ca_file):
        self.vehicle_id = vehicle_id
        self.iot_endpoint = iot_endpoint
        self.cert_file = cert_file
        self.key_file = key_file
        self.ca_file = ca_file
        
        # Estado del vehículo
        self.location = {"lat": -12.0464, "lng": -77.0428}
        self.speed = 0
        self.fuel_level = 100
        self.engine_temp = 70
        self.is_moving = False
        
        # Cliente MQTT
        self.client = mqtt.Client(client_id=f"vehicle-{vehicle_id}")
        self.setup_mqtt()
    
    def setup_mqtt(self):
        """Configurar conexión MQTT con AWS IoT Core"""
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.load_verify_locations(self.ca_file)
        context.load_cert_chain(self.cert_file, self.key_file)
        
        self.client.tls_set_context(context)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        print(f"Conectando a {self.iot_endpoint}...")
        self.client.connect(self.iot_endpoint, 8883, 60)
        self.client.loop_start()
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback de conexión exitosa"""
        if rc == 0:
            print(f"✅ Vehículo {self.vehicle_id} conectado exitosamente")
            # Suscribirse a comandos
            client.subscribe(f"vehicles/{self.vehicle_id}/commands")
        else:
            print(f"❌ Error de conexión: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Procesar comandos recibidos"""
        try:
            command = json.loads(msg.payload.decode())
            print(f"📨 Comando recibido: {command}")
            self.process_command(command)
        except Exception as e:
            print(f"❌ Error procesando comando: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback de desconexión"""
        print(f"🔌 Vehículo {self.vehicle_id} desconectado")
    
    def process_command(self, command):
        """Procesar comandos remotos"""
        cmd_type = command.get('type')
        
        if cmd_type == 'start_engine':
            self.is_moving = True
            print("🚗 Motor encendido")
        elif cmd_type == 'stop_engine':
            self.is_moving = False
            self.speed = 0
            print("🛑 Motor apagado")
        elif cmd_type == 'emergency_stop':
            self.emergency_stop()
        elif cmd_type == 'request_video':
            self.send_video_data('EVENT')
    
    def generate_telemetry(self):
        """Generar datos de telemetría realistas"""
        if self.is_moving:
            # Simular movimiento
            self.speed = max(0, min(120, self.speed + random.uniform(-5, 10)))
            self.location['lat'] += random.uniform(-0.001, 0.001)
            self.location['lng'] += random.uniform(-0.001, 0.001)
            
            # Consumo de combustible
            self.fuel_level = max(0, self.fuel_level - random.uniform(0.1, 0.3))
            
            # Temperatura del motor
            self.engine_temp = min(120, self.engine_temp + random.uniform(-2, 5))
        else:
            self.speed = 0
            self.engine_temp = max(70, self.engine_temp - random.uniform(1, 3))
        
        return {
            "vehicle_id": self.vehicle_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "location": {
                "lat": round(self.location['lat'], 6),
                "lng": round(self.location['lng'], 6),
                "address": "Lima, Perú"
            },
            "speed": round(self.speed, 1),
            "fuel_level": round(self.fuel_level, 1),
            "engine_temp": round(self.engine_temp, 1),
            "driver_id": f"DR{random.randint(1000, 9999)}",
            "route_id": f"RT{random.randint(100, 999)}",
            "odometer": random.randint(50000, 200000),
            "engine_hours": random.randint(1000, 5000)
        }
    
    def send_telemetry(self):
        """Enviar datos de telemetría"""
        telemetry = self.generate_telemetry()
        topic = f"vehicles/{self.vehicle_id}/telemetry"
        
        self.client.publish(topic, json.dumps(telemetry))
        print(f"📊 Telemetría enviada: Speed={telemetry['speed']}km/h, Fuel={telemetry['fuel_level']}%")
    
    def send_panic_alert(self, panic_type="EMERGENCY"):
        """Simular activación del botón de pánico"""
        panic_data = {
            "vehicle_id": self.vehicle_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "panic_type": panic_type,
            "location": {
                "lat": round(self.location['lat'], 6),
                "lng": round(self.location['lng'], 6),
                "address": "Lima, Perú - EMERGENCIA"
            },
            "driver_info": {
                "name": "Juan Pérez",
                "license": "L12345678"
            },
            "additional_data": {
                "speed_at_panic": round(self.speed, 1),
                "fuel_level": round(self.fuel_level, 1),
                "engine_temp": round(self.engine_temp, 1)
            }
        }
        
        topic = f"vehicles/{self.vehicle_id}/panic"
        self.client.publish(topic, json.dumps(panic_data))
        print(f"🚨 ALERTA DE PÁNICO ENVIADA: {panic_type}")
    
    def send_video_data(self, video_type="CONTINUOUS"):
        """Simular envío de metadatos de video"""
        # Simular frame de imagen en base64 (imagen pequeña de prueba)
        fake_image = b"fake_image_data_for_testing"
        fake_image_b64 = base64.b64encode(fake_image).decode()
        
        video_data = {
            "vehicle_id": self.vehicle_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "video_type": video_type,
            "camera_id": "CAM_FRONT",
            "resolution": "1920x1080",
            "duration_seconds": 30,
            "file_size_mb": random.uniform(10, 50),
            "frame_image": fake_image_b64,  # Frame para análisis
            "metadata": {
                "location": self.location,
                "speed": self.speed,
                "weather": "clear",
                "time_of_day": "day"
            }
        }
        
        if video_type == "EVENT":
            video_data["event_type"] = random.choice([
                "HARD_BRAKING", "SHARP_TURN", "COLLISION_DETECTED", "LANE_DEPARTURE"
            ])
        
        topic = f"vehicles/{self.vehicle_id}/video"
        self.client.publish(topic, json.dumps(video_data))
        print(f"📹 Video data enviado: {video_type}")
    
    def send_diagnostics(self):
        """Enviar datos de diagnóstico del vehículo"""
        diagnostics = {
            "vehicle_id": self.vehicle_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "engine_status": "OK" if self.engine_temp < 100 else "WARNING",
            "battery_voltage": round(random.uniform(12.0, 14.5), 1),
            "tire_pressure": {
                "front_left": round(random.uniform(30, 35), 1),
                "front_right": round(random.uniform(30, 35), 1),
                "rear_left": round(random.uniform(30, 35), 1),
                "rear_right": round(random.uniform(30, 35), 1)
            },
            "brake_status": "OK",
            "transmission_status": "OK",
            "error_codes": [] if random.random() > 0.1 else ["P0301", "P0420"],
            "maintenance_due": random.choice([True, False])
        }
        
        topic = f"vehicles/{self.vehicle_id}/diagnostics"
        self.client.publish(topic, json.dumps(diagnostics))
        print(f"🔧 Diagnósticos enviados")
    
    def emergency_stop(self):
        """Simular parada de emergencia"""
        self.is_moving = False
        self.speed = 0
        self.send_panic_alert("EMERGENCY_STOP")
        print("🛑 PARADA DE EMERGENCIA ACTIVADA")
    
    def simulate_journey(self, duration_minutes=60):
        """Simular un viaje completo"""
        print(f"🚗 Iniciando simulación de viaje para vehículo {self.vehicle_id}")
        print(f"⏱️  Duración: {duration_minutes} minutos")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Encender motor
        self.is_moving = True
        
        telemetry_interval = 5  # segundos
        video_interval = 30     # segundos
        diagnostics_interval = 120  # segundos
        
        last_telemetry = 0
        last_video = 0
        last_diagnostics = 0
        
        try:
            while time.time() < end_time:
                current_time = time.time()
                
                # Enviar telemetría cada 5 segundos
                if current_time - last_telemetry >= telemetry_interval:
                    self.send_telemetry()
                    last_telemetry = current_time
                
                # Enviar video cada 30 segundos
                if current_time - last_video >= video_interval:
                    self.send_video_data("CONTINUOUS")
                    last_video = current_time
                
                # Enviar diagnósticos cada 2 minutos
                if current_time - last_diagnostics >= diagnostics_interval:
                    self.send_diagnostics()
                    last_diagnostics = current_time
                
                # Simular eventos aleatorios
                if random.random() < 0.001:  # 0.1% probabilidad por segundo
                    self.send_panic_alert()
                elif random.random() < 0.005:  # 0.5% probabilidad por segundo
                    self.send_video_data("EVENT")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Simulación interrumpida por el usuario")
        
        # Apagar motor
        self.is_moving = False
        self.speed = 0
        print(f"✅ Simulación completada para vehículo {self.vehicle_id}")
    
    def disconnect(self):
        """Desconectar del broker MQTT"""
        self.client.loop_stop()
        self.client.disconnect()

def main():
    """Función principal para ejecutar el simulador"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulador de vehículo IoT')
    parser.add_argument('--vehicle-id', required=True, help='ID del vehículo')
    parser.add_argument('--endpoint', required=True, help='Endpoint de AWS IoT Core')
    parser.add_argument('--cert', required=True, help='Archivo de certificado')
    parser.add_argument('--key', required=True, help='Archivo de clave privada')
    parser.add_argument('--ca', required=True, help='Archivo CA')
    parser.add_argument('--duration', type=int, default=60, help='Duración en minutos')
    
    args = parser.parse_args()
    
    # Crear simulador
    simulator = VehicleSimulator(
        vehicle_id=args.vehicle_id,
        iot_endpoint=args.endpoint,
        cert_file=args.cert,
        key_file=args.key,
        ca_file=args.ca
    )
    
    try:
        # Esperar conexión
        time.sleep(2)
        
        # Ejecutar simulación
        simulator.simulate_journey(args.duration)
        
    finally:
        simulator.disconnect()

if __name__ == "__main__":
    main()
