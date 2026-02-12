#  API Routers

This directory contains all API route handlers for the FastAPI Todo & Notes application. Each router is responsible for a specific domain of the application and follows RESTful principles.

## Router Structure

```
routers/
├── __init__.py          # Router initialization
├── user.py             # User management endpoints
├── task.py             # Task management endpoints
├── auth.py             # Authentication endpoints
├── health.py           # Health check endpoints
└── README.md           # This documentation
```

## Authentication & Authorization

### JWT Implementation
- **Library**: `PYJWT` for token creation and validation
- **Token Manager**: Located in `/utils/jwt_manager.py`
- **OAuth2 Scheme**: Using `OAUTH2PasswordBearer` in `/utils/oauth2_scheme.py`
- **Password Hashing**: bcrypt for secure password storage

### Authentication Flow
1. User registers/login → JWT token issued
2. Token included in `Authorization: Bearer <token>` header
3. Middleware validates token on protected routes
4. User context available in request state

## User Service (`/user`)

### Authentication Routes

#### POST `/user/login`
**Description**: Authenticate user and return JWT token

**Request Body**:
```json
{
  "username": "string",
  "password": "string",
  "email": "string"
}
```

**Response**:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Example**:
```bash
curl -X 'POST' \
  'http://localhost:8000/user/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"john_doe","password":"secure123","email":"john@example.com"}'
```

#### POST `/user/register`
**Description**: Register new user account

**Request Body**:
```json
{
  "username": "string",
  "password": "string",
  "email": "string"
}
```

**Registration Process**:
1. Validates input data (username uniqueness, email format)
2. Hashes password using bcrypt
3. Creates user record in database
4. Queues email verification task in Redis
5. Celery worker sends verification email
6. User verifies email using `/user/verify`
7. Account activated → `user.is_verified = True`
8. JWT token issued for immediate login

### Profile Management Routes

#### GET `/user/me`
**Description**: Get current user profile
- **Authentication**: Required
- **Response**: User profile data (excluding password)

#### PUT `/user/me`
**Description**: Update current user profile
- **Authentication**: Required
- **Request Body**: Updatable user fields
- **Response**: Updated user profile

#### DELETE `/user/me`
**Description**: Delete current user account
- **Authentication**: Required
- **Process**: Soft delete with data cleanup

## Avatar Management (`/user/avatar`)

### Avatar Upload & Storage

#### POST `/user/avatar`
**Description**: Upload user avatar image

**Request**: `multipart/form-data`
- **File**: Image file (JPEG, PNG, WebP supported)
- **Max Size**: 5MB

**Process**:
1. Validates image format and size
2. Resizes and optimizes image using Pillow
3. Uploads to MinIO S3 storage
4. Updates `user.avatar_url` in database
5. Returns avatar URL

**Response**:
```json
{
  "avatar_url": "https://storage.example.com/avatars/user_id.jpg",
  "message": "Avatar uploaded successfully"
}
```

#### GET `/user/avatar`
**Description**: Get user avatar URL

**Response**:
```json
{
  "avatar_url": "https://storage.example.com/avatars/user_id.jpg",
  "default_avatar": false
}
```

**Fallback**: Returns default avatar if user hasn't uploaded one

#### DELETE `/user/avatar`
**Description**: Remove user avatar

**Process**:
1. Sets `user.avatar_url = None` in database
2. Deletes avatar file from MinIO storage
3. Returns success confirmation

**Response**:
```json
{
  "message": "Avatar deleted successfully"
}
```

## Task Service (`/tasks`)

### Task Management Routes

#### GET `/tasks`
**Description**: List user's tasks with filtering and pagination

**Query Parameters**:
- `skip`: int (default: 0) - Number of tasks to skip
- `limit`: int (default: 100) - Maximum tasks to return
- `status`: str (optional) - Filter by task status
- `due_date`: str (optional) - Filter by due date range

**Authentication**: Required

**Response**:
```json
{
  "tasks": [
    {
      "task_id": "uuid",
      "title": "string",
      "description": "string",
      "created_at": "2024-01-01T00:00:00Z",
      "appointed_at": "2024-01-02T00:00:00Z",
      "status": "pending|completed|cancelled"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 100
}
```

#### POST `/tasks`
**Description**: Create new task

**Request Body**:
```json
{
  "title": "string",
  "description": "string",
  "appointed_at": "2024-01-02T00:00:00Z"
}
```

**Authentication**: Required

#### GET `/tasks/{task_id}`
**Description**: Get specific task details

**Path Parameters**:
- `task_id`: UUID of the task

**Authentication**: Required

#### PUT `/tasks/{task_id}`
**Description**: Update existing task

**Path Parameters**:
- `task_id`: UUID of the task

**Request Body**: Partial task updates
```json
{
  "title": "string",
  "description": "string",
  "appointed_at": "2024-01-02T00:00:00Z",
  "status": "completed"
}
```

**Authentication**: Required

#### DELETE `/tasks/{task_id}`
**Description**: Delete task

**Path Parameters**:
- `task_id`: UUID of the task

**Authentication**: Required

## Health Service (`/health`)

### Health Check Routes

#### GET `/health`
**Description**: Application health status

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "minio": "healthy"
  }
}
```

#### GET `/health/ready`
**Description**: Readiness probe for Kubernetes

**Response**: 200 OK if all dependencies are ready

#### GET `/health/live`
**Description**: Liveness probe for Kubernetes

**Response**: 200 OK if application is running

## Error Handling

### Standard Error Responses

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Invalid request data
- `UNAUTHORIZED`: Missing or invalid authentication
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `CONFLICT`: Resource conflict (e.g., duplicate username)
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server-side error

## Rate Limiting

### Implementation
- **Library**: `slowapi` with Redis backend
- **Default Limits**: 100 requests per minute per IP
- **Authenticated Users**: 1000 requests per minute per user
- **Strict Endpoints**: Login/register limited to 5 requests per minute

### Headers
Rate limit information included in response headers:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

## Response Format Standards

### Success Responses
```json
{
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Pagination Responses
```json
{
  "data": [ ... ],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
  }
}
```

## Security Features

### Input Validation
- **Pydantic Models**: All inputs validated using Pydantic schemas
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Prevention**: Input sanitization and output encoding

### Authentication Security
- **JWT Tokens**: Short-lived tokens (10 minutes default)
- **Refresh Tokens**: Secure token refresh mechanism
- **Password Requirements**: Minimum 6 characters, complexity requirements

### CORS Configuration
- **Origins**: Configurable allowed origins
- **Methods**: HTTP methods per endpoint
- **Headers**: Allowed headers for cross-origin requests

## Testing

### Route Testing
All routes include comprehensive tests:
- **Unit Tests**: Individual endpoint logic
- **Integration Tests**: Full request/response cycles
- **Authentication Tests**: Token validation and authorization
- **Error Handling Tests**: Various error scenarios

### Test Commands
```bash
# Run all router tests
pytest tests/test_routers/

# Run specific router tests
pytest tests/test_routers/test_user.py
pytest tests/test_routers/test_tasks.py
```

## API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### Schema Documentation
All request/response schemas are automatically documented using:
- **Pydantic Models**: Auto-generated schemas
- **Field Descriptions**: Detailed field documentation
- **Example Values**: Sample request/response data
- **Validation Rules**: Input constraints and requirements
