# Interfaz Web de Pruebas - Vehicle Tracking System

Esta interfaz web permite probar el acceso a los módulos de **Ventas** y **Cliente** del sistema de seguimiento vehicular.

## 🚀 Características

### Módulo Cliente
- **Dashboard de Flota**: Visualización del estado general de la flota
- **Listado de Vehículos**: Consulta de vehículos registrados
- **Reportes**: Generación de reportes de actividad
- **Notificaciones**: Envío y recepción de notificaciones

### Módulo Ventas
- **Inventario de Vehículos**: Gestión del inventario disponible
- **Telemetría**: Consulta de datos de telemetría por vehículo
- **Registro de Vehículos**: Alta de nuevos vehículos
- **Gestión de Contratos**: Visualización y gestión de contratos
- **Aprobaciones**: Gestión de aprobaciones pendientes

## 🔧 Configuración

### Información de Conexión
```
API Base URL: https://qiaz9dfl08.execute-api.us-east-1.amazonaws.com/test-70v
User Pool ID: us-east-1_7bPnuc8m8
Client ID: 66sq2g4tpeehsqi0im0lf32p4f
Región: us-east-1
```

### Usuarios de Prueba
Para probar la interfaz, necesitará crear usuarios en Amazon Cognito:

1. **Acceder a la consola de AWS Cognito**
2. **Navegar al User Pool**: `us-east-1_7bPnuc8m8`
3. **Crear usuarios de prueba**:
   - Usuario Cliente: `cliente_test`
   - Usuario Ventas: `ventas_test`
   - Contraseña temporal: `TempPass123!`

## 📋 Instrucciones de Uso

### 1. Abrir la Interfaz
```bash
# Navegar al directorio
cd /home/labuser/vehicle-tracking-infrastructure/web-interface

# Abrir en navegador (o usar un servidor web local)
python3 -m http.server 8080
# Luego abrir: http://localhost:8080
```

### 2. Autenticación
1. Seleccionar el módulo deseado (Cliente o Ventas)
2. Ingresar credenciales de usuario
3. Hacer clic en "Autenticar"
4. El estado cambiará a "Conectado" cuando sea exitoso

### 3. Probar Funcionalidades
- **Módulo Cliente**: Probar dashboard, vehículos, reportes y notificaciones
- **Módulo Ventas**: Probar inventario, telemetría, registro y contratos

## 🔐 Seguridad

### Autenticación
- Utiliza Amazon Cognito para autenticación segura
- Tokens JWT para autorización de API
- Sesiones persistentes con renovación automática

### Autorización
- Cada endpoint requiere token de autenticación válido
- Los permisos se validan en el API Gateway
- Separación de roles entre módulos

## 🛠️ Desarrollo

### Estructura de Archivos
```
web-interface/
├── index.html          # Interfaz principal
├── config.js           # Configuración de la aplicación
├── README.md           # Esta documentación
└── assets/             # Recursos adicionales (opcional)
```

### APIs Disponibles

#### Módulo Cliente
- `GET /fleet/dashboard` - Dashboard de flota
- `GET /vehicles` - Listar vehículos
- `GET /reports` - Generar reportes
- `POST /notifications` - Enviar notificaciones

#### Módulo Ventas
- `GET /vehicles` - Inventario de vehículos
- `GET /vehicles/{id}/telemetry` - Telemetría específica
- `POST /vehicles` - Registrar nuevo vehículo
- `GET /contracts` - Listar contratos (simulado)
- `GET /approvals` - Aprobaciones pendientes (simulado)

## 🐛 Solución de Problemas

### Error de Autenticación
- Verificar que el usuario existe en Cognito
- Confirmar que la contraseña es correcta
- Revisar que el User Pool ID y Client ID sean correctos

### Error de API
- Verificar que el token de autenticación sea válido
- Confirmar que el endpoint existe
- Revisar los logs de CloudWatch para más detalles

### Problemas de CORS
- El API Gateway debe tener CORS configurado correctamente
- Verificar que los headers de autorización estén permitidos

## 📊 Monitoreo

### CloudWatch Logs
- Logs de API Gateway: `/aws/apigateway/vehicle-tracking-test-70v`
- Logs de Lambda: `/aws/lambda/vehicle-tracking-test-70v-*`

### Métricas
- Dashboard de CloudWatch: `vehicle-tracking-test-70v-monitoring`
- Métricas de API Gateway y Lambda disponibles

## 🔄 Actualizaciones

Para actualizar la configuración después de cambios en la infraestructura:

1. Ejecutar `terraform output` para obtener nuevos valores
2. Actualizar `config.js` con los nuevos endpoints
3. Actualizar `index.html` si es necesario
4. Probar la conectividad

## 📞 Soporte

Para problemas técnicos:
1. Revisar los logs de CloudWatch
2. Verificar el estado de los recursos en AWS
3. Consultar la documentación de la API
4. Revisar la configuración de Cognito

---

**Nota**: Esta es una interfaz de pruebas. Para producción, considere implementar:
- Manejo de errores más robusto
- Validación de entrada mejorada
- Interfaz de usuario más pulida
- Pruebas automatizadas
- Configuración de entorno separada
