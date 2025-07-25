# Sistema de Autenticación con Amazon Cognito

# Cognito User Pool para clientes
resource "aws_cognito_user_pool" "client_pool" {
  name = "${var.project_name}-${var.environment}-client-pool"

  # Configuración de políticas de contraseña
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  # Configuración de MFA
  mfa_configuration = "OPTIONAL"
  
  software_token_mfa_configuration {
    enabled = true
  }

  # Atributos requeridos y opcionales
  schema {
    attribute_data_type = "String"
    name               = "email"
    required           = true
    mutable           = true
  }

  schema {
    attribute_data_type = "String"
    name               = "phone_number"
    required           = false
    mutable           = true
  }

  schema {
    attribute_data_type = "String"
    name               = "company_name"
    required           = false
    mutable           = true
  }

  schema {
    attribute_data_type = "String"
    name               = "fleet_size"
    required           = false
    mutable           = true
  }

  # Evitar recreación por cambios en schema
  lifecycle {
    ignore_changes = [schema]
  }

  # Configuración de verificación
  auto_verified_attributes = ["email"]
  
  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "Código de verificación - Plataforma Vehicular"
    email_message        = "Tu código de verificación es {####}"
  }

  # Configuración de recuperación de cuenta
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Configuración de dispositivos
  device_configuration {
    challenge_required_on_new_device      = true
    device_only_remembered_on_user_prompt = false
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-client-pool"
    Environment = var.environment
  }
}

# Cognito User Pool para conductores/operadores
resource "aws_cognito_user_pool" "driver_pool" {
  name = "${var.project_name}-${var.environment}-driver-pool"

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = true
  }

  mfa_configuration = "OPTIONAL"
  
  software_token_mfa_configuration {
    enabled = true
  }

  schema {
    attribute_data_type = "String"
    name               = "email"
    required           = true
    mutable           = true
  }

  schema {
    attribute_data_type = "String"
    name               = "phone_number"
    required           = true
    mutable           = true
  }

  schema {
    attribute_data_type = "String"
    name               = "license_number"
    required           = false
    mutable           = true
  }

  schema {
    attribute_data_type = "String"
    name               = "employee_id"
    required           = false
    mutable           = true
  }

  auto_verified_attributes = ["email"]

  # Evitar recreación por cambios en schema
  lifecycle {
    ignore_changes = [schema]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-driver-pool"
    Environment = var.environment
  }
}

# User Pool Client para aplicación web
resource "aws_cognito_user_pool_client" "web_client" {
  name         = "${var.project_name}-${var.environment}-web-client"
  user_pool_id = aws_cognito_user_pool.client_pool.id

  generate_secret                      = false
  prevent_user_existence_errors        = "ENABLED"
  enable_token_revocation             = true
  enable_propagate_additional_user_context_data = false

  # Flujos de autenticación permitidos
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]

  # Configuración de tokens
  access_token_validity  = 1    # 1 hora
  id_token_validity     = 1    # 1 hora
  refresh_token_validity = 30   # 30 días

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  # URLs de callback para OAuth
  callback_urls = [
    "https://${var.project_name}-${var.environment}.com/callback",
    "http://localhost:3000/callback"  # Para desarrollo
  ]

  logout_urls = [
    "https://${var.project_name}-${var.environment}.com/logout",
    "http://localhost:3000/logout"
  ]

  # Scopes OAuth
  allowed_oauth_flows = ["code", "implicit"]
  allowed_oauth_scopes = ["email", "openid", "profile"]
  allowed_oauth_flows_user_pool_client = true

  # Atributos de lectura y escritura
  read_attributes = [
    "email",
    "email_verified",
    "phone_number",
    "phone_number_verified",
    "custom:company_name",
    "custom:fleet_size"
  ]

  write_attributes = [
    "email",
    "phone_number",
    "custom:company_name",
    "custom:fleet_size"
  ]
}

# User Pool Client para aplicación móvil
resource "aws_cognito_user_pool_client" "mobile_client" {
  name         = "${var.project_name}-${var.environment}-mobile-client"
  user_pool_id = aws_cognito_user_pool.client_pool.id

  generate_secret                      = false
  prevent_user_existence_errors        = "ENABLED"
  enable_token_revocation             = true

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  access_token_validity  = 1
  id_token_validity     = 1
  refresh_token_validity = 30

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  # URLs para deep linking móvil
  callback_urls = [
    "vehicletracking://callback",
    "com.vehicletracking.app://callback"
  ]

  logout_urls = [
    "vehicletracking://logout",
    "com.vehicletracking.app://logout"
  ]

  allowed_oauth_flows = ["code"]
  allowed_oauth_scopes = ["email", "openid", "profile"]
  allowed_oauth_flows_user_pool_client = true

  read_attributes = [
    "email",
    "email_verified",
    "phone_number",
    "phone_number_verified",
    "custom:company_name"
  ]

  write_attributes = [
    "email",
    "phone_number",
    "custom:company_name"
  ]
}

# User Pool Client para conductores
resource "aws_cognito_user_pool_client" "driver_client" {
  name         = "${var.project_name}-${var.environment}-driver-client"
  user_pool_id = aws_cognito_user_pool.driver_pool.id

  generate_secret                      = false
  prevent_user_existence_errors        = "ENABLED"
  enable_token_revocation             = true

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  access_token_validity  = 8    # 8 horas para turnos largos
  id_token_validity     = 8
  refresh_token_validity = 7    # 7 días

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  callback_urls = [
    "vehicletracking-driver://callback"
  ]

  logout_urls = [
    "vehicletracking-driver://logout"
  ]

  read_attributes = [
    "email",
    "phone_number"
  ]
}

# Identity Pool para acceso a recursos AWS
resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = "${var.project_name}-${var.environment}-identity-pool"
  allow_unauthenticated_identities = false

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.web_client.id
    provider_name           = aws_cognito_user_pool.client_pool.endpoint
    server_side_token_check = false
  }

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.mobile_client.id
    provider_name           = aws_cognito_user_pool.client_pool.endpoint
    server_side_token_check = false
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-identity-pool"
    Environment = var.environment
  }
}

# Roles IAM para usuarios autenticados
resource "aws_iam_role" "authenticated_role" {
  name = "${var.project_name}-${var.environment}-cognito-authenticated-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.main.id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "authenticated"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-cognito-authenticated-role"
    Environment = var.environment
  }
}

# Política para usuarios autenticados
resource "aws_iam_role_policy" "authenticated_policy" {
  name = "${var.project_name}-${var.environment}-cognito-authenticated-policy"
  role = aws_iam_role.authenticated_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::${var.project_name}-${var.environment}-*/*"
        Condition = {
          StringLike = {
            "s3:prefix" = "$${cognito-identity.amazonaws.com:sub}/*"
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = "arn:aws:dynamodb:${data.aws_region.current.name}:*:table/${var.project_name}-${var.environment}-*"
        Condition = {
          "ForAllValues:StringEquals" = {
            "dynamodb:LeadingKeys" = ["$${cognito-identity.amazonaws.com:sub}"]
          }
        }
      }
    ]
  })
}

# Attachment del Identity Pool
resource "aws_cognito_identity_pool_roles_attachment" "main" {
  identity_pool_id = aws_cognito_identity_pool.main.id

  roles = {
    "authenticated" = aws_iam_role.authenticated_role.arn
  }
}

# Dominio personalizado para Cognito (opcional)
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.project_name}-${var.environment}-auth"
  user_pool_id = aws_cognito_user_pool.client_pool.id
}

# Data sources
data "aws_region" "current" {}
