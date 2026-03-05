# Atlas AI Routes - API Endpoint Handlers

**Module**: `app/routes`  
**Purpose**: FastAPI endpoint handlers for REST API  
**Last Updated**: March 2026

---

## 📋 Overview

The Routes module defines all REST API endpoints. Each route:

✅ **Validates Input** - Pydantic models for request parsing  
✅ **Handles Authentication** - JWT token verification  
✅ **Enforces Tenant Isolation** - All queries scoped to user's tenant  
✅ **Calls Services** - Delegates business logic to service layer  
✅ **Returns JSON** - Consistent response format  

---

## 📚 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| **Authentication** | | |
| `/api/auth/register` | POST | Create new tenant account |
| `/api/auth/login` | POST | Login with email/password |
| `/api/auth/refresh` | POST | Refresh JWT token |
| `/api/auth/me` | GET | Get user profile |
| **Query/RAG** | | |
| `/api/query/search` | POST | Execute RAG query (no agent) |
| `/api/query/cache-stats` | GET | Cache hit/miss stats |
| `/api/query/clear-cache` | DELETE | Clear cache (admin) |
| **Agent** | | |
| `/api/agent/reason` | POST | Execute agent with streaming |
| `/api/agent/runs` | GET | List execution history |
| `/api/agent/runs/{run_id}` | GET | Get detailed trace |
| `/api/agent/metrics` | GET | Performance metrics |
| **Ingestion** | | |
| `/api/ingest-rag/upload` | POST | Upload document(s) |
| `/api/ingest-rag/status/{file_id}` | GET | Track progress |
| `/api/ingest-rag/documents` | GET | List documents |
| `/api/ingest-rag/document/{doc_id}` | DELETE | Delete document |
| **Evaluation** | | |
| `/api/eval-rag/evaluate` | POST | Run evaluation |
| `/api/eval-rag/results` | GET | Get results |

---

## 🔐 Authentication

**All endpoints require JWT token** (except login/register):

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

# Token includes:
# - user_id (who is this?)
# - tenant_id (which tenant?)
# - email (user email)
# - role (admin/user/viewer)
# - exp (expiration time - 8 hours)
```

---

## 🔌 Main Endpoint Categories

### 1. Authentication (`auth_route.py`)

**Register**: Create new tenant account

```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "john@acme.com",
  "password": "secure_password",
  "company_name": "Acme Corp"
}

Response 201: {
  "tenant_id": "uuid-123",
  "user_id": "uuid-456",
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Login**: Authenticate with email/password

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "john@acme.com",
  "password": "secure_password"
}

Response 200: {
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "uuid-456", "email": "john@acme.com", "role": "admin" }
}
```

### 2. Agent (`agent_route.py`)  

**Reason (with streaming)**: Execute agent with real-time updates

```bash
POST /api/agent/reason
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "How many Q4 users?"
}

Response: (Server-Sent Events stream)
data: {"type": "thought", "content": "I need to query the database..."}
data: {"type": "token", "content": "In"}
data: {"type": "token", "content": " Q4"}
data: {"type": "final_answer", "content": "In Q4, we had 1523 users"}
data: [DONE]
```

**List Runs**: Get execution history

```bash
GET /api/agent/runs?page=1&limit=20
Authorization: Bearer <token>

Response 200: {
  "runs": [
    {
      "run_id": "uuid-123",
      "question": "How many Q4 users?",
      "final_answer": "In Q4, we had 1523...",
      "status": "completed",
      "total_cost_usd": 0.045,
      "execution_time_ms": 2345,
      "created_at": "2026-03-05T10:30:45Z"
    }
  ],
  "total": 482,
  "page": 1
}
```

### 3. Query/RAG (`query_route.py`)

**Search**: Execute RAG query (no agent reasoning)

```bash
POST /api/query/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "What is our RAG architecture?",
  "top_k": 3,
  "use_reranker": true
}

Response 200: {
  "answer": "RAG combines retrieval and generation...",
  "sources": [
    {
      "content": "RAG (Retrieval-Augmented Generation)...",
      "source": "Architecture.pdf",
      "page": 5,
      "metadata": { "author": "John Smith" }
    }
  ],
  "cache_hit": false,
  "duration_ms": 234,
  "tokens_used": 289,
  "cost_usd": 0.015
}
```

### 4. Ingestion (`ingest_rag_route.py`)

**Upload**: Ingest document(s)

```bash
POST /api/ingest-rag/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: [binary PDF data]
metadata: {"source": "Finance", "author": "John Smith"}

Response 202: {
  "file_id": "uuid-abc",
  "filename": "annual_report.pdf",
  "status": "processing",
  "chunks_created": 42,
  "duration_ms": 2345
}
```

**Check Status**: Track ingestion progress

```bash
GET /api/ingest-rag/status/uuid-abc
Authorization: Bearer <token>

Response 200: {
  "file_id": "uuid-abc",
  "filename": "annual_report.pdf",
  "status": "completed",  # or "processing", "failed"
  "progress": 100,
  "chunks_created": 42,
  "message": "Document successfully ingested"
}
```

**List Documents**: Get all ingested documents

```bash
GET /api/ingest-rag/documents?page=1&limit=50
Authorization: Bearer <token>

Response 200: {
  "documents": [
    {
      "id": "uuid-doc-1",
      "filename": "annual_report.pdf",
      "chunks": 42,
      "uploaded_at": "2026-03-05T10:30:45Z"
    }
  ],
  "total": 127,
  "page": 1
}
```

---

## 📁 Route Files

```
app/routes/
├── README.md                 ← You are here
├── __init__.py              # Export all routers
├── agent_route.py           # Agent reasoning endpoints
├── auth_route.py            # Authentication endpoints
├── query_route.py           # RAG query endpoints
├── ingest_rag_route.py      # Document ingestion endpoints
├── eval_pipline.py          # Evaluation endpoints
└── [other routes]
```

---

## 🏗️ Route Implementation Pattern

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/query", tags=["query"])

# Request model
class QueryRequest(BaseModel):
    query: str
    top_k: int = 3
    use_reranker: bool = True

# Response model
class QueryResponse(BaseModel):
    answer: str
    cache_hit: bool
    duration_ms: float

# Endpoint
@router.post("/search", response_model=QueryResponse)
async def search(
    request: QueryRequest,
    current_user: TokenData = Depends(verify_token),  # Auth
    db: Session = Depends(get_db)                      # DB
) -> QueryResponse:
    """Execute RAG query."""
    
    # Validate tenant
    if not current_user.tenant_id:
        raise HTTPException(status_code=401)
    
    # Call service
    from app.services.query_service import QueryService
    result = QueryService.execute(
        tenant_id=current_user.tenant_id,
        query=request.query,
        db=db
    )
    
    return QueryResponse(**result)
```

---

## ✅ Security Patterns

**1. Tenant Isolation**: All queries filtered by user's `tenant_id`

```python
# Routes automatically get user's tenant via token
current_user: TokenData = Depends(verify_token)
# Service enforces: WHERE tenant_id = current_user.tenant_id
```

**2. Role-Based Access**: Endpoints require specific roles

```python
@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: TokenData = Depends(require_role([Role.ADMIN]))
):
    # Only admins can delete
```

**3. Rate Limiting**: Per-tenant throttling

```bash
# Response headers
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 89
X-RateLimit-Reset: 1709630445

# Exceeded
429 Too Many Requests
```

---

## 📊 Response Format

All endpoints return consistent structure:

**Success (2xx)**:
```json
{
  "success": true,
  "data": { /* endpoint data */ },
  "timestamp": "2026-03-05T10:30:45Z"
}
```

**Error (4xx/5xx)**:
```json
{
  "success": false,
  "error": "Invalid request",
  "code": "INVALID_INPUT",
  "timestamp": "2026-03-05T10:30:45Z"
}
```

---

## 🔗 Middleware Features

**CORS**: Frontend (localhost:3000) allowed

**Metrics**: All endpoints tracked in Prometheus

**Sentry**: Errors automatically captured

**Logging**: JSON structured logs to stdout

---

## 📖 Auto-Generated Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🐛 Common HTTP Errors

| Code | Meaning | Check |
|------|---------|-------|
| 401 | No/invalid token | Authorization header correct |
| 403 | Insufficient permissions | User role for endpoint |
| 404 | Not found | URL path spelling |
| 422 | Invalid input | Request body matches model |
| 429 | Too many requests | Rate limit exceeded |
| 500 | Server error | Check logs |

---

**Version**: 2.0.0  
**Last Updated**: March 2026  
**Total Endpoints**: 18+ documented
**Auth**: JWT Bearer tokens required
