output "iot_policy_arn" {
  description = "ARN de la política IoT para vehículos"
  value       = aws_iot_policy.vehicle_policy.arn
}

output "iot_topic_arn" {
  description = "ARN base para topics IoT"
  value       = "arn:aws:iot:${data.aws_region.current.name}:${var.account_id}:topic"
}

output "kinesis_stream_name" {
  description = "Nombre del stream de Kinesis para telemetría"
  value       = aws_kinesis_stream.vehicle_telemetry_stream.name
}

output "kinesis_stream_arn" {
  description = "ARN del stream de Kinesis para telemetría"
  value       = aws_kinesis_stream.vehicle_telemetry_stream.arn
}

output "panic_sns_topic_arn" {
  description = "ARN del topic SNS para alertas de pánico"
  value       = aws_sns_topic.panic_alerts.arn
}

output "video_storage_bucket" {
  description = "Nombre del bucket S3 para almacenamiento de video"
  value       = aws_s3_bucket.video_storage.bucket
}

output "vehicle_status_table_name" {
  description = "Nombre de la tabla DynamoDB para estado de vehículos"
  value       = aws_dynamodb_table.vehicle_status.name
}

output "panic_events_table_name" {
  description = "Nombre de la tabla DynamoDB para eventos de pánico"
  value       = aws_dynamodb_table.panic_events.name
}
