# AWS WAF v2 para Vehicle Tracking System
# Protección de CloudFront Distribution

# WAF Web ACL para CloudFront
resource "aws_wafv2_web_acl" "vehicle_tracking_waf" {
  name  = "${var.project_name}-${var.environment}-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # Regla 1: Rate Limiting - Protección contra DDoS
  rule {
    name     = "RateLimitRule"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.rate_limit
        aggregate_key_type = "IP"
        
        scope_down_statement {
          geo_match_statement {
            # Permitir solo ciertos países (ajustar según necesidad)
            country_codes = var.allowed_countries
          }
        }
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
    }
  }

  # Regla 2: AWS Managed Rules - Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"

        # Excluir reglas específicas si es necesario
        dynamic "rule_action_override" {
          for_each = var.common_rule_exclusions
          content {
            action_to_use {
              allow {}
            }
            name = rule_action_override.value
          }
        }
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
    }
  }

  # Regla 3: Known Bad Inputs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSet"
    }
  }

  # Regla 4: SQL Injection Protection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 4

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLiRuleSet"
    }
  }

  # Regla 5: Linux Operating System Protection
  rule {
    name     = "AWSManagedRulesLinuxRuleSet"
    priority = 5

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesLinuxRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesLinuxRuleSet"
    }
  }

  # Regla 6: IP Reputation List
  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 6

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesAmazonIpReputationList"
    }
  }

  # Regla 7: Bot Control (opcional, costo adicional)
  dynamic "rule" {
    for_each = var.enable_bot_control ? [1] : []
    content {
      name     = "AWSManagedRulesBotControlRuleSet"
      priority = 7

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          name        = "AWSManagedRulesBotControlRuleSet"
          vendor_name = "AWS"
        }
      }

      visibility_config {
        sampled_requests_enabled   = true
        cloudwatch_metrics_enabled = true
        metric_name                = "AWSManagedRulesBotControlRuleSet"
      }
    }
  }

  # Regla 8: Custom IP Whitelist (para IPs de oficina/administración)
  dynamic "rule" {
    for_each = length(var.ip_whitelist) > 0 ? [1] : []
    content {
      name     = "IPWhitelistRule"
      priority = 8

      action {
        allow {}
      }

      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.ip_whitelist[0].arn
        }
      }

      visibility_config {
        sampled_requests_enabled   = true
        cloudwatch_metrics_enabled = true
        metric_name                = "IPWhitelistRule"
      }
    }
  }

  # Regla 9: Custom IP Blacklist
  dynamic "rule" {
    for_each = length(var.ip_blacklist) > 0 ? [1] : []
    content {
      name     = "IPBlacklistRule"
      priority = 9

      action {
        block {}
      }

      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.ip_blacklist[0].arn
        }
      }

      visibility_config {
        sampled_requests_enabled   = true
        cloudwatch_metrics_enabled = true
        metric_name                = "IPBlacklistRule"
      }
    }
  }

  # Regla 10: Geographic Restrictions
  dynamic "rule" {
    for_each = var.enable_geo_blocking ? [1] : []
    content {
      name     = "GeoBlockingRule"
      priority = 10

      action {
        block {}
      }

      statement {
        not_statement {
          statement {
            geo_match_statement {
              country_codes = var.allowed_countries
            }
          }
        }
      }

      visibility_config {
        sampled_requests_enabled   = true
        cloudwatch_metrics_enabled = true
        metric_name                = "GeoBlockingRule"
      }
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-waf"
    Environment = var.environment
    Purpose     = "CloudFront Protection"
    Project     = var.project_name
  }

  visibility_config {
    sampled_requests_enabled   = true
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-waf"
  }
}

# IP Set para Whitelist (IPs permitidas)
resource "aws_wafv2_ip_set" "ip_whitelist" {
  count = length(var.ip_whitelist) > 0 ? 1 : 0

  name  = "${var.project_name}-${var.environment}-ip-whitelist"
  scope = "CLOUDFRONT"

  ip_address_version = "IPV4"
  addresses          = var.ip_whitelist

  tags = {
    Name        = "${var.project_name}-${var.environment}-ip-whitelist"
    Environment = var.environment
  }
}

# IP Set para Blacklist (IPs bloqueadas)
resource "aws_wafv2_ip_set" "ip_blacklist" {
  count = length(var.ip_blacklist) > 0 ? 1 : 0

  name  = "${var.project_name}-${var.environment}-ip-blacklist"
  scope = "CLOUDFRONT"

  ip_address_version = "IPV4"
  addresses          = var.ip_blacklist

  tags = {
    Name        = "${var.project_name}-${var.environment}-ip-blacklist"
    Environment = var.environment
  }
}

# CloudWatch Log Group para WAF
resource "aws_cloudwatch_log_group" "waf_log_group" {
  name              = "/aws/wafv2/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-waf-logs"
    Environment = var.environment
  }
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "waf_logging" {
  resource_arn            = aws_wafv2_web_acl.vehicle_tracking_waf.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf_log_group.arn]

  redacted_fields {
    single_header {
      name = "authorization"
    }
  }

  redacted_fields {
    single_header {
      name = "cookie"
    }
  }

  redacted_fields {
    single_header {
      name = "x-api-key"
    }
  }
}

# CloudWatch Alarms para WAF
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  alarm_name          = "${var.project_name}-${var.environment}-waf-blocked-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.blocked_requests_threshold
  alarm_description   = "This metric monitors blocked requests by WAF"
  alarm_actions       = var.alarm_actions

  dimensions = {
    WebACL = aws_wafv2_web_acl.vehicle_tracking_waf.name
    Rule   = "ALL"
    Region = "CloudFront"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-waf-blocked-alarm"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "waf_rate_limit_triggered" {
  alarm_name          = "${var.project_name}-${var.environment}-waf-rate-limit"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.rate_limit_threshold
  alarm_description   = "This metric monitors rate limiting triggers"
  alarm_actions       = var.alarm_actions

  dimensions = {
    WebACL = aws_wafv2_web_acl.vehicle_tracking_waf.name
    Rule   = "RateLimitRule"
    Region = "CloudFront"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-waf-rate-limit-alarm"
    Environment = var.environment
  }
}
