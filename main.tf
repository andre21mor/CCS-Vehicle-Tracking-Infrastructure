# Configuración específica para prueba de 70 vehículos
# Este archivo reemplaza main.tf para evitar conflictos

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project      = var.project_name
      Environment  = "test-70v"
      Purpose      = "Testing"
      VehicleCount = "70"
      TestDuration = "14days"
      CostCenter   = "RnD"
      Owner        = "TestTeam"
      AutoShutdown = "true"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Variables específicas para prueba
variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "vehicle-tracking"
}

variable "test_vehicle_count" {
  description = "Número de vehículos para la prueba"
  type        = number
  default     = 70
}

variable "test_duration_days" {
  description = "Duración de la prueba en días"
  type        = number
  default     = 14
}

# VPC y Networking (configuración mínima para pruebas)
module "networking_test" {
  source = "./modules/networking"
  
  project_name = var.project_name
  environment  = "test-70v"
  vpc_cidr     = "10.1.0.0/16"
  azs          = slice(data.aws_availability_zones.available.names, 0, 2)
}

# AWS IoT Core
module "iot_core_test" {
  source = "./modules/iot-core"
  
  project_name = var.project_name
  environment  = "test-70v"
  account_id   = data.aws_caller_identity.current.account_id
}

# Base de datos (configuración mínima)
module "database_test" {
  source = "./modules/database"
  
  project_name = var.project_name
  environment  = "test-70v"
  vpc_id       = module.networking_test.vpc_id
  private_subnet_ids = module.networking_test.private_subnet_ids
  database_subnet_group_name = module.networking_test.database_subnet_group_name
  enable_rds = false
}

# Autenticación
module "auth_test" {
  source = "./modules/auth"
  
  project_name = var.project_name
  environment  = "test-70v"
}

# Procesamiento en tiempo real (optimizado)
module "real_time_processing_test" {
  source = "./modules/real-time-processing"
  
  project_name = var.project_name
  environment  = "test-70v"
  vpc_id       = module.networking_test.vpc_id
  private_subnet_ids = module.networking_test.private_subnet_ids
  iot_topic_arn = module.iot_core_test.iot_topic_arn
}

# API Gateway
module "api_services_test" {
  source = "./modules/api-services"
  
  project_name = var.project_name
  environment  = "test-70v"
  vpc_id       = module.networking_test.vpc_id
  private_subnet_ids = module.networking_test.private_subnet_ids
  public_subnet_ids  = module.networking_test.public_subnet_ids
  user_pool_id = module.auth_test.client_user_pool_id
  
  depends_on = [module.auth_test, module.database_test]
}

# Módulo de Ventas
module "sales_test" {
  source = "./modules/sales"
  
  project_name = var.project_name
  environment  = "test-70v"
  vpc_id       = module.networking_test.vpc_id
  private_subnet_ids = module.networking_test.private_subnet_ids
  user_pool_id = module.auth_test.client_user_pool_id
  api_gateway_id = module.api_services_test.api_gateway_id
  api_gateway_root_resource_id = module.api_services_test.api_gateway_root_resource_id
  cognito_authorizer_id = module.api_services_test.cognito_authorizer_id
  
  depends_on = [module.api_services_test]
}

# Contract Approval (para módulo de ventas) - TEMPORALMENTE DESHABILITADO
# module "contract_approval_test" {
#   source = "./modules/contract-approval"
#   
#   project_name = var.project_name
#   environment  = "test-70v"
#   vpc_id       = module.networking_test.vpc_id
#   private_subnet_ids = module.networking_test.private_subnet_ids
#   user_pool_id = module.auth_test.client_user_pool_id
#   
#   depends_on = [module.auth_test, module.database_test]
# }

# CloudFront para Interfaz Web
module "cloudfront_test" {
  source = "./modules/cloudfront"
  
  project_name = var.project_name
  environment  = "test-70v"
  
  # Configuración de CloudFront
  enable_logging = true
  price_class    = "PriceClass_100"
  
  depends_on = [module.api_services_test]
}

# Outputs para la prueba
output "test_environment_info" {
  description = "Información del ambiente de prueba"
  value = {
    environment_name = "test-70v"
    vehicle_count = var.test_vehicle_count
    test_duration_days = var.test_duration_days
    estimated_daily_cost = 1.89
    estimated_total_cost = 1.89 * var.test_duration_days
    vpc_id = module.networking_test.vpc_id
    region = var.aws_region
  }
}

output "connection_info" {
  description = "Información de conexión para dispositivos de prueba"
  value = {
    iot_endpoint = "iot.${var.aws_region}.amazonaws.com"
    iot_policy_arn = module.iot_core_test.iot_policy_arn
    cognito_user_pool_id = module.auth_test.client_user_pool_id
    cognito_client_id = module.auth_test.web_client_id
    api_base_url = module.api_services_test.api_gateway_url
    kinesis_stream_name = module.iot_core_test.kinesis_stream_name
    panic_alerts_topic = module.iot_core_test.panic_sns_topic_arn
  }
}

output "monitoring_info" {
  description = "Información de monitoreo"
  value = {
    dashboard_url = module.real_time_processing_test.dashboard_url
    vehicle_status_table = module.iot_core_test.vehicle_status_table_name
    panic_events_table = module.iot_core_test.panic_events_table_name
    video_storage_bucket = module.iot_core_test.video_storage_bucket
  }
}

# Outputs de CloudFront
output "web_interface_info" {
  description = "Información de la interfaz web"
  value = {
    cloudfront_url = module.cloudfront_test.web_interface_url
    cloudfront_distribution_id = module.cloudfront_test.cloudfront_distribution_id
    s3_bucket_name = module.cloudfront_test.s3_bucket_name
    domain_name = module.cloudfront_test.cloudfront_domain_name
  }
}

output "web_interface_url" {
  description = "URL de la interfaz web en CloudFront"
  value = module.cloudfront_test.web_interface_url
}

# Outputs del módulo de ventas
output "sales_module_info" {
  description = "Información del módulo de ventas"
  value = {
    clients_table = module.sales_test.sales_clients_table_name
    inventory_table = module.sales_test.sales_inventory_table_name
    contracts_table = module.sales_test.sales_contracts_table_name
    quotations_table = module.sales_test.sales_quotations_table_name
    api_endpoints = module.sales_test.sales_api_endpoints
  }
}
