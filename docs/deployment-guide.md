# Deployment Guide

## Prerequisites

### Required Tools
- **Terraform** >= 1.0
- **AWS CLI** >= 2.0
- **Git** >= 2.0

### AWS Account Setup
1. **AWS Account** with appropriate permissions
2. **IAM User** with programmatic access
3. **Required AWS Services** enabled in target region

### Required AWS Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:*",
                "lambda:*",
                "apigateway:*",
                "cognito-idp:*",
                "cognito-identity:*",
                "s3:*",
                "cloudfront:*",
                "iot:*",
                "kinesis:*",
                "sns:*",
                "cloudwatch:*",
                "iam:*",
                "ec2:*"
            ],
            "Resource": "*"
        }
    ]
}
```

## Step-by-Step Deployment

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-org/vehicle-tracking-infrastructure
cd vehicle-tracking-infrastructure

# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

### 2. Configure Variables

```bash
# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit configuration file
nano terraform.tfvars
```

**Example terraform.tfvars:**
```hcl
# Environment Configuration
environment = "production"
region = "us-east-1"

# Fleet Configuration
vehicle_count = 100
max_vehicles_per_fleet = 500

# Networking
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# Domain Configuration (optional)
domain_name = "your-domain.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"

# Monitoring
enable_detailed_monitoring = true
log_retention_days = 30

# Cost Optimization
enable_reserved_capacity = false
```

### 3. Initialize Terraform

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format code (optional)
terraform fmt -recursive
```

### 4. Plan Deployment

```bash
# Create execution plan
terraform plan -out=tfplan

# Review the plan carefully
# Ensure all resources are as expected
```

### 5. Deploy Infrastructure

```bash
# Apply the configuration
terraform apply tfplan

# Or apply directly (will prompt for confirmation)
terraform apply
```

**Expected deployment time**: 10-15 minutes

### 6. Verify Deployment

```bash
# Get deployment outputs
terraform output

# Test API endpoint
curl $(terraform output -raw api_base_url)/health

# Access web interface
open $(terraform output -raw web_interface_url)
```

## Environment-Specific Deployments

### Development Environment

```bash
# Use development configuration
cp terraform.tfvars.dev terraform.tfvars

# Deploy with smaller resources
terraform apply -var="vehicle_count=10" -var="environment=dev"
```

### Test Environment (70 Vehicles)

```bash
# Use test configuration
cp terraform.tfvars.test terraform.tfvars

# Deploy test environment
terraform apply
```

### Production Environment

```bash
# Use production configuration
cp terraform.tfvars.prod terraform.tfvars

# Deploy with additional safeguards
terraform plan -out=prod.tfplan
terraform apply prod.tfplan
```

## Post-Deployment Configuration

### 1. Create Initial Users

```bash
# Create admin user
aws cognito-idp admin-create-user \
  --user-pool-id $(terraform output -raw cognito_user_pool_id) \
  --username admin \
  --user-attributes Name=email,Value=admin@yourcompany.com \
  --temporary-password TempPassword123! \
  --message-action SUPPRESS
```

### 2. Configure DNS (if using custom domain)

```bash
# Get CloudFront distribution domain
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain_name)

# Create CNAME record in your DNS provider
# CNAME: your-domain.com -> $CLOUDFRONT_DOMAIN
```

### 3. Set up Monitoring Alerts

```bash
# Create CloudWatch alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "High-API-Error-Rate" \
  --alarm-description "Alert when API error rate is high" \
  --metric-name 4XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Troubleshooting

### Common Issues

#### 1. Terraform State Lock
```bash
# If deployment fails due to state lock
terraform force-unlock <LOCK_ID>
```

#### 2. AWS Permissions Error
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
  --action-names dynamodb:CreateTable \
  --resource-arns "*"
```

#### 3. Resource Limits
```bash
# Check AWS service limits
aws service-quotas get-service-quota \
  --service-code lambda \
  --quota-code L-B99A9384
```

#### 4. Lambda Deployment Package Too Large
```bash
# Check Lambda package sizes
ls -lh *.zip

# If packages are too large, optimize or use S3 deployment
```

### Debugging Commands

```bash
# Check Terraform state
terraform state list
terraform state show <resource_name>

# View detailed logs
terraform apply -auto-approve -var="log_level=DEBUG"

# Check AWS resources
aws dynamodb list-tables
aws lambda list-functions
aws apigateway get-rest-apis
```

## Rollback Procedures

### 1. Terraform Rollback
```bash
# Rollback to previous state
terraform apply -target=<specific_resource> -var="previous_value"

# Or destroy and recreate
terraform destroy -target=<problematic_resource>
terraform apply -target=<problematic_resource>
```

### 2. Complete Environment Rollback
```bash
# Destroy entire environment
terraform destroy

# Restore from backup state
cp terraform.tfstate.backup terraform.tfstate
terraform apply
```

## Maintenance

### Regular Tasks

#### 1. Update Dependencies
```bash
# Update Terraform providers
terraform init -upgrade

# Update Lambda dependencies
cd lambda_functions
pip install -r requirements.txt --upgrade
```

#### 2. Cost Optimization Review
```bash
# Generate cost report
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

#### 3. Security Updates
```bash
# Update IAM policies
terraform plan -target=module.auth
terraform apply -target=module.auth

# Rotate secrets
aws secretsmanager update-secret \
  --secret-id vehicle-tracking-api-key \
  --secret-string "new-secret-value"
```

### Backup Procedures

#### 1. Terraform State Backup
```bash
# Backup state file
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d)

# Store in S3
aws s3 cp terraform.tfstate s3://your-backup-bucket/terraform-state/
```

#### 2. Database Backup
```bash
# DynamoDB backup (automatic with point-in-time recovery)
aws dynamodb put-backup-policy \
  --table-name vehicle-tracking-vehicles \
  --backup-policy BackupEnabled=true
```

## Performance Tuning

### 1. Lambda Optimization
```bash
# Monitor Lambda performance
aws logs filter-log-events \
  --log-group-name /aws/lambda/vehicle-tracking-api \
  --filter-pattern "REPORT"
```

### 2. DynamoDB Optimization
```bash
# Monitor DynamoDB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=vehicle-tracking-vehicles \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

## Support

For deployment issues:
1. Check this guide first
2. Review Terraform logs
3. Check AWS CloudWatch logs
4. Create GitHub issue with detailed error information
5. Contact the CloudOps team for critical issues
