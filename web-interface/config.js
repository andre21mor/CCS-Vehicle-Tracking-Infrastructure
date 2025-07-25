// Configuración de la aplicación web
const CONFIG = {
    // Configuración AWS obtenida del despliegue de Terraform
    COGNITO_USER_POOL_ID: 'us-east-1_7bPnuc8m8',
    COGNITO_CLIENT_ID: '66sq2g4tpeehsqi0im0lf32p4f',
    API_BASE_URL: 'https://qiaz9dfl08.execute-api.us-east-1.amazonaws.com/test-70v',
    AWS_REGION: 'us-east-1'
};

// También mantener la estructura anterior para compatibilidad
const APP_CONFIG = {
    // Configuración AWS obtenida del despliegue de Terraform
    aws: {
        region: 'us-east-1',
        userPoolId: 'us-east-1_7bPnuc8m8',
        clientId: '66sq2g4tpeehsqi0im0lf32p4f',
        apiBaseUrl: 'https://qiaz9dfl08.execute-api.us-east-1.amazonaws.com/test-70v'
    },
    
    // Configuración de módulos
    modules: {
        client: {
            name: 'Módulo Cliente',
            description: 'Gestión de flota y monitoreo para clientes',
            endpoints: [
                '/fleet/dashboard',
                '/vehicles',
                '/reports',
                '/notifications'
            ]
        },
        sales: {
            name: 'Módulo Ventas',
            description: 'Gestión de inventario y contratos de venta',
            endpoints: [
                '/vehicles',
                '/vehicles/{id}/telemetry',
                '/contracts',
                '/approvals'
            ]
        }
    },
    
    // Usuarios de prueba (estos deberían crearse en Cognito)
    testUsers: {
        client: {
            username: 'cliente_test',
            password: 'TempPass123!',
            userPool: 'client_pool'
        },
        sales: {
            username: 'ventas_test',
            password: 'TempPass123!',
            userPool: 'client_pool'
        }
    },
    
    // Configuración de la interfaz
    ui: {
        theme: 'modern',
        autoRefresh: true,
        refreshInterval: 30000, // 30 segundos
        maxRetries: 3
    }
};

// Exportar configuración para uso en otros archivos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CONFIG, APP_CONFIG };
}
