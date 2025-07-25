# Procesamiento en tiempo real para datos de vehículos

# Lambda function para procesamiento de telemetría en tiempo real
resource "aws_lambda_function" "telemetry_processor" {
  filename         = "telemetry_processor.zip"
  function_name    = "${var.project_name}-${var.environment}-telemetry-processor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 60
  memory_size     = 256

  environment {
    variables = {
      ENVIRONMENT = var.environment
      PROJECT_NAME = var.project_name
    }
  }

  depends_on = [data.archive_file.telemetry_processor_zip]
}

# Crear el archivo ZIP para la función Lambda
data "archive_file" "telemetry_processor_zip" {
  type        = "zip"
  output_path = "telemetry_processor.zip"
  source {
    content = <<EOF
import json
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Procesa eventos de telemetría de vehículos en tiempo real
    """
    try:
        for record in event['Records']:
            # Decodificar datos de Kinesis
            payload = json.loads(record['kinesis']['data'])
            
            # Procesar telemetría
            process_telemetry(payload)
            
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed telemetry data')
        }
    except Exception as e:
        logger.error(f"Error processing telemetry: {str(e)}")
        raise

def process_telemetry(data):
    """
    Procesa datos de telemetría individual
    """
    vehicle_id = data.get('vehicle_id')
    speed = data.get('speed', 0)
    fuel_level = data.get('fuel_level', 0)
    engine_temp = data.get('engine_temp', 0)
    
    # Detectar anomalías
    alerts = []
    if speed > 120:
        alerts.append('SPEEDING')
    if fuel_level < 10:
        alerts.append('LOW_FUEL')
    if engine_temp > 100:
        alerts.append('OVERHEATING')
    
    # Enviar alertas si es necesario
    if alerts:
        send_alerts(vehicle_id, alerts, data)
    
    logger.info(f"Processed telemetry for vehicle {vehicle_id}")

def send_alerts(vehicle_id, alerts, data):
    """
    Envía alertas a SNS
    """
    sns = boto3.client('sns')
    
    for alert in alerts:
        message = {
            'vehicle_id': vehicle_id,
            'alert_type': alert,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        # Aquí se enviaría a SNS topic específico
        logger.info(f"Alert {alert} for vehicle {vehicle_id}")
EOF
    filename = "index.py"
  }
}

# IAM role para Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy para Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-${var.environment}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "kinesis:DescribeStream",
          "kinesis:GetShardIterator",
          "kinesis:GetRecords",
          "kinesis:ListStreams"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Dashboard para monitoreo
resource "aws_cloudwatch_dashboard" "vehicle_monitoring" {
  dashboard_name = "${var.project_name}-${var.environment}-monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.telemetry_processor.function_name],
            [".", "Errors", ".", "."],
            [".", "Invocations", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Performance"
          period  = 300
        }
      }
    ]
  })
}

# Variables
variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, test, prod)"
  type        = string
}

variable "vpc_id" {
  description = "ID de la VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs de las subnets privadas"
  type        = list(string)
}

variable "iot_topic_arn" {
  description = "ARN del topic IoT"
  type        = string
}

variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

# Outputs
output "lambda_function_arn" {
  description = "ARN de la función Lambda de procesamiento"
  value       = aws_lambda_function.telemetry_processor.arn
}

output "dashboard_url" {
  description = "URL del dashboard de CloudWatch"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.vehicle_monitoring.dashboard_name}"
}
