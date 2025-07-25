# Operations Runbook

## System Overview
This runbook provides operational procedures for the Vehicle Tracking Infrastructure.

## Emergency Contacts
- **On-call Engineer**: +1-XXX-XXX-XXXX
- **Architecture Team**: architecture@company.com
- **AWS Support**: Enterprise Support Case

## System Health Checks

### 1. API Health Check
```bash
curl https://qiaz9dfl08.execute-api.us-east-1.amazonaws.com/test-70v/health
```
Expected response: `200 OK`

### 2. Database Health
```bash
aws dynamodb describe-table --table-name vehicle-tracking-test-70v-vehicles
```

### 3. Lambda Functions
```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `vehicle-tracking`)].FunctionName'
```

## Common Issues and Solutions

### Issue: High API Latency
**Symptoms**: Response times > 1000ms
**Investigation**:
1. Check CloudWatch metrics for Lambda duration
2. Check DynamoDB throttling metrics
3. Check ElastiCache hit ratio

**Resolution**:
1. Scale up DynamoDB read/write capacity
2. Optimize Lambda memory allocation
3. Check cache configuration

### Issue: Lambda Function Errors
**Symptoms**: 5XX errors in API Gateway
**Investigation**:
1. Check CloudWatch logs: `/aws/lambda/function-name`
2. Check Lambda metrics for errors and duration
3. Check IAM permissions

**Resolution**:
1. Review and fix code issues
2. Update IAM policies if needed
3. Increase Lambda timeout if needed

### Issue: DynamoDB Throttling
**Symptoms**: `ProvisionedThroughputExceededException`
**Investigation**:
1. Check DynamoDB metrics in CloudWatch
2. Review access patterns
3. Check GSI utilization

**Resolution**:
1. Enable auto-scaling
2. Increase provisioned capacity temporarily
3. Optimize queries and access patterns

## Monitoring and Alerting

### Key Metrics to Monitor
- API Gateway 4XX/5XX error rates
- Lambda function duration and errors
- DynamoDB read/write capacity utilization
- ElastiCache CPU and memory utilization

### Alert Thresholds
- API error rate > 5%
- Lambda duration > 10 seconds
- DynamoDB throttling > 0
- ElastiCache CPU > 80%

## Backup and Recovery

### Database Backup
- DynamoDB: Point-in-time recovery enabled (35 days)
- ElastiCache: Daily snapshots

### Recovery Procedures
1. **DynamoDB Recovery**:
   ```bash
   aws dynamodb restore-table-to-point-in-time \
     --source-table-name original-table \
     --target-table-name restored-table \
     --restore-date-time 2025-01-01T00:00:00.000Z
   ```

2. **Lambda Recovery**:
   ```bash
   terraform apply -target=module.api_services.aws_lambda_function.function_name
   ```

## Scaling Procedures

### Horizontal Scaling
- Lambda: Automatic scaling (no action required)
- DynamoDB: Enable auto-scaling or increase capacity manually
- API Gateway: Automatic scaling (no action required)

### Vertical Scaling
- Lambda: Increase memory allocation
- ElastiCache: Scale up node type

## Security Incident Response

### 1. Suspected Breach
1. Immediately rotate all API keys and secrets
2. Review CloudTrail logs for suspicious activity
3. Check access patterns in CloudWatch
4. Contact security team

### 2. DDoS Attack
1. Enable AWS Shield Advanced if not already enabled
2. Implement rate limiting in API Gateway
3. Review CloudFront access logs
4. Contact AWS Support

## Maintenance Windows

### Scheduled Maintenance
- **Frequency**: Monthly
- **Duration**: 2 hours
- **Time**: Sunday 2:00 AM - 4:00 AM UTC

### Maintenance Checklist
- [ ] Update Lambda function dependencies
- [ ] Review and optimize DynamoDB indexes
- [ ] Clean up old CloudWatch logs
- [ ] Update Terraform modules
- [ ] Security patches and updates
- [ ] Cost optimization review

## Performance Tuning

### Lambda Optimization
1. Monitor memory usage and adjust allocation
2. Use provisioned concurrency for critical functions
3. Optimize cold start times

### Database Optimization
1. Review and optimize DynamoDB queries
2. Use appropriate indexes (GSI/LSI)
3. Monitor and adjust read/write capacity

### Caching Strategy
1. Implement appropriate TTL values
2. Monitor cache hit ratios
3. Use ElastiCache for frequently accessed data

## Cost Management

### Daily Cost Monitoring
```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '1 day ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost
```

### Cost Optimization Actions
1. Review unused resources monthly
2. Implement lifecycle policies for S3
3. Use reserved capacity for predictable workloads
4. Monitor and optimize Lambda memory allocation
