# 
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda function handler for a simple API Gateway integration
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get method and path from event
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    
    # Simple routing
    if path == '/' and http_method == 'GET':
        return handle_health_check()
    elif path == '/hello' and http_method == 'GET':
        return handle_hello(event)
    elif path == '/hello' and http_method == 'POST':
        return handle_create_hello(event)
    else:
        return handle_not_found()

def handle_health_check():
    """Health check endpoint"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Lambda function is healthy',
            'status': 'OK'
        })
    }

def handle_hello(event):
    """GET /hello endpoint"""
    query_params = event.get('queryStringParameters') or {}
    name = query_params.get('name', 'World')
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': f'Hello, {name}!',
            'timestamp': context_timestamp()
        })
    }

def handle_create_hello(event):
    """POST /hello endpoint"""
    try:
        body = json.loads(event.get('body', '{}'))
        name = body.get('name', 'Anonymous')
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Hello created for {name}!',
                'data': body,
                'timestamp': context_timestamp()
            })
        }
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid JSON in request body'
            })
        }

def handle_not_found():
    """404 handler"""
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        })
    }

def context_timestamp():
    """Get current timestamp"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')