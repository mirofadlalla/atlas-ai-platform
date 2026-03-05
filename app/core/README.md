# Atlas AI Core Module - Complete Documentation

**Module**: `app/core`  
**Purpose**: Core infrastructure - configuration, database, authentication, monitoring  
**Last Updated**: March 2026

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Configuration System](#configuration-system)
3. [Database Layer](#database-layer)
4. [Authentication & Authorization](#authentication--authorization)
5. [Monitoring & Metrics](#monitoring--metrics)
6. [Rate Limiting](#rate-limiting)
7. [File Breakdown](#file-breakdown)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The Core module provides foundational infrastructure for the entire application:

✅ **Settings Management** - Environment configuration from `.env` files  
✅ **Database Connectivity** - SQLAlchemy ORM setup with connection pooling  
✅ **Authentication** - JWT token generation and validation  
✅ **Authorization** - Role-based access control (RBAC)  
✅ **Observability** - Prometheus metrics collection (40+ metrics)  
✅ **Resource Monitoring** - CPU, memory, disk usage tracking  
✅ **Rate Limiting** - Per-tenant and per-user throttling  

---

## ⚙️ Configuration System

### File: `config.py`

The `Settings` class (Pydantic) manages all configuration with defaults from `.env` file:

```python
class Settings(BaseSettings):
    # Database
    postgres_user: str = "postgres"
    postgres_pass: str = "1234"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = ""
    
    # Redis (Caching & Semantic Cache)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "atlas_redis_password"
    redis_db: int = 0
    
    # API Keys
    hf_api: str = ""           # Hugging Face API
    api_secret_key: str = ""   # JWT secret
    
    # Timeouts
    semantic_chunking_timeout: int = 900         # seconds
    embedding_request_timeout: float = 120.0     # seconds
    
    class Config:
        env_file = '.env'
        extra = "ignore"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection string"""
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_pass}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection string with authentication"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        else:
            return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
```

### Environment Variables (.env)

```bash
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASS=secure_password
POSTGRES_HOST=postgres          # Docker service name
POSTGRES_PORT=5432
POSTGRES_DB=atlas_db

# Redis Configuration
REDIS_HOST=redis                # Docker service name
REDIS_PORT=6379
REDIS_PASSWORD=atlas_redis_password
REDIS_DB=0

# API Keys
HF_API=hf_xxxxxxxxxxxx         # Hugging Face API key
API_SECRET_KEY=your-very-secret-key-change-in-prod

# RAG Configuration
SEMANTIC_CHUNKING_TIMEOUT=900
EMBEDDING_REQUEST_TIMEOUT=120.0
```

### Usage in Code

```python
from app.core.config import settings

# Access settings anywhere
db_url = settings.DATABASE_URL
redis_url = settings.REDIS_URL
secret = settings.api_secret_key
```

---

## 🗄️ Database Layer

### File: `db.py`

Manages SQLAlchemy connection pooling and session creation:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine with connection pooling
data_base = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,             # Verify connections before use
    pool_size=20,                   # Connection pool size
    max_overflow=40,                # Additional overflow connections
)

# Session factory
Sessions = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=data_base
)

# FastAPI dependency
def get_db():
    """FastAPI dependency for injecting database sessions"""
    db = Sessions()
    try:
        yield db
    finally:
        db.close()

# Direct session (for Celery tasks)
def get_db_session():
    """Get raw session for background tasks (not via FastAPI)"""
    db = Sessions()
    try:
        return db
    except Exception:
        db.close()
        raise
```

### Connection Pool Strategy

- **pool_size=20**: Minimum connections always open
- **max_overflow=40**: Up to 40 additional temporary connections
- **pool_pre_ping=True**: Test connection before use (handles stale connections)
- **Total capacity**: 60 concurrent connections

### Usage in Routes

```python
from fastapi import Depends
from app.core.db import get_db

@router.get("/api/users")
async def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
```

### Usage in Celery (Background Tasks)

```python
from app.core.db import get_db_session

@celery_app.task
def process_document(document_id: int):
    db = get_db_session()
    try:
        doc = db.query(Document).get(document_id)
        # Process document
    finally:
        db.close()
```

---

## 🔐 Authentication & Authorization

### File: `auth.py`

Implements JWT-based authentication with Bcrypt password hashing:

- **Password Hashing**: Bcrypt with salt for secure storage
- **JWT Tokens**: 8-hour expiration, HS256 algorithm
- **Role-Based Access**: Admin, User, Viewer roles
- **Tenant Isolation**: All auth checks include tenant_id

---

## 📊 Monitoring & Metrics

### File: `monitors.py`

Defines 40+ Prometheus metrics:

**HTTP Metrics**:
- `atlas_http_requests_total` - Total requests by method/endpoint/status
- `atlas_http_request_duration_seconds` - Request latency
- `atlas_http_request_size_bytes` - Request payload size
- `atlas_http_response_size_bytes` - Response payload size

**RAG Metrics**:
- `atlas_cache_hits_total` - Cache successes by level (ram/redis/db)
- `atlas_cache_misses_total` - Cache misses
- `atlas_vector_search_duration_seconds` - Search latency
- `atlas_retrieved_chunks_count` - Documents retrieved
- `atlas_reranking_duration_seconds` - Reranker latency
- `atlas_llm_cost_usd_total` - LLM costs

**Agent Metrics**:
- `atlas_agent_executions_total` - Agent runs by status
- `atlas_agent_execution_duration_seconds` - Execution time
- `atlas_agent_cost_usd_total` - Agent costs
- `atlas_agent_tokens_total` - Token consumption

**Resource Metrics**:
- `atlas_system_cpu_percent` - CPU usage
- `atlas_system_memory_percent` - Memory usage
- `atlas_system_disk_percent` - Disk usage

### Metrics Exposure

**Endpoint**: `GET /metrics`

Returns Prometheus-format metrics for scraping by Prometheus server.

---

## 🚦 Rate Limiting

### File: `rate_limitizer.py`

Prevents abuse with per-tenant, per-user limits:

- Search: 100 per hour
- Agent runs: 50 per hour
- Ingestion: 10 per hour
- Admin: Unlimited

```python
from app.core.rate_limitizer import check_rate_limit

@router.post("/api/query/search")
async def search(
    request: QueryRequest,
    _: None = Depends(check_rate_limit(action="search")),
):
    # Endpoint is automatically rate limited
    pass
```

---

## 📁 File Breakdown

| File | Purpose |
|------|---------|
| `__init__.py` | Module initialization |
| `config.py` | Settings management from `.env` |
| `db.py` | SQLAlchemy engine & session factory |
| `auth.py` | JWT authentication & RBAC |
| `monitors.py` | Prometheus metrics definitions (40+) |
| `rate_limitizer.py` | Per-tenant rate limiting |
| `README.md` | This documentation |

---

## 🐛 Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check `.env` has correct credentials
- Ensure `pool_pre_ping=True` to handle stale connections

### JWT Token Expired
- Tokens expire after 8 hours (`ACCESS_TOKEN_EXPIRE_MINUTES = 480`)
- Use refresh endpoint to get new token
- Verify `API_SECRET_KEY` is same on client and server

### Metrics Not Appearing
- Ensure middleware registered in `main.py`
- Check `/metrics` endpoint returns data
- Verify Prometheus scraping configuration

---

**Version**: 2.0.0  
**Last Updated**: March 2026  
**Key Components**: Configuration, Database, Auth, Metrics, Rate Limiting
