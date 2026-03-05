# Atlas AI Services - Business Logic Layer

**Module**: `app/services`  
**Purpose**: Business logic, external integrations, orchestration  
**Last Updated**: March 2026

---

## 📋 Overview

The Services module implements business logic independently from web framework concerns. Services:

✅ **Orchestrate Workflows** - Combine multiple repositories/APIs  
✅ **Handle External APIs** - OpenAI, Hugging Face, Qdrant integration  
✅ **Implement Domain Logic** - User management, cost tracking, authentication  
✅ **Reusable Across Layers** - Can be called from routes, Celery tasks, agents  

---

## 🏗️ Service Hierarchy

```
HTTP Route Handler (FastAPI)
    ↓
Service (Business Logic)
    ├─ Coordinates multiple repos
    ├─ Calls external APIs
    └─ Implements workflows
    ↓
Repository Layer (Data Access)
```

---

## 📁 Service Directory Structure

```
app/services/
├── README.md                              ← You are here
├── llm_runner.py                          # OpenAI API wrapper + token tracking
├── mlflow_service.py                      # Experiment tracking
├── token_service.py                       # JWT token management
├── tenant_registration_service.py         # Account creation
├── user_approval_service.py               # Admin approval workflow
├── user_profile_service.py                # User profile management
├── invitation_management_service.py       # Invitations
├── hash_service.py                        # Password hashing
│
├── auth_services/                         # Authentication workflows
│   ├── __init__.py
│   └── [auth related services]
│
├── rag_services/                          # RAG & analytics services
│   ├── __init__.py
│   ├── query_logging_service.py          # Log queries for analytics
│   ├── agent_logging_service.py          # Log agent executions
│   ├── ingest_rag_service.py             # Document ingestion orchestration
│   └── [rag related services]
│
└── __init__.py
```

---

## 💼 Key Services

### 1. **llm_runner.py** - LLM Integration with Cost Tracking

**Purpose**: Wrapper around OpenAI API with token counting and cost tracking

- **Supports Multiple Models**: GPT-4, GPT-3.5-Turbo
- **Token Counting**: Tracks usage automatically
- **Cost Calculation**: Converts tokens to USD
- **Streaming Support**: Real-time token generation
- **Error Handling**: Timeout & retry logic

### 2. **rag_services/query_logging_service.py** - Analytics Logging

**Purpose**: Async logging of queries for analytics (doesn't block user response)

- Logs to `runs` table
- Logs to `costLog` table
- Records cache hits/misses
- Tracks query performance metrics
- Triggered asynchronously via Celery

### 3. **rag_services/agent_logging_service.py** - Agent Telemetry

**Purpose**: Detailed logging of agent execution steps

- Records each node's execution
- Logs tool invocations (SQL, Retrieval)
- Tracks token usage per component
- Aggregates total cost
- Enables full audit trail

### 4. **rag_services/ingest_rag_service.py** - Document Ingestion

**Purpose**: Orchestrates document ingestion workflow

- Coordinates chunking, embedding, Qdrant insertion
- Handles file tracking & deduplication
- Triggers Celery background tasks
- Updates processing status
- Logs metrics

### 5. **tenant_registration_service.py** - Account Creation

**Purpose**: Complete tenant onboarding

- Creates tenant record
- Creates admin user
- Generates JWT token
- Initializes Qdrant collection
- Sets up rate limits

### 6. **user_approval_service.py** - Admin Approval Workflow

**Purpose**: Manage user registration approval

- Request approval (status: pending)
- Approve user (status: approved)
- Reject user (status: rejected)
- Track admin who approved
- Send notifications

### 7. **auth_services/** - Authentication Workflows

- User registration
- Login/password verification
- Token refresh
- Email validation
- Invitation acceptance

---

## 💡 Design Patterns

### Stateless Services

Services don't maintain state - they receive dependencies:

```python
# ✅ GOOD: All dependencies passed in
def create_user(email: str, password: str, tenant_id: str, db: Session):
    repo = UserRepository(db)
    user = repo.create(email, hash_password(password), tenant_id)
    return user

# ❌ BAD: Service maintains state
class UserService:
    def __init__(self):
        self.db = None  # ← Don't do this!
```

### Single Responsibility

Each service has ONE purpose:

| Service | Purpose |
|---------|---------|
| `TokenService` | JWT tokens only |
| `TenantRegistrationService` | Tenant setup only |
| `UserApprovalService` | Approval workflow only |

### Async-Ready

Services work with both FastAPI async routes AND Celery tasks:

```python
# In FastAPI route
@router.post("/api/query")
async def handle_query(request: QueryRequest, db: Session):
    result = query_service.execute(request, db)  # Called from route
    return result

# In Celery task  
@celery_app.task
def background_query(request_data):
    result = query_service.execute(request_data, db)  # Called from worker
```

---

## 🔄 Typical Service Usage

**Example: Agent Query Flow**

```python
# routes/agent_route.py

@router.post("/api/agent/reason")
async def reason_agent(
    request: AgentRequest,
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # 1. Validate user
    if not current_user.tenant_id:
        raise HTTPException(401, "Invalid token")
    
    # 2. Create run record (via service)
    from app.services.rag_services.agent_logging_service import AgentLoggingService
    run = AgentLoggingService.create_run(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        question=request.question,
        db=db
    )
    
    try:
        # 3. Execute agent
        answer = agent.execute(request.question)
        
        # 4. Log completion (async, doesn't block response)
        AgentLoggingService.log_completion.delay(
            run_id=run.id,
            answer=answer,
            tokens=1250,
            cost=0.045
        )
        
        return {
            "run_id": run.id,
            "answer": answer,
            "status": "completed"
        }
    except Exception as e:
        AgentLoggingService.log_error(run.id, str(e), db)
        raise
```

---

## 🔌 External Service Integration

### OpenAI API (`llm_runner.py`)

```python
from app.services.llm_runner import get_llm

llm = get_llm(model="gpt-4")
result = llm.generate(
    prompt="Summarize this...",
    context="...",
    max_tokens=2000
)

# Returns: {
#     "response": "...",
#     "tokens": 1250,
#     "cost_usd": 0.045
# }
```

### Qdrant Vector Store

```python
from app.repositories.qdrant import QdrantRepository

qdrant = QdrantRepository(host="qdrant", port=6333)

results = qdrant.search_hybrid(
    tenant_id="tenant-42",
    query_embedding=[...],
    top_k=3
)
```

### Celery Tasks (Background Processing)

```python
from app.services.rag_services.query_logging_service import trigger_query_logging

# Fire-and-forget: doesn't block HTTP response
trigger_query_logging.delay(
    tenant_id="tenant-42",
    query="What is...",
    duration_ms=234
)
```

---

## 📊 Logging & Observability

Services automatically log to:

1. **Structured JSON Logs** (stdout)
2. **Prometheus Metrics**
3. **Database (audit trail)**
4. **Sentry (errors)**

Example:

```json
{
  "timestamp": "2026-03-05T10:30:45Z",
  "service": "AgentLoggingService",
  "operation": "log_completion",
  "run_id": "uuid-123",
  "tenant_id": "tenant-42",
  "tokens_used": 1250,
  "cost_usd": 0.045,
  "status": "success"
}
```

---

## 🐛 Troubleshooting

### Service Method Fails with "AttributeError"

**Cause**: Missing dependency injection

**Check**: Verify all parameters passed to service method

```python
# ❌ Missing db
result = UserService.create_user(email, password, tenant_id)

# ✅ Include db
result = UserService.create_user(email, password, tenant_id, db)
```

### Circular Service Dependencies

**Cause**: Services import each other at module level

**Solution**: Import inside methods

```python
# ❌ Circular import
from app.services.token_service import TokenService

class AuthService:
    def register(self, ...):
        token = TokenService.create_token(...)

# ✅ Safe
class AuthService:
    def register(self, ...):
        from app.services.token_service import TokenService
        token = TokenService.create_token(...)
```

---

**Version**: 2.0.0  
**Last Updated**: March 2026  
**Pattern**: Stateless, reusable business logic with external integrations
