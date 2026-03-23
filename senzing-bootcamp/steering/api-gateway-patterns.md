---
inclusion: manual
---

# API Gateway Integration Patterns

## Overview

This guide covers patterns for integrating Senzing entity resolution into applications through API gateways, REST APIs, and service architectures.

## Why API Gateway?

An API gateway provides:

- **Single Entry Point**: Unified interface for all clients
- **Authentication/Authorization**: Centralized security
- **Rate Limiting**: Protect backend from overload
- **Caching**: Improve performance
- **Monitoring**: Track API usage
- **Versioning**: Manage API versions
- **Load Balancing**: Distribute requests

## Integration Patterns

### Pattern 1: Direct SDK Integration

**Description**: Application directly uses Senzing SDK

```
[Application] → [Senzing SDK] → [Database]
```

**Pros**:
- Lowest latency
- Simplest architecture
- No network overhead

**Cons**:
- Tight coupling
- SDK must be in same language
- Harder to scale horizontally

**Use when**:
- Single application
- Performance critical
- Simple deployment

**Example** (Python):
```python
from senzing import SzEngine

class CustomerService:
    def __init__(self):
        self.engine = SzEngine()
        self.engine.initialize(instance_name='app', settings=ENGINE_CONFIG)
    
    def find_customer(self, name, email):
        """Find customer by name and email"""
        search_attrs = {
            "NAME_FULL": name,
            "EMAIL_ADDRESS": email
        }
        results = self.engine.searchByAttributes(json.dumps(search_attrs))
        return json.loads(results)
```

### Pattern 2: REST API Wrapper

**Description**: Wrap Senzing SDK in REST API

```
[Client] → [REST API] → [Senzing SDK] → [Database]
```

**Pros**:
- Language agnostic
- Easy to consume
- Can add caching layer
- Horizontal scaling

**Cons**:
- Network latency
- Additional component to maintain

**Use when**:
- Multiple applications
- Different languages
- Microservices architecture

**Example** (Flask):
```python
from flask import Flask, request, jsonify
from senzing import SzEngine

app = Flask(__name__)
engine = SzEngine()
engine.initialize(instance_name='api', settings=ENGINE_CONFIG)

@app.route('/api/v1/search', methods=['POST'])
def search_entities():
    """Search for entities by attributes"""
    search_attrs = request.json
    
    try:
        results = engine.searchByAttributes(json.dumps(search_attrs))
        return jsonify(json.loads(results))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/entity/<int:entity_id>', methods=['GET'])
def get_entity(entity_id):
    """Get entity by ID"""
    try:
        entity = engine.getEntityByEntityID(entity_id)
        return jsonify(json.loads(entity))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### Pattern 3: API Gateway + Microservice

**Description**: API gateway routes to Senzing microservice

```
[Client] → [API Gateway] → [Senzing Service] → [Senzing SDK] → [Database]
```

**Pros**:
- Centralized security
- Rate limiting
- Monitoring
- Multiple backends
- Service mesh integration

**Cons**:
- More complex
- Additional latency
- More components

**Use when**:
- Enterprise architecture
- Multiple services
- Need centralized control
- Service mesh (Istio, Linkerd)

**Example** (Kong Gateway):
```yaml
# Kong service definition
services:
  - name: senzing-service
    url: http://senzing-api:8080
    routes:
      - name: senzing-search
        paths:
          - /senzing/search
        methods:
          - POST
      - name: senzing-entity
        paths:
          - /senzing/entity
        methods:
          - GET
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          hour: 1000
      - name: key-auth
      - name: cors
```

### Pattern 4: GraphQL Gateway

**Description**: GraphQL API for flexible queries

```
[Client] → [GraphQL Gateway] → [Senzing SDK] → [Database]
```

**Pros**:
- Flexible queries
- Single request for multiple operations
- Strong typing
- Client-driven queries

**Cons**:
- More complex
- Query complexity management needed

**Use when**:
- Complex data requirements
- Multiple related queries
- Modern frontend (React, Vue)

**Example** (GraphQL):
```python
import graphene
from senzing import SzEngine

class Entity(graphene.ObjectType):
    entity_id = graphene.Int()
    names = graphene.List(graphene.String)
    addresses = graphene.List(graphene.String)
    phones = graphene.List(graphene.String)

class Query(graphene.ObjectType):
    entity = graphene.Field(Entity, entity_id=graphene.Int(required=True))
    search = graphene.List(Entity, name=graphene.String(), email=graphene.String())
    
    def resolve_entity(self, info, entity_id):
        engine = SzEngine()
        engine.initialize(instance_name='graphql', settings=ENGINE_CONFIG)
        entity_json = engine.getEntityByEntityID(entity_id)
        entity_data = json.loads(entity_json)
        # Transform to GraphQL format
        return Entity(
            entity_id=entity_data['RESOLVED_ENTITY']['ENTITY_ID'],
            names=[n['NAME_FULL'] for n in entity_data['RESOLVED_ENTITY'].get('NAME', [])],
            addresses=[a['ADDR_FULL'] for a in entity_data['RESOLVED_ENTITY'].get('ADDRESS', [])],
            phones=[p['PHONE_NUMBER'] for p in entity_data['RESOLVED_ENTITY'].get('PHONE', [])]
        )

schema = graphene.Schema(query=Query)
```

### Pattern 5: Event-Driven Integration

**Description**: Async processing via message queue

```
[Client] → [API Gateway] → [Queue] → [Worker] → [Senzing SDK] → [Database]
                              ↓
                          [Response Queue]
```

**Pros**:
- Decoupled
- Handles load spikes
- Async processing
- Retry logic

**Cons**:
- More complex
- Eventual consistency
- Requires message queue

**Use when**:
- Batch processing
- High volume
- Async acceptable
- Need retry logic

**Example** (RabbitMQ):
```python
import pika
import json
from senzing import SzEngine

# Worker process
def process_entity_request(ch, method, properties, body):
    """Process entity resolution request from queue"""
    
    request = json.loads(body)
    
    engine = SzEngine()
    engine.initialize(instance_name='worker', settings=ENGINE_CONFIG)
    
    try:
        if request['operation'] == 'search':
            result = engine.searchByAttributes(json.dumps(request['attributes']))
        elif request['operation'] == 'get_entity':
            result = engine.getEntityByEntityID(request['entity_id'])
        
        # Send result to response queue
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            body=result
        )
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    except Exception as e:
        # Send error to response queue
        error_response = json.dumps({'error': str(e)})
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            body=error_response
        )
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    finally:
        engine.destroy()

# Start worker
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='senzing_requests')
channel.basic_consume(queue='senzing_requests', on_message_callback=process_entity_request)
channel.start_consuming()
```

## REST API Design

### Endpoint Structure

```
GET    /api/v1/entities/{entity_id}           # Get entity by ID
GET    /api/v1/entities/{entity_id}/records   # Get entity records
POST   /api/v1/search                         # Search entities
POST   /api/v1/records                        # Add record
DELETE /api/v1/records/{data_source}/{record_id}  # Delete record
GET    /api/v1/why/{entity_id_1}/{entity_id_2}    # Why entities matched
GET    /api/v1/how/{entity_id}                    # How entity was built
GET    /api/v1/health                         # Health check
GET    /api/v1/stats                          # Statistics
```

### Request/Response Examples

**Search Entities**:
```http
POST /api/v1/search
Content-Type: application/json

{
  "NAME_FULL": "John Smith",
  "EMAIL_ADDRESS": "john.smith@email.com"
}
```

Response:
```json
{
  "RESOLVED_ENTITIES": [
    {
      "MATCH_INFO": {
        "MATCH_SCORE": 95
      },
      "ENTITY": {
        "RESOLVED_ENTITY": {
          "ENTITY_ID": 12345,
          "ENTITY_NAME": "John Smith",
          "RECORD_SUMMARY": [
            {
              "DATA_SOURCE": "CUSTOMERS",
              "RECORD_COUNT": 2
            }
          ]
        }
      }
    }
  ]
}
```

**Get Entity**:
```http
GET /api/v1/entities/12345
```

Response:
```json
{
  "RESOLVED_ENTITY": {
    "ENTITY_ID": 12345,
    "NAME": [
      {"NAME_FULL": "John Smith"}
    ],
    "ADDRESS": [
      {"ADDR_FULL": "123 Main St, Boston, MA"}
    ],
    "PHONE": [
      {"PHONE_NUMBER": "617-555-1234"}
    ],
    "EMAIL": [
      {"EMAIL_ADDRESS": "john.smith@email.com"}
    ],
    "RECORDS": [
      {
        "DATA_SOURCE": "CUSTOMERS",
        "RECORD_ID": "C12345"
      },
      {
        "DATA_SOURCE": "ORDERS",
        "RECORD_ID": "O67890"
      }
    ]
  }
}
```

## Authentication and Authorization

### API Key Authentication

```python
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# API keys (in production, use database or secrets manager)
API_KEYS = {
    'key_abc123': {'client': 'web_app', 'permissions': ['read', 'search']},
    'key_xyz789': {'client': 'admin_app', 'permissions': ['read', 'write', 'delete']}
}

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key or api_key not in API_KEYS:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Add client info to request
        request.client_info = API_KEYS[api_key]
        
        return f(*args, **kwargs)
    return decorated_function

def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if permission not in request.client_info['permissions']:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/api/v1/search', methods=['POST'])
@require_api_key
@require_permission('search')
def search_entities():
    # Search logic here
    pass
```

### JWT Authentication

```python
import jwt
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET_KEY = 'your-secret-key'  # Use environment variable in production

def generate_token(user_id, permissions):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'permissions': permissions,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def require_jwt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user_id = payload['user_id']
            request.permissions = payload['permissions']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/v1/search', methods=['POST'])
@require_jwt
def search_entities():
    # Search logic here
    pass
```

### OAuth 2.0 Integration

```python
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc6750 import BearerTokenValidator

# OAuth 2.0 setup (simplified)
require_oauth = ResourceProtector()

@app.route('/api/v1/search', methods=['POST'])
@require_oauth('search')
def search_entities():
    # Search logic here
    pass
```

## Rate Limiting

### Simple Rate Limiting

```python
from flask import Flask, request, jsonify
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta

app = Flask(__name__)

# Rate limit storage (use Redis in production)
rate_limits = defaultdict(list)

def rate_limit(max_requests=100, window_seconds=3600):
    """Rate limit decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier (API key or IP)
            client_id = request.headers.get('X-API-Key') or request.remote_addr
            
            now = datetime.now()
            window_start = now - timedelta(seconds=window_seconds)
            
            # Clean old requests
            rate_limits[client_id] = [
                req_time for req_time in rate_limits[client_id]
                if req_time > window_start
            ]
            
            # Check limit
            if len(rate_limits[client_id]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window_seconds
                }), 429
            
            # Add current request
            rate_limits[client_id].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/api/v1/search', methods=['POST'])
@rate_limit(max_requests=100, window_seconds=3600)
def search_entities():
    # Search logic here
    pass
```

### Redis-Based Rate Limiting

```python
import redis
from flask import Flask, request, jsonify

app = Flask(__name__)
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def rate_limit_redis(max_requests=100, window_seconds=3600):
    """Rate limit using Redis"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = request.headers.get('X-API-Key') or request.remote_addr
            key = f'rate_limit:{client_id}'
            
            # Increment counter
            current = redis_client.incr(key)
            
            # Set expiry on first request
            if current == 1:
                redis_client.expire(key, window_seconds)
            
            # Check limit
            if current > max_requests:
                ttl = redis_client.ttl(key)
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': ttl
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

## Caching

### Response Caching

```python
from flask import Flask, request, jsonify
from functools import wraps
import hashlib
import json

app = Flask(__name__)

# Cache storage (use Redis in production)
cache = {}

def cache_response(ttl_seconds=300):
    """Cache response decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key from request
            cache_key = hashlib.md5(
                f"{request.path}{request.get_data()}".encode()
            ).hexdigest()
            
            # Check cache
            if cache_key in cache:
                cached_data, cached_time = cache[cache_key]
                if (datetime.now() - cached_time).seconds < ttl_seconds:
                    return jsonify(cached_data)
            
            # Execute function
            response = f(*args, **kwargs)
            
            # Cache response
            cache[cache_key] = (response.get_json(), datetime.now())
            
            return response
        return decorated_function
    return decorator

@app.route('/api/v1/entity/<int:entity_id>', methods=['GET'])
@cache_response(ttl_seconds=300)
def get_entity(entity_id):
    # Get entity logic here
    pass
```

## Load Balancing

### Nginx Configuration

```nginx
upstream senzing_backend {
    least_conn;  # Load balancing method
    
    server senzing-api-1:8080 weight=1 max_fails=3 fail_timeout=30s;
    server senzing-api-2:8080 weight=1 max_fails=3 fail_timeout=30s;
    server senzing-api-3:8080 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.company.com;
    
    location /api/ {
        proxy_pass http://senzing_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Health check
        proxy_next_upstream error timeout http_500 http_502 http_503;
    }
}
```

## Health Checks

### Health Check Endpoint

```python
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    
    health = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Check database connection
    try:
        engine = SzEngine()
        engine.initialize(instance_name='health', settings=ENGINE_CONFIG)
        stats = engine.getStats()
        engine.destroy()
        health['checks']['database'] = 'healthy'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['checks']['database'] = f'unhealthy: {str(e)}'
    
    # Check disk space
    import shutil
    disk = shutil.disk_usage('/')
    if disk.free / disk.total < 0.1:  # Less than 10% free
        health['status'] = 'degraded'
        health['checks']['disk'] = 'low space'
    else:
        health['checks']['disk'] = 'healthy'
    
    status_code = 200 if health['status'] == 'healthy' else 503
    return jsonify(health), status_code
```

## API Documentation

### OpenAPI/Swagger

```yaml
openapi: 3.0.0
info:
  title: Senzing Entity Resolution API
  version: 1.0.0
  description: API for entity resolution operations

servers:
  - url: https://api.company.com/api/v1

paths:
  /search:
    post:
      summary: Search for entities
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                NAME_FULL:
                  type: string
                EMAIL_ADDRESS:
                  type: string
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                type: object
  
  /entities/{entity_id}:
    get:
      summary: Get entity by ID
      parameters:
        - name: entity_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Entity details
        '404':
          description: Entity not found

security:
  - ApiKeyAuth: []

components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
```

## Agent Behavior

When implementing API gateway integration in Module 12:

1. **Assess requirements**: What integration pattern fits?
2. **Choose pattern**: Direct SDK, REST API, or API gateway?
3. **Generate API code**: Create REST API wrapper if needed
4. **Add authentication**: Implement API key or JWT auth
5. **Add rate limiting**: Protect from overload
6. **Add caching**: Improve performance
7. **Set up load balancing**: Configure Nginx or cloud LB
8. **Add health checks**: Monitor API health
9. **Document API**: Generate OpenAPI spec
10. **Test integration**: Verify all endpoints work

## When to Load This Guide

Load this guide when:
- Starting Module 12 (deployment)
- User asks about API integration
- Building microservices architecture
- Need to expose Senzing to multiple applications
- Setting up API gateway

## Related Documentation

- `POWER.md` - Module 12 overview
- `steering/steering.md` - Module 12 workflow
- `docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md` - Deployment guide
- `steering/multi-environment-strategy.md` - Environment management
- `steering/disaster-recovery.md` - Backup and recovery

## Version History

- **v3.0.0** (2026-03-17): API gateway patterns guide created for Module 12 enhancement

