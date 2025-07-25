// Datos de prueba para la interfaz web
const TEST_DATA = {
    // Datos simulados para el dashboard de flota
    fleetDashboard: {
        summary: {
            total_vehicles: 70,
            active_vehicles: 65,
            inactive_vehicles: 5,
            alerts_count: 3,
            last_updated: new Date().toISOString()
        },
        recent_alerts: [
            {
                id: "ALT001",
                vehicle_id: "VH001",
                type: "maintenance",
                message: "Mantenimiento programado vencido",
                timestamp: "2025-01-24T15:30:00Z",
                severity: "medium"
            },
            {
                id: "ALT002",
                vehicle_id: "VH015",
                type: "fuel",
                message: "Nivel de combustible bajo",
                timestamp: "2025-01-24T14:45:00Z",
                severity: "low"
            },
            {
                id: "ALT003",
                vehicle_id: "VH032",
                type: "panic",
                message: "Botón de pánico activado",
                timestamp: "2025-01-24T13:20:00Z",
                severity: "high"
            }
        ],
        vehicle_status_distribution: {
            active: 65,
            maintenance: 3,
            inactive: 2
        }
    },

    // Lista de vehículos
    vehicles: [
        {
            vehicle_id: "VH001",
            make: "Toyota",
            model: "Corolla",
            year: 2023,
            status: "active",
            location: {
                lat: 19.4326,
                lng: -99.1332,
                address: "Ciudad de México, CDMX"
            },
            last_update: "2025-01-24T16:00:00Z",
            driver: "Juan Pérez",
            fuel_level: 85,
            mileage: 15420
        },
        {
            vehicle_id: "VH002",
            make: "Nissan",
            model: "Sentra",
            year: 2022,
            status: "active",
            location: {
                lat: 19.4284,
                lng: -99.1276,
                address: "Polanco, CDMX"
            },
            last_update: "2025-01-24T15:55:00Z",
            driver: "María García",
            fuel_level: 92,
            mileage: 22100
        },
        {
            vehicle_id: "VH003",
            make: "Chevrolet",
            model: "Aveo",
            year: 2023,
            status: "maintenance",
            location: {
                lat: 19.4205,
                lng: -99.1590,
                address: "Taller Central, CDMX"
            },
            last_update: "2025-01-24T10:30:00Z",
            driver: null,
            fuel_level: 45,
            mileage: 8750
        }
    ],

    // Datos de telemetría
    telemetry: {
        vehicle_id: "VH001",
        timestamp: new Date().toISOString(),
        location: {
            lat: 19.4326,
            lng: -99.1332,
            speed: 45,
            heading: 180
        },
        engine: {
            rpm: 2200,
            temperature: 89,
            oil_pressure: 35,
            fuel_level: 85
        },
        diagnostics: {
            engine_status: "normal",
            brake_status: "normal",
            transmission_status: "normal",
            battery_voltage: 12.6,
            odometer: 15420
        },
        driver_behavior: {
            harsh_acceleration: 0,
            harsh_braking: 1,
            speeding_events: 0,
            idle_time: 120
        }
    },

    // Reportes
    reports: {
        report_type: "fleet_summary",
        generated_at: new Date().toISOString(),
        period: {
            start: "2025-01-17T00:00:00Z",
            end: "2025-01-24T23:59:59Z"
        },
        summary: {
            total_distance: 12450.5,
            total_fuel_consumed: 890.2,
            average_fuel_efficiency: 14.0,
            total_driving_time: 156.5,
            maintenance_alerts: 5,
            safety_incidents: 2
        },
        top_vehicles: [
            {
                vehicle_id: "VH001",
                distance: 1250.5,
                fuel_efficiency: 15.2,
                driver_score: 92
            },
            {
                vehicle_id: "VH002",
                distance: 1180.3,
                fuel_efficiency: 14.8,
                driver_score: 88
            },
            {
                vehicle_id: "VH003",
                distance: 980.7,
                fuel_efficiency: 13.5,
                driver_score: 85
            }
        ]
    },

    // Contratos (simulado)
    contracts: [
        {
            id: "CT001",
            client_name: "Empresa Logística ABC",
            client_id: "CLI001",
            vehicle_count: 25,
            contract_type: "fleet_management",
            start_date: "2025-01-01",
            end_date: "2025-12-31",
            status: "active",
            monthly_fee: 15000.00,
            services: [
                "GPS Tracking",
                "Maintenance Alerts",
                "Driver Monitoring",
                "Fuel Management"
            ],
            contact_person: {
                name: "Carlos Rodríguez",
                email: "carlos@logisticaabc.com",
                phone: "+52-55-1234-5678"
            }
        },
        {
            id: "CT002",
            client_name: "Transportes XYZ S.A.",
            client_id: "CLI002",
            vehicle_count: 15,
            contract_type: "basic_tracking",
            start_date: "2025-02-01",
            end_date: "2026-01-31",
            status: "pending_approval",
            monthly_fee: 8500.00,
            services: [
                "GPS Tracking",
                "Basic Reports"
            ],
            contact_person: {
                name: "Ana Martínez",
                email: "ana@transportesxyz.com",
                phone: "+52-55-9876-5432"
            }
        },
        {
            id: "CT003",
            client_name: "Delivery Express",
            client_id: "CLI003",
            vehicle_count: 30,
            contract_type: "premium",
            start_date: "2024-06-01",
            end_date: "2025-05-31",
            status: "active",
            monthly_fee: 22000.00,
            services: [
                "GPS Tracking",
                "Real-time Monitoring",
                "Driver Behavior Analysis",
                "Panic Button",
                "Video Recording",
                "Advanced Analytics"
            ],
            contact_person: {
                name: "Roberto Silva",
                email: "roberto@deliveryexpress.com",
                phone: "+52-55-5555-1234"
            }
        }
    ],

    // Aprobaciones pendientes
    approvals: [
        {
            id: "AP001",
            type: "contract_modification",
            contract_id: "CT001",
            client_name: "Empresa Logística ABC",
            requested_by: "Carlos Rodríguez",
            request_date: "2025-01-20T10:30:00Z",
            description: "Solicitud para agregar 5 vehículos adicionales al contrato",
            current_vehicles: 25,
            requested_vehicles: 30,
            additional_cost: 3000.00,
            status: "pending",
            priority: "medium"
        },
        {
            id: "AP002",
            type: "service_upgrade",
            contract_id: "CT002",
            client_name: "Transportes XYZ S.A.",
            requested_by: "Ana Martínez",
            request_date: "2025-01-22T14:15:00Z",
            description: "Upgrade de plan básico a plan premium",
            current_plan: "basic_tracking",
            requested_plan: "premium",
            additional_cost: 13500.00,
            status: "pending",
            priority: "high"
        },
        {
            id: "AP003",
            type: "contract_renewal",
            contract_id: "CT003",
            client_name: "Delivery Express",
            requested_by: "Roberto Silva",
            request_date: "2025-01-23T09:45:00Z",
            description: "Renovación anticipada del contrato por 2 años adicionales",
            current_end_date: "2025-05-31",
            requested_end_date: "2027-05-31",
            discount_applied: 10,
            status: "pending",
            priority: "low"
        }
    ],

    // Notificaciones
    notifications: [
        {
            id: "NOT001",
            type: "maintenance",
            title: "Mantenimiento Programado",
            message: "El vehículo VH001 requiere mantenimiento en 500 km",
            timestamp: "2025-01-24T16:30:00Z",
            read: false,
            priority: "medium",
            vehicle_id: "VH001"
        },
        {
            id: "NOT002",
            type: "alert",
            title: "Botón de Pánico Activado",
            message: "Alerta de pánico desde vehículo VH032 - Ubicación: Av. Insurgentes Sur",
            timestamp: "2025-01-24T13:20:00Z",
            read: true,
            priority: "high",
            vehicle_id: "VH032"
        },
        {
            id: "NOT003",
            type: "system",
            title: "Actualización del Sistema",
            message: "Nueva versión del sistema disponible con mejoras de seguridad",
            timestamp: "2025-01-24T08:00:00Z",
            read: false,
            priority: "low",
            vehicle_id: null
        }
    ]
};

// Función para obtener datos simulados
function getTestData(type, params = {}) {
    switch (type) {
        case 'dashboard':
            return TEST_DATA.fleetDashboard;
        
        case 'vehicles':
            if (params.id) {
                return TEST_DATA.vehicles.find(v => v.vehicle_id === params.id);
            }
            return TEST_DATA.vehicles;
        
        case 'telemetry':
            const telemetryData = { ...TEST_DATA.telemetry };
            if (params.vehicle_id) {
                telemetryData.vehicle_id = params.vehicle_id;
            }
            // Simular datos en tiempo real
            telemetryData.timestamp = new Date().toISOString();
            telemetryData.location.speed = Math.floor(Math.random() * 80) + 20;
            telemetryData.engine.rpm = Math.floor(Math.random() * 2000) + 1500;
            return telemetryData;
        
        case 'reports':
            return TEST_DATA.reports;
        
        case 'contracts':
            return { contracts: TEST_DATA.contracts };
        
        case 'approvals':
            return { pending_approvals: TEST_DATA.approvals };
        
        case 'notifications':
            return TEST_DATA.notifications;
        
        default:
            return { error: 'Tipo de datos no encontrado' };
    }
}

// Exportar para uso en otros archivos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TEST_DATA, getTestData };
}
