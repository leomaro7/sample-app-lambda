import json
import pytest
from src.lambda_function import lambda_handler, handle_health_check, handle_hello, handle_create_hello, handle_not_found


class TestLambdaFunction:
    """Test cases for Lambda function"""

    def test_health_check_endpoint(self):
        """Test GET / endpoint"""
        event = {
            'httpMethod': 'GET',
            'path': '/',
            'queryStringParameters': None
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Lambda function is healthy'
        assert body['status'] == 'OK'

    def test_hello_get_without_name(self):
        """Test GET /hello without name parameter"""
        event = {
            'httpMethod': 'GET',
            'path': '/hello',
            'queryStringParameters': None
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Hello, World!'
        assert 'timestamp' in body

    def test_hello_get_with_name(self):
        """Test GET /hello with name parameter"""
        event = {
            'httpMethod': 'GET',
            'path': '/hello',
            'queryStringParameters': {'name': 'Alice'}
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Hello, Alice!'
        assert 'timestamp' in body

    def test_hello_post_valid_json(self):
        """Test POST /hello with valid JSON"""
        event = {
            'httpMethod': 'POST',
            'path': '/hello',
            'body': json.dumps({'name': 'Bob'}),
            'queryStringParameters': None
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['message'] == 'Hello created for Bob!'
        assert body['data']['name'] == 'Bob'
        assert 'timestamp' in body

    def test_hello_post_invalid_json(self):
        """Test POST /hello with invalid JSON"""
        event = {
            'httpMethod': 'POST',
            'path': '/hello',
            'body': 'invalid json',
            'queryStringParameters': None
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Invalid JSON in request body'

    def test_hello_post_without_name(self):
        """Test POST /hello without name in body"""
        event = {
            'httpMethod': 'POST',
            'path': '/hello',
            'body': json.dumps({}),
            'queryStringParameters': None
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['message'] == 'Hello created for Anonymous!'

    def test_not_found(self):
        """Test 404 for unknown endpoints"""
        event = {
            'httpMethod': 'GET',
            'path': '/unknown',
            'queryStringParameters': None
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'Not Found'
        assert 'not found' in body['message'].lower()

    def test_cors_headers(self):
        """Test CORS headers are present in all responses"""
        event = {
            'httpMethod': 'GET',
            'path': '/',
            'queryStringParameters': None
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert response['headers']['Content-Type'] == 'application/json'


class TestHelperFunctions:
    """Test helper functions directly"""

    def test_handle_health_check(self):
        """Test health check function directly"""
        response = handle_health_check()
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'OK'

    def test_handle_not_found(self):
        """Test not found handler directly"""
        response = handle_not_found()
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'Not Found'