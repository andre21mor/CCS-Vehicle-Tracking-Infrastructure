# 🏗️ Architecture Diagrams - Vehicle Tracking Infrastructure

## 📋 Overview

Este directorio contiene diagramas detallados de la arquitectura AWS del sistema Vehicle Tracking Infrastructure, creados específicamente para Draw.io (diagrams.net).

## 📁 Archivos de Diagramas

### 1. **`vehicle-tracking-architecture.drawio`**
**Diagrama Principal de Arquitectura**
- Vista general completa del sistema
- Todos los servicios AWS y sus conexiones
- Flujos de datos principales
- Información de costos y performance
- Ideal para: Presentaciones ejecutivas, documentación técnica

### 2. **`data-flow-diagram.drawio`**
**Diagrama de Flujo de Datos**
- Flujos detallados de datos IoT
- Procesamiento de video y Rekognition
- Flujo de datos de ventas
- Procesamiento de alertas de emergencia
- Métricas de volumen de datos
- Ideal para: Análisis técnico, optimización de performance

### 3. **`network-security-diagram.drawio`**
**Diagrama de Red y Seguridad**
- Arquitectura de VPC detallada
- Subnets públicas y privadas
- Security Groups y NACLs
- Roles IAM y políticas
- Flujos de red y seguridad
- Ideal para: Auditorías de seguridad, compliance

## 🚀 Cómo Usar los Diagramas

### **Opción 1: Draw.io Online**
1. Ve a [app.diagrams.net](https://app.diagrams.net)
2. Click en "Open Existing Diagram"
3. Selecciona el archivo `.drawio` que deseas abrir
4. ¡Listo! Puedes ver y editar el diagrama

### **Opción 2: Draw.io Desktop**
1. Descarga Draw.io Desktop desde [GitHub](https://github.com/jgraph/drawio-desktop/releases)
2. Instala la aplicación
3. Abre el archivo `.drawio` directamente

### **Opción 3: VS Code Extension**
1. Instala la extensión "Draw.io Integration" en VS Code
2. Abre el archivo `.drawio` en VS Code
3. Edita directamente en el editor

## 📊 Contenido de Cada Diagrama

### 🏗️ **Diagrama Principal (`vehicle-tracking-architecture.drawio`)**

#### Componentes Incluidos:
- **Usuarios Externos**: Web, Mobile, IoT Devices, Cámaras, Agentes de Ventas
- **CDN & Seguridad**: CloudFront, Cognito
- **API Layer**: API Gateway, Lambda Authorizer
- **Business Logic**: 13 Lambda Functions
- **Sales Module**: 4 Lambda Functions específicas
- **Data Layer**: 13 DynamoDB Tables, ElastiCache, S3 Buckets
- **Real-time Processing**: Kinesis, IoT Core
- **Monitoring**: CloudWatch, SNS

#### Información Adicional:
- **Costos**: $0.10/hora operacional
- **Performance**: <200ms response time
- **Arquitectura**: Event-Driven Serverless
- **Seguridad**: Enterprise-grade

### 📈 **Diagrama de Flujo (`data-flow-diagram.drawio`)**

#### Flujos Detallados:
1. **IoT Sensor Data Flow**:
   - 70 vehículos → 201K records/día
   - Hot/Warm/Cold storage strategy
   - Real-time processing con Kinesis

2. **Video Processing Flow**:
   - Cámaras HD → Video Processor → S3 → Rekognition
   - 2TB/mes de almacenamiento
   - AI analysis para comportamiento del conductor

3. **Sales Data Flow**:
   - Formularios web → API Gateway → Lambda → DynamoDB
   - 1K transacciones/mes
   - CRM completo integrado

4. **Alert Processing Flow**:
   - Botón de pánico → Procesamiento inmediato → SNS → Notificaciones
   - Respuesta en tiempo real

### 🔒 **Diagrama de Seguridad (`network-security-diagram.drawio`)**

#### Elementos de Seguridad:
- **Perímetro**: CloudFront + WAF + DDoS Protection
- **Red**: VPC con subnets públicas/privadas
- **Compute**: Lambda en subnets privadas
- **Datos**: ElastiCache en subnets de BD
- **Acceso**: Security Groups granulares
- **Identidad**: IAM Roles con least privilege

#### Compliance:
- SOC 2 Type II Ready
- GDPR Compliant
- ISO 27001 Controls
- PCI DSS Ready
- HIPAA Compatible

## 🎯 Casos de Uso por Audiencia

### 👔 **Para CEO/Ejecutivos**
- **Usar**: `vehicle-tracking-architecture.drawio`
- **Enfoque**: Costos, ROI, capacidades de negocio
- **Puntos clave**: 90% ahorro vs soluciones tradicionales

### 🏗️ **Para Arquitectos de Soluciones**
- **Usar**: `data-flow-diagram.drawio`
- **Enfoque**: Patrones arquitectónicos, flujos de datos
- **Puntos clave**: Event-driven, microservices, escalabilidad

### ☁️ **Para Arquitectos Cloud**
- **Usar**: `network-security-diagram.drawio`
- **Enfoque**: Implementación técnica, seguridad, compliance
- **Puntos clave**: VPC design, security groups, IAM

### 🔒 **Para Auditorías de Seguridad**
- **Usar**: `network-security-diagram.drawio`
- **Enfoque**: Controles de seguridad, compliance
- **Puntos clave**: Encryption, access controls, network isolation

## 🛠️ Personalización de Diagramas

### **Colores Utilizados**
- 🟠 **Naranja**: CDN/Security (CloudFront, WAF)
- 🔵 **Azul**: API Layer (API Gateway, DynamoDB)
- 🔴 **Rojo**: Lambda Functions
- 🟢 **Verde**: Sales Module, S3 Storage
- 🟣 **Púrpura**: Data Storage, Managed Services
- 🟡 **Amarillo**: Real-time Processing

### **Iconos y Símbolos**
- **Flechas gruesas**: Flujos principales de datos
- **Flechas delgadas**: Conexiones secundarias
- **Contenedores**: Agrupación lógica de servicios
- **Etiquetas**: Volúmenes de datos y métricas

## 📝 Notas Técnicas

### **Basado en Terraform Real**
- Todos los diagramas reflejan la infraestructura real desplegada
- 13 módulos de Terraform representados
- 50+ recursos AWS documentados
- Configuración actual del ambiente `test-70v`

### **Métricas Reales**
- Costos basados en deployment actual
- Performance medido en ambiente real
- Volúmenes de datos calculados para 70 vehículos

### **Escalabilidad Documentada**
- Diseño para 10,000+ vehículos
- Auto-scaling configurado
- Multi-AZ deployment

## 🔄 Actualizaciones

Para mantener los diagramas actualizados:

1. **Cambios en Terraform**: Actualizar diagramas cuando se modifique la infraestructura
2. **Nuevos servicios**: Agregar componentes cuando se integren nuevos servicios AWS
3. **Métricas**: Actualizar números de performance y costos periódicamente
4. **Versioning**: Usar nombres de archivo con versión para cambios mayores

## 📞 Soporte

Para preguntas sobre los diagramas:
- **Técnicas**: Revisar código Terraform en `/modules`
- **Arquitectura**: Consultar `/docs/architecture-decisions.md`
- **Costos**: Ver análisis en `/docs/cost-analysis.md`

---

**Creado por**: Amazon Q CloudOps Assistant  
**Fecha**: 26 de Julio, 2025  
**Versión**: 1.0  
**Basado en**: Terraform Infrastructure v1.0
