# Guía de Implementación - Prueba de 70 Vehículos

## 📊 Resumen de la Prueba

**Configuración**: 70 vehículos de prueba  
**Duración recomendada**: 14 días (2 semanas)  
**Costo total estimado**: **$26.42 USD**  
**Costo por día**: $1.89 USD  
**Costo por vehículo**: $0.81/mes ($0.027/día)

## 💰 Desglose de Costos

| Servicio | Costo Mensual | Porcentaje |
|----------|---------------|------------|
| AWS IoT Core | $6.56 | 11.6% |
| Kinesis Streams | $11.29 | 19.9% |
| Lambda Functions | $1.18 | 2.1% |
| DynamoDB | $2.98 | 5.3% |
| S3 Storage | $7.25 | 12.8% |
| Otros Servicios | $27.36 | 48.3% |
| **TOTAL** | **$56.62** | **100%** |

### Costos por Período de Prueba
- **1 día**: $1.89
- **3 días**: $5.66
- **1 semana**: $13.21
- **2 semanas**: **$26.42** ⭐ (Recomendado)
- **1 mes**: $56.62

## 🚀 Implementación Paso a Paso

### Paso 1: Preparación del Ambiente

```bash
# Clonar configuración de prueba
cd /home/labuser/vehicle-tracking-infrastructure

# Verificar archivos de configuración
ls -la terraform.tfvars.test
ls -la test_deployment_70_vehicles.tf
```

### Paso 2: Despliegue de Infraestructura

```bash
# Opción A: Despliegue automático completo
python3 examples/setup_test_70_vehicles.py full-setup --region us-east-1

# Opción B: Despliegue paso a paso
python3 examples/setup_test_70_vehicles.py deploy --region us-east-1
```

### Paso 3: Configuración de Vehículos de Prueba

```bash
# Crear certificados IoT para 70 vehículos
python3 examples/setup_test_70_vehicles.py setup-vehicles --region us-east-1

# Esto creará:
# - 70 certificados IoT (TEST001 - TEST070)
# - Políticas de seguridad
# - Configuración de conexión
```

### Paso 4: Configuración de Usuarios de Prueba

```bash
# Crear usuarios en Cognito
python3 examples/setup_test_70_vehicles.py setup-users --region us-east-1

# Usuarios creados:
# - test-admin@vehicletracking.com (FleetManager)
# - test-operator@vehicletracking.com (FleetOperator)  
# - test-customer@vehicletracking.com (Customer)
# Contraseña para todos: TestPass123!
```

### Paso 5: Configuración de Monitoreo

```bash
# Configurar alertas de costo
python3 examples/setup_test_70_vehicles.py setup-monitoring --region us-east-1

# Configuración:
# - Presupuesto: $50/mes
# - Alertas automáticas
# - Dashboard de costos
```

### Paso 6: Iniciar Simuladores (Opcional)

```bash
# Iniciar 5 simuladores de vehículos
python3 examples/setup_test_70_vehicles.py start-simulators --region us-east-1

# Para simuladores individuales:
python3 examples/vehicle_simulator.py \
  --vehicle-id TEST001 \
  --endpoint iot.us-east-1.amazonaws.com \
  --cert test_vehicles/TEST001_cert.pem \
  --key test_vehicles/TEST001_private.key \
  --ca test_vehicles/AmazonRootCA1.pem \
  --duration 60  # minutos
```

## 🔧 Configuración Optimizada para Pruebas

### Recursos Reducidos
- **Kinesis Shards**: 2 (en lugar de 10)
- **Lambda Memory**: 256MB (en lugar de 512MB)
- **ElastiCache**: 1 nodo t3.micro (en lugar de 2)
- **CloudWatch Logs**: Retención de 7 días
- **RDS**: Deshabilitado para pruebas

### Etiquetas de Identificación
Todos los recursos incluyen etiquetas:
```
Project: vehicle-tracking
Environment: test-70v
Purpose: Testing
VehicleCount: 70
TestDuration: 14days
AutoShutdown: true
```

## 📱 Pruebas de Funcionalidad

### 1. Pruebas de IoT Core
```bash
# Verificar conectividad
aws iot describe-endpoint --endpoint-type iot:Data-ATS

# Publicar mensaje de prueba
aws iot-data publish \
  --topic "vehicles/TEST001/telemetry" \
  --payload '{"vehicle_id":"TEST001","speed":65,"fuel":80}'
```

### 2. Pruebas de API Gateway
```bash
# Obtener token de autenticación
API_URL="https://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/test-70v"

# Listar vehículos
curl -X GET "$API_URL/vehicles" \
  -H "Authorization: Bearer $TOKEN"

# Crear contrato de prueba
curl -X POST "$API_URL/contracts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Customer",
    "customer_email": "test@example.com",
    "vehicle_count": 25,
    "contract_type": "STANDARD",
    "monthly_fee": 150.00,
    "contract_duration_months": 12
  }'
```

### 3. Pruebas de Dashboard
```bash
# Ver dashboard de flota
curl -X GET "$API_URL/fleet/dashboard" \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 Monitoreo Durante la Prueba

### Dashboard de CloudWatch
- URL: `https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=vehicle-tracking-test-70v-dashboard`

### Métricas Clave a Monitorear
- **IoT Messages**: Mensajes por minuto
- **Lambda Invocations**: Ejecuciones y errores
- **DynamoDB**: Lecturas/escrituras consumidas
- **Kinesis**: Records procesados
- **Costos**: Gasto diario acumulado

### Alertas Configuradas
- **Costo > $40/mes**: Alerta por email
- **Errores Lambda > 10/min**: Alerta crítica
- **IoT desconexiones > 5**: Alerta de conectividad

## 🧪 Escenarios de Prueba Sugeridos

### Semana 1: Funcionalidad Básica
- **Días 1-2**: Conectividad IoT y telemetría básica
- **Días 3-4**: APIs y autenticación
- **Días 5-7**: Dashboard y reportes

### Semana 2: Funcionalidad Avanzada
- **Días 8-9**: Sistema de contratos y aprobaciones
- **Días 10-11**: Alertas y notificaciones
- **Días 12-14**: Integración DocuSign y pruebas de carga

## 📈 Métricas de Éxito

### Técnicas
- ✅ 99%+ uptime de servicios
- ✅ <2s latencia promedio de APIs
- ✅ 0 errores críticos
- ✅ Procesamiento exitoso de 70 vehículos simultáneos

### Económicas
- ✅ Costo real ≤ $30 (presupuesto $26.42)
- ✅ Costo por vehículo < $0.50/mes
- ✅ 80%+ ahorro vs competencia

### Funcionales
- ✅ Todas las APIs funcionando
- ✅ Dashboard en tiempo real
- ✅ Alertas de pánico < 5s
- ✅ Contratos con firma electrónica

## 🧹 Limpieza Post-Prueba

### Automática (Recomendada)
```bash
# Eliminar todo el ambiente de prueba
python3 examples/setup_test_70_vehicles.py cleanup --region us-east-1
```

### Manual (Si es necesario)
```bash
# Destruir infraestructura
terraform destroy -var-file=terraform.tfvars.test -auto-approve

# Limpiar certificados IoT manualmente si quedan
aws iot list-certificates --query 'certificates[?contains(certificateId, `test`)].certificateId' --output text | \
xargs -I {} aws iot delete-certificate --certificate-id {} --force-delete
```

## 📞 Soporte Durante la Prueba

### Monitoreo de Costos
```bash
# Ver costos actuales
python3 examples/cost_calculator.py --vehicles 70 --optimized

# Ver resumen de la prueba
python3 examples/setup_test_70_vehicles.py summary --region us-east-1
```

### Logs y Debugging
```bash
# Ver logs de Lambda
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/vehicle-tracking-test-70v"

# Ver métricas de IoT
aws cloudwatch get-metric-statistics \
  --namespace AWS/IoT \
  --metric-name PublishIn.Success \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## 🎯 Resultados Esperados

Al final de la prueba de 2 semanas, deberías tener:

1. **Validación técnica completa** de la plataforma
2. **Métricas de rendimiento** reales con 70 vehículos
3. **Confirmación de costos** ultra-competitivos
4. **Experiencia de usuario** validada
5. **Documentación** para escalamiento a producción

**Costo total real esperado**: $26.42 USD (79.8% más barato que competencia)

---

¿Listo para comenzar la prueba? Ejecuta:
```bash
python3 examples/setup_test_70_vehicles.py full-setup --region us-east-1
```
