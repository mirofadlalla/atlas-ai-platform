# Atlas AI Platform - Implementation Guide

## Overview
Complete implementation of comprehensive project requirements including cost logging, rate limiting, user invitation system, MLflow integration, and admin approval workflows.

---

## 1. Cost Logging & Run Tracking ✅

### Database Models
- **Runs** (`app/models/runs.py`) - Tracks query executions with latency and cache metrics
- **CostLog** (`app/models/costLog.py`) - Records token usage and costs per model

### Repository Pattern
- **RunsRepository** (`app/repositories/runs_repository.py`)
  - `create()` - Log new run executions
  - `get_by_tenant()` - Retrieve runs per tenant
  - `get_stats_for_tenant()` - Get aggregated statistics
  
- **CostLogRepository** (`app/repositories/cost_log_repository.py`)
  - `create()` - Log cost information
  - `get_cost_summary_for_tenant()` - Cost breakdown by tenant
  - `get_cost_by_model()` - Cost analysis by model

### Logged Events
1. **Evaluation Requests** (`POST /eval/evaluate`)
   - Tenant ID, file name, number of runs
   - Logged to MLflow and database

2. **Query Requests** (`POST /query/ask`)
   - Query text, response latency
   - Input/output tokens and costs
   - Logged to database with MLflow tracking

3. **Ingestion Operations** (`POST /ingest-rag/upload_file`)
   - File ingestion metrics
   - Document and chunk counts
   - Admin user tracking

---

## 2. Code Architecture & Organization ✅

### Language Standardization
- **retrievel_data_pipeline.py** - All comments translated to English
  - `ask_stream()` method fully documented
  - Proper code comments explaining cache behavior

### Repository Pattern Implementation
All database interactions extracted to `app/repositories/`:
- `runs_repository.py` - Run management
- `cost_log_repository.py` - Cost tracking
- `invitation_repository.py` - Invitation lifecycle
- `user_repository.py` - User management
- `tenant_repository.py` - Tenant management

### Separation of Concerns
```
Routes (API endpoints)
    ↓
Services (Business logic)
    ↓
Repositories (Data access)
    ↓
Models (Database schemas)
```

---

## 3. Rate Limiting & Access Control ✅

### Enhanced Rate Limiter (`app/core/rate_limitizer.py`)

**Role-Based Rate Limits:**
- **Admin**: 300 requests/minute
- **User**: 100 requests/minute
- **Guest**: 20 requests/minute

**Features:**
- `rate_limit(user_id, role, endpoint)` - Main rate limiting function
- `get_rate_limit_remaining()` - Check remaining quota
- `reset_rate_limit()` - Admin operation to reset limits
- Violation logging for monitoring
- Graceful degradation on Redis failure

### Protected Endpoints
1. **Ingestion Endpoint** - Admin only
   - Verifies admin role before processing
   - Rate limiting enforced at start
   ```python
   if user_role != "admin":
       raise HTTPException(status_code=403, detail="Only admins can ingest data")
   rate_limit(user_id, role="admin", endpoint="/ingest-rag/upload_file")
   ```

2. **Evaluation Endpoint** - Rate limited per user
   ```python
   rate_limit(user_id, role=user_role, endpoint="/eval/evaluate")
   ```

3. **Query Endpoint** - Rate limited per user
   ```python
   rate_limit(user_id, role="user", endpoint="/query/ask")
   ```

---

## 4. User Authentication & Invitation System ✅

### Models
- **Invitation** (`app/models/invitation.py`)
  - Fields: invited_email, token, status, expires_at, created_at, accepted_at
  - Methods: `is_expired()`, `is_valid()`
  - Foreign keys to Users and Tenants

- **Users** (`app/models/user.py`) - Enhanced with approval workflow
  - New fields: `approval_status` (approved/pending/rejected)
  - `approved_by`, `approved_at` - Admin approval tracking

### Invitation Service (`app/services/invitation_service.py`)
```python
# Core methods
- send_invitation() - Create invitation
- validate_invitation() - Check token validity
- accept_invitation_and_register() - Complete signup
- reject_invitation() - Decline invitation
- resend_invitation() - Generate new token
- get_pending_invitations_for_admin() - List pending invites
```

### Invitation Endpoints (`app/routes/auth_route.py`)

1. **Send Invitation** `POST /auth/invitations/send`
   - Admin sends invitation to user email
   - Generates unique token (32 bytes hex)
   - Sets 7-day expiration

2. **Validate Invitation** `GET /auth/invitations/validate`
   - Check if token is valid and not expired
   - Return invitation details

3. **Register via Invitation** `POST /auth/register-via-invitation`
   - Accept invitation and create account
   - Sets user approval status based on config

4. **View Pending** `GET /auth/invitations/pending`
   - Admin views all pending invitations sent
   - Shows email, status, expiration date

5. **Resend Invitation** `POST /auth/invitations/resend`
   - Expire old token and generate new one
   - Updated expiration is automatically set

---

## 5. Admin Approval Workflow ✅

### User Lifecycle
```
Invitation Created
        ↓
User Accepts & Registers
        ↓
User Status: "pending"
        ↓
Admin Reviews → Approve/Reject
        ↓
User Status: "approved" or "rejected"
```

### Approval Endpoints

1. **View Pending Approvals** `GET /auth/pending-approvals`
   - Admin views all users awaiting approval
   - Shows user name, email, registration date

2. **Approve User** `POST /auth/approve-user/{user_id}`
   - Sets status to "approved"
   - Records approver and approval timestamp
   - User can now login

3. **Reject User** `POST /auth/reject-user/{user_id}`
   - Sets status to "rejected"
   - Records rejector and rejection timestamp

### Implementation
```python
# Database fields
user.approval_status = "pending" | "approved" | "rejected"
user.approved_by = admin_user_id
user.approved_at = datetime.utcnow()

# Check before login
if user.approval_status != "approved":
    raise HTTPException(status_code=403, detail="User not approved")
```

---

## 6. MLflow Integration ✅

### MLflow Service (`app/services/mlflow_service.py`)

**Experiments:**
- `RAG_Query_Tracking` - Query/answer operations
- `RAG_Evaluation` - Evaluation runs
- `RAG_Data_Ingestion` - File ingestion operations

**Key Methods:**
```python
# Query Logging
log_query_run(run_id, query, tenant_id, latency, cache_hit, cost_usd, tokens_used, model_name)
  - Logs query parameters and metrics
  - Handles streaming responses

# Evaluation Logging
log_evaluation_run(run_name, tenant_id, dataset_size, num_runs, metrics, parameters, artifacts)
  - Tracks evaluation experiments
  - Logs parameters and metrics

# Ingestion Logging
log_ingest_run(run_name, tenant_id, file_path, documents_count, chunks_count, vector_db, success)
  - Monitors data ingestion
  - Tracks document processing

# Cost Tracking
log_cost_metrics(run_id, total_cost_usd, input_tokens, output_tokens, model_name)
  - Separate cost logging for analysis
```

**Metrics Logged:**
- Latency (seconds)
- Cost (USD)
- Token counts (input/output/total)
- Cache hits
- Document counts
- Success/failure status

### Integration Points
1. **Query Endpoint** - Logs every query execution
2. **Evaluation Endpoint** - Logs evaluation jobs
3. **Ingestion Endpoint** - Logs file processing
4. All endpoints include proper error handling and metric logging

---

## 7. Rate Limiting Middleware Implementation ✅

### Applied to All Endpoints

**Authentication Routes:**
- `/auth/register` - No rate limiting (registration)
- `/auth/login` - Rate limiting per user (lower limit for brute force protection)
- `/auth/invitations/send` - Admin rate limit
- `/auth/approve-user/{user_id}` - Admin rate limit

**Query Routes:**
- `/query/ask` - Per-user rate limit (100 req/min)
- `/query/retrieve` - Per-user rate limit

**Ingestion Routes:**
- `/ingest-rag/upload_file` - Admin rate limit (300 req/min)

**Evaluation Routes:**
- `/eval/evaluate` - Per-user rate limit
- `/eval/status/{task_id}` - Per-user rate limit

### Implementation Pattern
```python
@router.post("/endpoint")
def endpoint(
    ...,
    current_user: str = Header(...),
    user_role: str = Header(...),
    db: Session = Depends(get_db)
):
    # 1. Rate limiting FIRST
    rate_limit(
        user_id=current_user,
        role=user_role,
        endpoint="/endpoint"
    )
    
    # 2. Then business logic
    # ...
```

---

## 8. New Routes & Endpoints

### Query Routes (`app/routes/query_route.py`)

1. **POST /query/ask** - Stream answers
   - Input: QueryRequest (query text)
   - Output: StreamingResponse (answer chunks)
   - Logs: Latency, tokens, costs to DB and MLflow

2. **POST /query/retrieve** - Retrieve documents
   - Input: QueryRequest (query text)
   - Output: List of relevant documents
   - Returns: Document content + metadata

### Enhanced Routes

**Evaluation Routes** (`app/routes/eval_pipline.py`)
- `/eval/evaluate` - Enhanced with rate limiting and MLflow
- `/eval/status/{task_id}` - Improved status tracking

**Ingestion Routes** (`app/routes/ingest_rag_route.py`)
- `/ingest-rag/upload_file` - Enhanced with admin verification and logging

**Authentication Routes** (`app/routes/auth_route.py`)
- 5 new invitation endpoints
- 3 new approval endpoints
- Enhanced profile endpoint with approval status

---

## 9. Configuration Files

### Required Headers in Requests
```
current_user: <user_id>        # User identifier
user_role: admin|user|guest    # User role
tenant_id: <tenant_id>         # Tenant identifier
```

### Environment Variables (add to .env)
```
# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5000  # MLflow server
MLFLOW_EXPERIMENT_QUERY=RAG_Query_Tracking
MLFLOW_EXPERIMENT_EVAL=RAG_Evaluation
MLFLOW_EXPERIMENT_INGEST=RAG_Data_Ingestion

# Redis Configuration (for rate limiting)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

---

## 10. Database Schema Changes

### New/Updated Tables
1. **invitations** table
   - invitation_id (PK)
   - invited_email
   - invited_by (FK)
   - tenant_id (FK)
   - token (unique)
   - status
   - user_id (FK, nullable)
   - created_at, expires_at, accepted_at

2. **users** table (enhanced)
   - Added: approval_status (varchar, default='approved')
   - Added: approved_by (FK, nullable)
   - Added: approved_at (datetime, nullable)

3. **runs** table
   - Existing table with relationships to CostLog

4. **cost_log** table
   - Existing table with relationships to Runs

### Alembic Migrations
Create migrations for:
1. Add invitation table
2. Add approval fields to users table

---

## 11. Testing the Implementation

### Test Invitation Flow
```bash
# 1. Send invitation (as admin)
curl -X POST http://localhost:8000/auth/invitations/send \
  -H "current_user: admin-123" \
  -H "user_role: admin" \
  -J '{"invited_email": "user@example.com", "tenant_id": "tenant-1"}'

# 2. Validate invitation
curl -X GET "http://localhost:8000/auth/invitations/validate?token=<token>"

# 3. Register via invitation
curl -X POST http://localhost:8000/auth/register-via-invitation \
  -J '{"token": "<token>", "name": "John Doe", "password": "...", "tenant_id": "tenant-1"}'

# 4. Approve user (as admin)
curl -X POST http://localhost:8000/auth/approve-user/user-456 \
  -H "current_user: admin-123" \
  -H "user_role: admin"
```

### Test Rate Limiting
```bash
# Rapid requests (should hit rate limit after 100 calls per minute)
for i in {1..105}; do
  curl -X POST http://localhost:8000/query/ask \
    -H "current_user: user-123" \
    -H "user_role: user" \
    -H "tenant_id: tenant-1" \
    -J '{"query": "test"}'
done
```

### Test Cost Logging
```bash
# Make a query and check database
curl -X POST http://localhost:8000/query/ask \
  -H "current_user: user-123" \
  -H "user_role: user" \
  -H "tenant_id: tenant-1" \
  -J '{"query": "What is machine learning?"}'

# Query database
SELECT * FROM runs WHERE tenant_id = 'tenant-1' ORDER BY created_at DESC LIMIT 1;
SELECT * FROM cost_log WHERE run_id = '<run_id>';
```

---

## 12. Monitoring & Analytics

### MLflow Dashboard
Access at `http://localhost:5000` to view:
- Query latency trends
- Cost analysis by model
- Cache hit rates
- Evaluation results

### Database Queries
```sql
-- Total costs per tenant
SELECT tenant_id, SUM(cost_usd) as total_cost 
FROM cost_log cl
JOIN runs r ON cl.run_id = r.run_id
GROUP BY tenant_id;

-- Average latency per model
SELECT model_name, AVG(latency) as avg_latency
FROM runs r
JOIN cost_log cl ON r.run_id = cl.run_id
GROUP BY cl.model_name;

-- Pending user approvals
SELECT * FROM users WHERE approval_status = 'pending';

-- Invitation statistics
SELECT status, COUNT(*) as count FROM invitations GROUP BY status;
```

---

## 13. Security Considerations

### Rate Limiting
- Prevents denial-of-service attacks
- Protects against brute force login attempts
- Redis-backed for distributed systems

### Admin Access Control
- Role-based access control (RBAC)
- Ingestion endpoints restricted to admins
- Admin approval required for new users

### Invitation Security
- Secure token generation (32 bytes random)
- Token expiration (7 days default)
- One-time use per token
- Email validation before sending

### Approval Workflow
- Prevents unauthorized user access
- Admin oversight on new registrations
- Audit trail of approvals/rejections

---

## 14. File Structure Summary

```
app/
├── models/
│   ├── user.py (enhanced with approval_status)
│   ├── invitation.py (NEW)
│   ├── runs.py
│   ├── costLog.py
│   └── ...
├── repositories/
│   ├── runs_repository.py (NEW)
│   ├── cost_log_repository.py (NEW)
│   ├── invitation_repository.py (NEW)
│   ├── user_repository.py
│   └── ...
├── services/
│   ├── invitation_service.py (NEW)
│   ├── mlflow_service.py (NEW/Enhanced)
│   └── ...
├── routes/
│   ├── auth_route.py (Enhanced with 8 new endpoints)
│   ├── query_route.py (NEW - 2 endpoints)
│   ├── eval_pipline.py (Enhanced with logging)
│   └── ingest_rag_route.py (Enhanced with rate limiting)
├── schema/
│   ├── invitation_requests.py (NEW)
│   └── ...
├── rag/
│   ├── retrivel_data_pipline.py (Comments translated to English)
│   └── ...
├── core/
│   ├── rate_limitizer.py (Enhanced with role-based limits)
│   └── ...
└── ...
```

---

## 15. Summary of Changes

### ✅ Completed Requirements

1. **Cost Logging & Run Tracking**
   - Database tables for runs and costs
   - MLflow experiment tracking
   - All endpoints log metrics

2. **Code Architecture**
   - Repository pattern implemented
   - Comments translated to English
   - Clean separation of concerns

3. **Rate Limiting**
   - Role-based rate limits
   - Applied to all endpoints
   - Violation logging

4. **User Invitations**
   - Invitation model and repository
   - Secure token generation
   - Expiration handling

5. **Admin Approval**
   - User approval workflow
   - Approval/rejection endpoints
   - Audit trail

6. **MLflow Integration**
   - Query tracking
   - Evaluation monitoring
   - Cost analysis

7. **Comprehensive Rate Limiting**
   - Middleware on all endpoints
   - Different limits per role
   - Redis-backed persistence

---

## 16. Next Steps & Recommendations

1. **Database Migrations**: Create Alembic migrations for new tables
2. **Tests**: Add unit and integration tests
3. **Documentation**: Generate API docs with Swagger
4. **Monitoring**: Set up dashboards for MLflow metrics
5. **Email Integration**: Integrate email service for invitations
6. **Notification System**: Add user notifications for approvals
7. **Audit Logging**: Comprehensive audit trail for compliance
8. **Performance**: Cache frequently accessed data (Redis)

