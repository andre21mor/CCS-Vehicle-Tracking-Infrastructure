# Outputs del módulo CloudFront

output "cloudfront_distribution_id" {
  description = "ID de la distribución CloudFront"
  value       = aws_cloudfront_distribution.web_interface.id
}

output "cloudfront_distribution_arn" {
  description = "ARN de la distribución CloudFront"
  value       = aws_cloudfront_distribution.web_interface.arn
}

output "cloudfront_domain_name" {
  description = "Nombre de dominio de CloudFront"
  value       = aws_cloudfront_distribution.web_interface.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "Hosted Zone ID de CloudFront"
  value       = aws_cloudfront_distribution.web_interface.hosted_zone_id
}

output "web_interface_url" {
  description = "URL completa de la interfaz web"
  value       = "https://${aws_cloudfront_distribution.web_interface.domain_name}"
}

output "s3_bucket_name" {
  description = "Nombre del bucket S3 para la interfaz web"
  value       = aws_s3_bucket.web_interface.bucket
}

output "s3_bucket_arn" {
  description = "ARN del bucket S3 para la interfaz web"
  value       = aws_s3_bucket.web_interface.arn
}

output "s3_bucket_domain_name" {
  description = "Nombre de dominio del bucket S3"
  value       = aws_s3_bucket.web_interface.bucket_domain_name
}

output "cloudfront_logs_bucket" {
  description = "Bucket para logs de CloudFront"
  value       = aws_s3_bucket.cloudfront_logs.bucket
}

output "origin_access_control_id" {
  description = "ID del Origin Access Control"
  value       = aws_cloudfront_origin_access_control.web_interface_oac.id
}
