output "vpc_id" {
  description = "ID de la VPC principal"
  value       = module.networking_test.vpc_id
}

output "iot_policy_arn" {
  description = "ARN de la política IoT para vehículos"
  value       = module.iot_core_test.iot_policy_arn
}

output "kinesis_stream_name" {
  description = "Nombre del stream de Kinesis para telemetría"
  value       = module.iot_core_test.kinesis_stream_name
}

output "panic_alerts_topic_arn" {
  description = "ARN del topic SNS para alertas de pánico"
  value       = module.iot_core_test.panic_sns_topic_arn
}

output "video_storage_bucket" {
  description = "Bucket S3 para almacenamiento de video"
  value       = module.iot_core_test.video_storage_bucket
}

output "vehicle_status_table" {
  description = "Tabla DynamoDB para estado de vehículos"
  value       = module.iot_core_test.vehicle_status_table_name
}

output "dashboard_url" {
  description = "URL del dashboard de monitoreo"
  value       = module.real_time_processing_test.dashboard_url
}

output "iot_endpoint" {
  description = "Endpoint de AWS IoT Core"
  value       = "https://iot.${var.aws_region}.amazonaws.com"
}

output "device_connection_info" {
  description = "Información para conectar dispositivos IoT"
  value = {
    iot_endpoint = "iot.${var.aws_region}.amazonaws.com"
    topics = {
      telemetry   = "vehicles/{vehicle_id}/telemetry"
      video       = "vehicles/{vehicle_id}/video"
      panic       = "vehicles/{vehicle_id}/panic"
      diagnostics = "vehicles/{vehicle_id}/diagnostics"
      commands    = "vehicles/{vehicle_id}/commands"
    }
    policy_arn = module.iot_core_test.iot_policy_arn
  }
}
