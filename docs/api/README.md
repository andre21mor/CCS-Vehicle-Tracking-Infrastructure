# API Documentation

## Base URL
```
https://qiaz9dfl08.execute-api.us-east-1.amazonaws.com/test-70v
```

## Authentication
All API endpoints require authentication using AWS Cognito JWT tokens.

### Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

## Endpoints

### Vehicle Management
- `GET /vehicles` - List all vehicles
- `GET /vehicles/{id}` - Get vehicle details
- `GET /vehicles/{id}/telemetry` - Get vehicle telemetry
- `GET /vehicles/{id}/location` - Get current location
- `GET /vehicles/{id}/alerts` - Get vehicle alerts

### Fleet Dashboard
- `GET /fleet/dashboard` - Get fleet overview

### Sales Module
- `GET /sales/clients` - List clients
- `POST /sales/clients` - Create new client
- `GET /sales/inventory` - List inventory
- `GET /sales/contracts` - List contracts
- `GET /sales/dashboard` - Sales dashboard

### Notifications
- `POST /notifications` - Send notification

### Reports
- `GET /reports` - Generate reports

## Response Format
All responses follow this format:
```json
{
  "statusCode": 200,
  "body": {
    "data": {},
    "message": "Success"
  }
}
```

## Error Handling
```json
{
  "statusCode": 400,
  "body": {
    "error": "Error message",
    "details": "Detailed error information"
  }
}
```
