# FastAPI Todo & Notes App

A modern web application built with FastAPI that combines task management with markdown note-taking capabilities, all tied to user accounts for seamless cross-device synchronization.

## Features

### Core Functionality
- **User Authentication**: Secure JWT-based authentication with bcrypt password hashing
- **Task Management**: Create, read, update, and delete tasks with titles, descriptions, and scheduled dates
- **Markdown Notes**: Store and manage notes as `.md` files (infrastructure ready)
- **Avatar Management**: Upload and manage user profile pictures
- **Cross-Device Sync**: All data is tied to your user account and accessible across devices

### Technical Features
- **RESTful API**: Clean, well-documented API endpoints with OpenAPI/Swagger documentation
- **Database Migrations**: Alembic for database schema management
- **Containerized**: Full Docker and Docker Compose setup
- **Health Checks**: Built-in health monitoring endpoints
- **CORS Support**: Configured for cross-origin requests

## Stack & Technologies

### Backend
- **FastAPI** (0.115.0) - Modern, fast web framework for building APIs
- **SQLAlchemy** (2.0.36) - SQL toolkit and ORM
- **Pydantic** (2.9.2) - Data validation and settings management
- **Pydantic-Settings** (2.6.0) - Settings management
- **PyJWT** (2.10.1) - JWT token handling
- **bcrypt** (4.2.0) - Password hashing
- **asyncpg** (0.30.0) - Async PostgreSQL driver
- **aioboto3** (15.5.0) - Async AWS S3 client
- **Alembic** (1.18.1) - Database migrations
- **Pillow** (12.1.0) - Image processing
- **loguru** (0.7.2) - Structured logging

### Database & Storage
- **PostgreSQL** - Primary database for user data and tasks
- **MinIO** - S3-compatible object storage for avatars and notes

### Development & Quality
- **pytest** - Testing framework
- **flake8** - Code linting
- **pre-commit** - Git hooks for code quality
- **Docker** & **Docker Compose** - Containerization

## Project Structure

```
fastapi_todo_app/
├── app/
│   ├── config/          # Application configuration
│   ├── database/        # Database models and operations
│   ├── external/        # External utilities
│   ├── models/          # SQLAlchemy models (User, Task)
│   ├── routers/         # API endpoints (user, task, health)
│   ├── schemas/         # Pydantic schemas
│   ├── s3_client.py     # S3/MinIO client
│   ├── utils/           # Utility functions
│   └── test/            # Test suite
├── scripts/             # CI/CD scripts
├── static/              # Static assets
├── docker-compose.yaml  # Container orchestration
├── Dockerfile           # Application container
├── requirements.txt     # Production dependencies
└── requirements_dev.txt # Development dependencies
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.13 (for local development)

### 1. Clone the Repository
```bash
git clone https://github.com/katharsis23/fastapi_todo_app.git
cd fastapi_todo_app
```

### 2. Environment Configuration
Copy the sample environment file and configure your settings:
```bash
cp .env.sample .env
```

Edit `.env` with your configuration:
- **Database**: PostgreSQL connection details
- **JWT**: Secret key and token settings
- **MinIO**: S3 storage credentials

### 3. Start the Application
```bash
docker-compose up -d
```

This will start:
- **FastAPI Backend** on `http://localhost:8000`
- **PostgreSQL** on `localhost:5430`
- **MinIO Console** on `http://localhost:9001`

### 4. Access the Application
- **API Documentation**: `http://localhost:8000/docs`
- **MinIO Console**: `http://localhost:9001`

## Development

### Local Development Setup
```bash
# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_dev.txt
```

### Available Scripts

#### Pre-commit Check
```bash
./scripts/pre-commit.sh
```
Runs linting and tests before committing changes.

#### CI Pipeline
```bash
./scripts/CI.sh
```
Full CI pipeline including Docker build, linting, and testing.

### Code Quality Tools
- **Flake8**: Code linting with custom configuration in `app/.flake8`
- **Pre-commit hooks**: Automated quality checks
- **Pytest**: Comprehensive test suite

## Database Schema

### Users Table
- `user_id` (UUID, Primary Key)
- `username` (String, Unique)
- `password` (String, Hashed)
- `avatar_url` (String, Optional)

### Tasks Table
- `task_id` (UUID, Primary Key)
- `title` (String)
- `description` (Text, Optional)
- `created_at` (Timestamp)
- `appointed_at` (Timestamp, Optional)
- `user_fk` (UUID, Foreign Key)

## Docker Services

### Backend Service
- **Image**: Built from `Dockerfile`
- **Port**: 8000
- **Health Check**: Auto-restart on failure
- **Dependencies**: PostgreSQL, MinIO

### PostgreSQL Service
- **Image**: `postgres:latest`
- **Port**: 5430 (host)
- **Volume**: Persistent data storage
- **Health Check**: Connection validation

### MinIO Service
- **Image**: `minio/minio`
- **Ports**: 9000 (API), 9001 (Console)
- **Volume**: Persistent storage
- **Auto-bucket creation**: avatars, notes

## Contributing

We welcome contributions! Please follow these guidelines:

### 1. Branch Management
- Create your branch from `dev`: `git checkout -b feature/your-feature dev`
- Keep your `dev` branch updated regularly

### 2. Code Quality Philosophy
- **Refactoring is everyday work** - Don't hesitate to improve code readability and quality
- **Write tests** for any new functionality
- **Follow existing patterns** and coding standards

### 3. Before Submitting
1. Run the pre-commit script:
   ```bash
   ./scripts/pre-commit.sh
   ```
2. Ensure all linting passes and tests succeed
3. Create a pull request to `dev`
4. **Do not merge** without code review

### 4. Development Workflow
- Pre-commit hooks automatically enforce code quality
- Use meaningful commit messages
- Update documentation for any API changes

## Configuration

### Environment Variables
Refer to `.env.sample` for all available configuration options:

#### Database
- `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`, `DB_PORT`
- `DATABASE_URL` - Full connection string

#### JWT Authentication
- `SECRET_KEY` - JWT signing secret
- `ALGORITHM` - Token algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token lifetime

#### MinIO/S3 Storage
- `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
- `S3_ENDPOINT_URL`
- `S3_BUCKET_AVATARS`, `S3_BUCKET_NOTES`

## Issues & Support

For issues, questions, or suggestions:
1. Check existing issues in the repository
2. Create a new issue with detailed description
3. Include steps to reproduce any bugs

---

**Note**: This is a learning project focused on backend development and deployment practices. While functional, it may not follow all production best practices. Contributions for improvement are always welcome!
