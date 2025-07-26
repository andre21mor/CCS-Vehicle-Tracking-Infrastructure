# CloudFront Distribution para la Interfaz Web
# Vehicle Tracking System

# S3 Bucket para alojar la interfaz web
resource "aws_s3_bucket" "web_interface" {
  bucket = "${var.project_name}-${var.environment}-web-interface-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-web-interface"
    Environment = var.environment
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Configuración de versionado
resource "aws_s3_bucket_versioning" "web_interface_versioning" {
  bucket = aws_s3_bucket.web_interface.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Configuración de encriptación
resource "aws_s3_bucket_server_side_encryption_configuration" "web_interface_encryption" {
  bucket = aws_s3_bucket.web_interface.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bloquear acceso público directo al bucket
resource "aws_s3_bucket_public_access_block" "web_interface_pab" {
  bucket = aws_s3_bucket.web_interface.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Origin Access Control para CloudFront
resource "aws_cloudfront_origin_access_control" "web_interface_oac" {
  name                              = "${var.project_name}-${var.environment}-web-oac"
  description                       = "OAC for Vehicle Tracking Web Interface"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Política del bucket S3 para permitir acceso desde CloudFront
resource "aws_s3_bucket_policy" "web_interface_policy" {
  bucket = aws_s3_bucket.web_interface.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.web_interface.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.web_interface.arn
          }
        }
      }
    ]
  })
}

# Distribución CloudFront
resource "aws_cloudfront_distribution" "web_interface" {
  origin {
    domain_name              = aws_s3_bucket.web_interface.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.web_interface_oac.id
    origin_id                = "S3-${aws_s3_bucket.web_interface.bucket}"
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Vehicle Tracking Web Interface Distribution"
  default_root_object = "index.html"
  
  # Integración con WAF (si está configurado)
  web_acl_id = var.waf_web_acl_id != "" ? var.waf_web_acl_id : null

  # Configuración de caché para archivos estáticos
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.web_interface.bucket}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400

    # Compresión automática
    compress = true
  }

  # Configuración específica para archivos JavaScript y CSS
  ordered_cache_behavior {
    path_pattern     = "*.js"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.web_interface.bucket}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }

  ordered_cache_behavior {
    path_pattern     = "*.css"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.web_interface.bucket}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }

  # Configuración para manejar errores de SPA
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  # Restricciones geográficas (opcional)
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Configuración del certificado SSL
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  # Configuración de logs (opcional)
  logging_config {
    include_cookies = false
    bucket          = aws_s3_bucket.cloudfront_logs.bucket_domain_name
    prefix          = "web-interface-logs/"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-web-distribution"
    Environment = var.environment
  }
}

# Bucket para logs de CloudFront
resource "aws_s3_bucket" "cloudfront_logs" {
  bucket = "${var.project_name}-${var.environment}-cloudfront-logs-${random_string.logs_suffix.result}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-cloudfront-logs"
    Environment = var.environment
  }
}

resource "random_string" "logs_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Enable ACL for CloudFront logs bucket
resource "aws_s3_bucket_ownership_controls" "cloudfront_logs_ownership" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# ACL configuration for CloudFront logs bucket
resource "aws_s3_bucket_acl" "cloudfront_logs_acl" {
  depends_on = [aws_s3_bucket_ownership_controls.cloudfront_logs_ownership]
  bucket     = aws_s3_bucket.cloudfront_logs.id
  acl        = "private"
}

# Configuración de lifecycle para logs
resource "aws_s3_bucket_lifecycle_configuration" "cloudfront_logs_lifecycle" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  rule {
    id     = "logs_lifecycle"
    status = "Enabled"

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    filter {
      prefix = ""
    }
  }
}

# Subir archivos de la interfaz web al S3
resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.web_interface.bucket
  key          = "index.html"
  source       = "${path.root}/web-interface/index.html"
  content_type = "text/html"
  etag         = filemd5("${path.root}/web-interface/index.html")

  tags = {
    Name        = "index.html"
    Environment = var.environment
  }
}

resource "aws_s3_object" "config_js" {
  bucket       = aws_s3_bucket.web_interface.bucket
  key          = "config.js"
  source       = "${path.root}/web-interface/config.js"
  content_type = "application/javascript"
  etag         = filemd5("${path.root}/web-interface/config.js")

  tags = {
    Name        = "config.js"
    Environment = var.environment
  }
}

resource "aws_s3_object" "test_data_js" {
  bucket       = aws_s3_bucket.web_interface.bucket
  key          = "test-data.js"
  source       = "${path.root}/web-interface/test-data.js"
  content_type = "application/javascript"
  etag         = filemd5("${path.root}/web-interface/test-data.js")

  tags = {
    Name        = "test-data.js"
    Environment = var.environment
  }
}

# Invalidación de caché cuando se actualicen los archivos
# Nota: aws_cloudfront_invalidation no existe, usamos null_resource con AWS CLI
resource "null_resource" "web_interface_invalidation" {
  triggers = {
    index_html_hash = filemd5("${path.root}/web-interface/index.html")
    config_js_hash  = filemd5("${path.root}/web-interface/config.js")
    test_data_js_hash = filemd5("${path.root}/web-interface/test-data.js")
  }

  provisioner "local-exec" {
    command = "aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.web_interface.id} --paths '/*' --region us-east-1"
  }

  depends_on = [
    aws_s3_object.index_html,
    aws_s3_object.config_js,
    aws_s3_object.test_data_js,
    aws_cloudfront_distribution.web_interface
  ]
}
