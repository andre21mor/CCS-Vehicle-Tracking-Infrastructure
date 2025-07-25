# 🚀 Guía Rápida - Interfaz Web de Pruebas

## ⚡ Inicio Rápido

### 1. Acceder a la Interfaz
```bash
# La interfaz ya está disponible en:
http://localhost:8080
```

### 2. Usuarios de Prueba Creados ✅
| Módulo | Usuario | Contraseña | Email |
|--------|---------|------------|-------|
| Cliente | `cliente_test` | `TempPass123!` | cliente@vehicletracking.test |
| Ventas | `ventas_test` | `TempPass123!` | ventas@vehicletracking.test |
| Admin | `admin_test` | `TempPass123!` | admin@vehicletracking.test |

### 3. Pasos para Probar

#### 🏢 Módulo Cliente
1. Abrir http://localhost:8080
2. Seleccionar "Módulo Cliente"
3. Ingresar credenciales: `cliente_test` / `TempPass123!`
4. Hacer clic en "Autenticar"
5. Probar funciones:
   - 📊 Dashboard de Flota
   - 🚗 Listar Vehículos
   - 📈 Generar Reportes
   - 🔔 Enviar Notificación

#### 💼 Módulo Ventas
1. Seleccionar "Módulo Ventas"
2. Ingresar credenciales: `ventas_test` / `TempPass123!`
3. Hacer clic en "Autenticar"
4. Probar funciones:
   - 📦 Inventario de Vehículos
   - 📡 Telemetría de Vehículo
   - ➕ Registrar Vehículo
   - 📄 Ver Contratos
   - ✅ Aprobaciones Pendientes

## 🔧 Configuración Técnica

### Endpoints API Disponibles
```
Base URL: https://qiaz9dfl08.execute-api.us-east-1.amazonaws.com/test-70v

Cliente:
- GET /fleet/dashboard
- GET /vehicles
- GET /reports
- POST /notifications

Ventas:
- GET /vehicles
- GET /vehicles/{id}/telemetry
- POST /vehicles
- GET /contracts (simulado)
- GET /approvals (simulado)
```

### Cognito Configuration
```
User Pool ID: us-east-1_7bPnuc8m8
Client ID: 66sq2g4tpeehsqi0im0lf32p4f
Region: us-east-1
```

## 🎯 Funcionalidades de Prueba

### ✅ Funciones Implementadas
- ✅ Autenticación con Amazon Cognito
- ✅ Cambio entre módulos Cliente/Ventas
- ✅ Llamadas a API con autenticación JWT
- ✅ Visualización de respuestas JSON
- ✅ Manejo de errores
- ✅ Estado de conexión en tiempo real

### 📊 Datos de Prueba
- Dashboard con 70 vehículos simulados
- 3 vehículos de ejemplo con telemetría
- Reportes de flota con métricas
- 3 contratos de ejemplo
- 3 aprobaciones pendientes
- Notificaciones del sistema

## 🐛 Solución de Problemas

### Error de Autenticación
```bash
# Verificar usuarios en Cognito
aws cognito-idp list-users --user-pool-id us-east-1_7bPnuc8m8 --region us-east-1
```

### Error de API
- Verificar que el token JWT sea válido
- Revisar logs en CloudWatch: `/aws/apigateway/vehicle-tracking-test-70v`

### Servidor Web No Responde
```bash
# Reiniciar servidor
cd /home/labuser/vehicle-tracking-infrastructure/web-interface
pkill -f "python3 -m http.server"
python3 -m http.server 8080 &
```

## 📱 Características de la Interfaz

### 🎨 Diseño
- Interfaz moderna y responsiva
- Sidebar con selección de módulos
- Área de autenticación integrada
- Visualización de respuestas JSON
- Indicadores de estado en tiempo real

### 🔐 Seguridad
- Autenticación JWT con Amazon Cognito
- Tokens de sesión persistentes
- Validación de permisos por módulo
- Manejo seguro de credenciales

### 📊 Monitoreo
- Estado de conexión visual
- Logs de errores en consola
- Respuestas de API en tiempo real
- Indicadores de carga

## 🚀 Próximos Pasos

Para un entorno de producción, considere:
- Implementar HTTPS
- Mejorar el manejo de errores
- Agregar validación de formularios
- Implementar refresh automático de tokens
- Agregar pruebas automatizadas
- Mejorar la interfaz de usuario

---

**🎉 ¡La interfaz está lista para usar!**

Abra http://localhost:8080 y comience a probar los módulos de Cliente y Ventas.
