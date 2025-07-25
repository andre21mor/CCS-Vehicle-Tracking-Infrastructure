# IAM Role para funciones Lambda de ventas
resource "aws_iam_role" "sales_lambda_role" {
  name = "${var.project_name}-${var.environment}-sales-lambda-role"

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

  tags = {
    Name        = "${var.project_name}-${var.environment}-sales-lambda-role"
    Environment = var.environment
  }
}

# Policy para funciones Lambda de ventas
resource "aws_iam_role_policy" "sales_lambda_policy" {
  name = "${var.project_name}-${var.environment}-sales-lambda-policy"
  role = aws_iam_role.sales_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.sales_clients.arn,
          "${aws_dynamodb_table.sales_clients.arn}/*",
          aws_dynamodb_table.sales_inventory.arn,
          "${aws_dynamodb_table.sales_inventory.arn}/*",
          aws_dynamodb_table.sales_contracts.arn,
          "${aws_dynamodb_table.sales_contracts.arn}/*",
          aws_dynamodb_table.sales_quotations.arn,
          "${aws_dynamodb_table.sales_quotations.arn}/*"
        ]
      },
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
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach basic execution role
resource "aws_iam_role_policy_attachment" "sales_lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.sales_lambda_role.name
}

# Attach VPC access role
resource "aws_iam_role_policy_attachment" "sales_lambda_vpc" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.sales_lambda_role.name
}
