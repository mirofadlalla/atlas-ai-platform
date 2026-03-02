# Atlas AI Platform - Comprehensive Project Documentation

**Project Name:** Atlas AI Platform  
**Version:** 1.0.0  
**Type:** Multi-tenant RAG (Retrieval-Augmented Generation) and LLM Platform with Agent Capabilities  
**Technology Stack:** FastAPI, PostgreSQL, Qdrant, Redis, Celery, LangChain, LangGraph, LLMs (Local)  

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Directory Structure](#directory-structure)
4. [Database Models](#database-models)
5. [Core Configuration](#core-configuration)
6. [API Endpoints](#api-endpoints)
7. [RAG Pipeline](#rag-pipeline)
8. [Agent System](#agent-system)
9. [Services & Controllers](#services--controllers)
10. [Repositories & Data Access](#repositories--data-access)
11. [Task Queue (Celery)](#task-queue-celery)
12. [Authentication & Authorization](#authentication--authorization)
13. [Frontend](#frontend)
14. [Deployment & Docker](#deployment--docker)
15. [Monitoring & Observability](#monitoring--observability)
16. [External Dependencies](#external-dependencies)

---

## Project Overview

### Purpose

Atlas AI Platform is a comprehensive, multi-tenant SaaS solution for building Retrieval-Augmented Generation (RAG) and Large Language Model (LLM) applications. It provides:

- **Document Ingestion & Processing**: Upload PDFs, DOCX, TXT, HTML files; automatic chunking (token + semantic), embedding, and hybrid search indexing
- **Hybrid Retrieval**: Dense embeddings (BGE-M3) + sparse BM25 search in Qdrant vector database
- **Semantic Caching**: Redis-based semantic cache for repeated similar queries (TTL: 24 hours, distance threshold: 0.2)
- **Intelligent Agents**: LangGraph-based agent with thought node, SQL tool, retrieval tool, and adaptive routing
- **Cost Tracking**: Per-query cost logging with input/output token counts and USD cost calculation
- **Multi-Tenant Isolation**: Complete data isolation between tenants at database and vector store levels
- **Observability**: MLflow experiment tracking, Prometheus metrics, Sentry error tracking, structured JSON logging

### Key Features

1. **Multi-Tenant Architecture**: Each tenant has isolated data, embeddings, and configurations
2. **RAG Pipeline**: Document ingestion → chunking → embedding → hybrid indexing
3. **Agent with Tools**: SQL query tool, document retrieval tool, with thought-based routing
4. **Streaming Responses**: Server-Sent Events (SSE) for real-time response streaming
5. **Async Processing**: Celery task queue for file ingestion, evaluation, and query logging
6. **Rate Limiting**: Per-user and per-role rate limiting
7. **Admin Workflows**: User approval workflows, invitation-based registration
8. **Cost Management**: Track LLM usage costs per query/session
9. **Evaluation Pipeline**: Built-in evaluation framework for RAG quality assessment

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                          │
│  /auth  /ingest-rag  /query  /agent  /eval  + Health Monitoring    │
└────────────────┬─────────────────────────────┬──────────────────────┘
                 │                             │
      ┌──────────┘                             └──────────┐
      │                                                    │
      ▼ Async Tasks                                       ▼ API Responses
┌─────────────────────┐                        (JSON, Streaming SSE)
│   Celery (Broker)   │
│   - ingest_queue    │
│   - eval_queue      │                  ┌──────────────────────┐
│   - logging_queue   │                  │ Redis Semantic Cache │
│                     │                  │ • TTL: 24h           │
│ Message Broker:     │                  │ • Distance Thresh:0.2│
│ - RabbitMQ          │                  └──────────────────────┘
└─────────────────────┘
      │
      ▼ Workers Process Tasks
┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐  ┌──────────┐
│   PostgreSQL     │  │    Qdrant    │  │ Vector Embedder │  │  Redis   │
│  - Users         │  │  (Hybrid     │  │  (BGE-M3)       │  │  Cache   │
│  - Tenants       │  │   Vectors)   │  │                 │  │          │
│  - Runs          │  │  - Dense     │  │ Sparse (BM25)   │  │          │
│  - CostLog       │  │  - Sparse    │  │                 │  │          │
│  - Files         │  │  - Metadata  │  │                 │  │          │
│  - Tracker       │  │              │  │                 │  │          │
│  - Invitations   │  └──────────────┘  └─────────────────┘  └──────────┘
└──────────────────┘
```

### Data Flow

#### 1. **Ingestion Flow**
```
User Upload File
    ↓
/api/ingest-rag/upload_file (Admin only)
    ↓
Save File to Disk
    ↓
Queue to Celery (ingest_data_queue)
    ↓
RAGPipeline.process_file()
    ├─ Calculate SHA-256 file hash
    ├─ Check if already processed (FileTracker)
    ├─ Load file (PDF/DOCX/TXT/HTML)
    ├─ Token-based chunking (2000 chars, 50 overlap)
    ├─ Semantic chunking (LLM-based breakpoints, timeout: 900s fallback)
    ├─ Generate embeddings (BGE-M3 dense + BM25 sparse)
    ├─ Insert into Qdrant with tenant scoping
    └─ Update FileTracker status to "completed"
```

#### 2. **Query Flow**
```
User Query
    ↓
/api/query/ask (Rate limited)
    ↓
RetrievalPipeline initialized
    ├─ Check Redis semantic cache
    ├─ If cache miss: Retrieve docs (Qdrant hybrid search)
    ├─ Optional: Rerank docs (cross-encoder/BM25/hybrid)
    ├─ Generate answer (Local LLM)
    ├─ Cache result in Redis (24h TTL)
    └─ Log run and costs (Celery async)
    ↓
Stream response via SSE
```

#### 3. **Agent Flow**
```
User Question
    ↓
/api/agent/ask-agent
    ↓
LangGraph Agent State Graph
    ├─ THINK Node
    │  └─ Analyze question, decide: SQL | Retrieval | Finish
    │
    ├─ ROUTER (Conditional)
    │  └─ Route to appropriate tool or finish
    │
    ├─ SQL Node (if needed)
    │  ├─ Generate SQL
    │  ├─ Validate (inject tenant_id, check keywords)
    │  └─ Execute and capture results
    │
    ├─ RETRIEVAL Node (if needed)
    │  ├─ Query Qdrant hybrid search
    │  ├─ Rerank if enabled
    │  └─ Integrate results into context
    │
    └─ FINISH Node
       └─ Synthesize final answer from all gathered data
    ↓
Stream events via SSE (thoughts, tool calls, final answer)
    ↓
Log agent execution (Celery async)
```

---

## Directory Structure

### Root Directory

```
atlas-ai/
├── alembic.ini                          # Database migration configuration
├── alembic/                             # Database migration scripts
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                        # Migration version files
├── app/                                 # Main application package
├── main.py                              # FastAPI application entry point
├── logging_setup.py                     # Logging configuration
├── requirements.txt                     # Python dependencies
├── Dockerfile                           # Docker image build file
├── docker-compose.yml                   # Multi-service Docker setup
├── monitoring/                          # Prometheus & Grafana configs
├── frontend/                            # React frontend application
├── mlruns/                              # MLflow experiment tracking data
└── README.md / SYSTEM_DIAGRAMS.md       # Documentation
```

### App Package Structure

```
app/
├── __init__.py
├── core/                                # Core services & configuration
│   ├── auth.py                          # JWT & password utilities
│   ├── config.py                        # Settings & environment variables
│   ├── db.py                            # Database connection & session factory
│   ├── metrics.py                       # Metrics utilities
│   ├── monitors.py                      # Prometheus metrics definitions
│   └── rate_limitizer.py                # Rate limiting logic
│
├── models/                              # SQLAlchemy ORM models
│   ├── base.py                          # Declarative base for all models
│   ├── user.py                          # Users model (name, email, role, approval status)
│   ├── tenant.py                        # Tenants model (organization)
│   ├── documents.py                     # Documents model (placeholder)
│   ├── runs.py                          # Query runs tracking (query, answer, latency, cache_hit)
│   ├── costLog.py                       # Cost logs (input_tokens, output_tokens, cost_usd)
│   ├── invitation.py                    # Invitation workflows (pending/accepted/expired)
│   ├── TRACKER_DB_FILE.py               # File ingestion tracking (processed_at, status)
│   └── uuid.py                          # UUID primary key helper
│
├── routes/                              # FastAPI routers
│   ├── auth_route.py                    # Authentication & tenant registration endpoints
│   ├── ingest_rag_route.py              # File ingestion endpoints
│   ├── query_route.py                   # Query/retrieval endpoints
│   ├── agent_route.py                   # Agent interaction endpoints
│   └── eval_pipline.py                  # Evaluation pipeline endpoints
│
├── controllers/                         # Business logic controllers
│   ├── auth_controller.py               # Auth operations (register, login)
│   └── ingest_rag_controller.py         # File ingestion orchestration
│
├── services/                            # Complex business logic services
│   ├── auth_services/
│   │   ├── auth_service.py              # Current user dependency & JWT validation
│   │   ├── auth_admin_service.py        # Admin registration & login
│   │   └── invites_service.py           # Invitation management
│   │
│   ├── rag_services/
│   │   ├── ingest_rag_service.py        # Celery task for file ingestion
│   │   ├── query_logging_service.py     # Celery task for query logging
│   │   ├── agent_logging_service.py     # Celery task for agent logging
│   │   ├── path_processing_service.py   # File path processing
│   │   │
│   │   └── (other RAG-specific services)
│   │
│   ├── llm_runner.py                    # Local LLM interface (CustomLocalLLM)
│   ├── mlflow_service.py                # MLflow experiment tracking
│   ├── hash_service.py                  # Hashing utilities
│   ├── token_service.py                 # Token generation/validation
│   └── (other services)
│
├── repositories/                        # Data access layer (repositories pattern)
│   ├── user_repository.py               # User operations
│   ├── tenant_repository.py             # Tenant operations
│   ├── runs_repository.py               # Query runs operations
│   ├── cost_log_repository.py           # Cost log operations
│   ├── invitation_repository.py         # Invitation operations
│   ├── trakcer_db_file_repositorie.py   # File tracker operations
│   ├── qdrant.py                        # Qdrant vector database operations
│   └── (other repositories)
│
├── rag/                                 # Retrieval-Augmented Generation pipeline
│   ├── ingest_data_pipline.py           # Main ingestion orchestrator (RAGPipeline class)
│   ├── retrivel_data_pipline.py         # Retrieval pipeline (RetrievalPipeline class)
│   ├── reranker.py                      # Document reranking strategies
│   │
│   ├── steps/                           # Pipeline steps
│   │   ├── loader.py                    # DocumentLoader (loads PDF, DOCX, TXT, HTML)
│   │   ├── file_tracker.py              # FileTracker (SHA-256 hashing, status tracking)
│   │   ├── embeddings.py                # Embedding generation helpers
│   │   ├── semantic_chunking_function.py# SemanticChunkingFunction (token + semantic chunking)
│   │   ├── ingest.py                    # Main ingestion function (chunking → embedding → Qdrant)
│   │   └── retriever.py                 # Hybrid retriever setup (Qdrant integration)
│   │
│   ├── data/                            # Sample data directory
│   ├── evaluation/                      # Evaluation pipeline components
│   │   └── (evaluation tasks)
│   │
│   └── __init__.py
│
├── agent/                               # LangGraph-based agent system
│   ├── schemas.py                       # Pydantic models (ActionDecision, format_instructions)
│   │
│   ├── core/                            # Agent graph structure
│   │   ├── graph.py                     # StateGraph builder (think → router → sql|retrieval|finish)
│   │   ├── state.py                     # AgentState TypedDict (all agent state fields)
│   │   ├── router.py                    # route_action() - conditional routing logic
│   │   └── __init__.py
│   │
│   ├── nodes/                           # Individual agent nodes
│   │   ├── thought_node.py              # Generate thoughts and decide next action
│   │   ├── sql_node.py                  # Execute SQL queries
│   │   ├── retrieval_node.py            # Document retrieval
│   │   ├── finish_node.py               # Final answer synthesis
│   │   └── __init__.py
│   │
│   ├── tools/                           # Agent tools
│   │   ├── sql_engine/                  # SQL execution and validation
│   │   │   ├── generator.py             # SQL generation
│   │   │   ├── validator.py             # SQL validation & security
│   │   │   └── executor.py              # Query execution
│   │   │
│   │   ├── retrieval.py                 # Retrieval tool
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── design_pattern/                     # Design pattern implementations
│   ├── llm_singlton.py                 # LLMService singleton (HF Inference API)
│   ├── embedded_model.py               # EmbeddedModel singleton (BGE-M3 embeddings)
│   ├── upload_factory.py               # Upload factory pattern
│   ├── user_factory.py                 # User creation factory
│   │
│   └── upload_factory_pattern/         # Upload factory implementation
│
├── schema/                              # Pydantic request/response schemas
│   ├── auth_admin.py                    # UserCreate, Token, UserLogin
│   ├── invitation_requests.py           # Invitation-related schemas
│   ├── query_request.py                 # QueryRequest schema
│   ├── upload_request.py                # Upload request schema
│   ├── tenant_schema.py                 # Tenant registration schema
│   └── (other schemas)
│
├── celery/                              # Celery task queue configuration
│   ├── celery_config.py                 # Queue setup, routing, serialization
│   └── __pycache__/
│
├── controllers/
│   ├── auth_controller.py
│   └── ingest_rag_controller.py
│
├── files/                               # File storage
│   ├── uploads/                         # Uploaded files storage
│   └── eval_files/                      # Evaluation files
│
├── __pycache__/
└── __init__.py
```

### Frontend Structure

```
frontend/
├── package.json                         # NPM dependencies (React 18, React Router)
├── build/                               # Production build output
├── public/                              # Static assets
├── src/                                 # React source code
│   ├── index.js
│   ├── App.js
│   └── (component files)
└── README.md
```

---

## Database Models

### Model: `Users` ([app/models/user.py](app/models/user.py))

**Table Name:** `users`

**Fields:**
- `id` (UUID, Primary Key): Unique user identifier
- `name` (String, Not Null): User's display name
- `email` (String, Not Null, Unique, Indexed): User's email
- `tenant_id` (String, Foreign Key to `tenants.id`): Organization tenant
- `hashed_password` (String, Not Null): BCrypt-hashed password
- `role` (String, Default: "user"): User role ("admin" or "user")
- `approval_status` (String, Default: "approved"): Approval workflow ("approved", "pending", "rejected")
- `approved_by` (String, Foreign Key to `users.id`, Nullable): Approving admin user ID
- `approved_at` (DateTime, Nullable): Approval timestamp
- `created_at` (DateTime, Default: UTC now): Account creation timestamp

**Relationships:**
- Many-to-One: `Tenants` (back_populates="users")

---

### Model: `Tenants` ([app/models/tenant.py](app/models/tenant.py))

**Table Name:** `tenants`

**Fields:**
- `id` (UUID, Primary Key): Unique tenant/organization identifier
- `name` (String, Not Null): Organization name
- `plan` (String, Not Null): Subscription plan tier
- `created_at` (DateTime, Default: UTC now): Organization creation timestamp

**Relationships:**
- One-to-Many: `Users` (back_populates="tenant")

---

### Model: `Runs` ([app/models/runs.py](app/models/runs.py))

**Table Name:** `runs`

**Fields:**
- `run_id` (UUID, Primary Key): Unique query run identifier
- `tenant_id` (String, Indexed): Tenant that executed the query
- `query` (Text): User's query text
- `answer` (Text): Generated answer
- `latency` (Float): Response time in seconds
- `cache_hit` (Boolean, Default: False): Whether response came from semantic cache
- `retrieved_docs_ids` (Text): Comma-separated IDs of retrieved documents
- `created_at` (DateTime, Default: UTC now): Execution timestamp

**Relationships:**
- One-to-One: `CostLog` (back_populates="run", uselist=False)

---

### Model: `CostLog` ([app/models/costLog.py](app/models/costLog.py))

**Table Name:** `cost_log`

**Fields:**
- `log_id` (UUID, Primary Key): Unique cost log identifier
- `run_id` (String, Foreign Key to `runs.run_id`, Unique): Associated query run
- `input_tokens` (Integer): Total input tokens consumed
- `output_tokens` (Integer): Total output tokens generated
- `model_name` (String): LLM model name used
- `cost_usd` (Numeric, 10,6): Total cost in USD
- `created_at` (DateTime, Default: UTC now): Cost logging timestamp

**Relationships:**
- Many-to-One: `Runs` (back_populates="cost_details")

---

### Model: `TRACKER_DB_FILE` ([app/models/TRACKER_DB_FILE.py](app/models/TRACKER_DB_FILE.py))

**Table Name:** `tracker_db_file`

**Fields:**
- `id` (Integer, Primary Key, Auto-increment): Unique tracking record ID
- `tenant_id` (String, Not Null): Tenant that uploaded the file
- `file_name` (String, Not Null): Original filename
- `file_hash` (String, Indexed): SHA-256 hash of file content
- `processed_at` (DateTime, Default: UTC now): Processing timestamp
- `status` (String, Default: "completed"): Status ("processing", "completed", "failed")
- `started_at` (DateTime, Nullable): Processing start timestamp
- `completed_at` (DateTime, Nullable): Processing completion timestamp

---

### Model: `Invitation` ([app/models/invitation.py](app/models/invitation.py))

**Table Name:** `invitations`

**Fields:**
- `invitation_id` (UUID, Primary Key): Unique invitation identifier
- `invited_email` (String, Not Null, Indexed): Email of invited user
- `invited_by` (String, Foreign Key to `users.id`, Not Null): Inviting admin
- `tenant_id` (String, Foreign Key to `tenants.id`, Not Null): Target organization
- `token` (Text, Not Null, Unique, Indexed): Secure invitation token
- `status` (String, Default: "pending"): Status ("pending", "accepted", "rejected", "expired")
- `user_id` (String, Foreign Key to `users.id`, Nullable): Accepted user ID
- `created_at` (DateTime, Default: UTC now): Invitation creation
- `expires_at` (DateTime, Default: UTC now + 7 days): Expiration timestamp
- `accepted_at` (DateTime, Nullable): Acceptance timestamp

**Relationships:**
- Foreign Key `invited_by` → `Users` (backref="invitations_sent")
- Foreign Key `user_id` → `Users` (backref="invitation_acceptance")
- Foreign Key `tenant_id` → `Tenants` (backref="invitations")

**Methods:**
- `is_expired()`: Check if invitation has expired
- `is_valid()`: Check if invitation is valid and can be used

---

### Model: `Documents` ([app/models/documents.py](app/models/documents.py))

**Table Name:** `documents`

**Status:** Placeholder model (currently empty, intended for future expansion)

---

## Core Configuration

### File: [app/core/config.py](app/core/config.py)

**Class:** `Settings` (extends `BaseSettings` from pydantic-settings)

**Environment Variables & Defaults:**

| Variable | Default | Type | Purpose |
|----------|---------|------|---------|
| `postgres_user` | "postgres" | str | PostgreSQL username |
| `postgres_pass` | "1234" | str | PostgreSQL password |
| `postgres_host` | "localhost" | str | PostgreSQL server host |
| `postgres_port` | 5432 | int | PostgreSQL port |
| `postgres_db` | "" | str | Database name |
| `hf_api` | "" | str | Hugging Face API token (embedding model access) |
| `api_secret_key` | "" | str | JWT secret key for authentication |
| `redis_host` | "localhost" | str | Redis server host |
| `redis_port` | 6379 | int | Redis port |
| `redis_password` | "atlas_redis_password" | str | Redis authentication password |
| `redis_db` | 0 | int | Redis database number |
| `semantic_chunking_timeout` | 900 | int | Semantic chunking timeout (sec); fallback to token-based if exceeded |
| `embedding_request_timeout` | 120.0 | float | Embedding API request timeout (sec) |

**Computed Properties:**

```python
DATABASE_URL: str
# Example: "postgresql+psycopg2://postgres:1234@localhost:5432/atlas_db"

REDIS_URL: str
# With authentication: "redis://:atlas_redis_password@localhost:6379/0"
# Without: "redis://localhost:6379/0"

REDIS_URL_NO_DB: str
# For semantic cache: "redis://:<password>@<host>:6379/0" (always uses DB 0)
```

**Loading:** Reads from `.env` file via `env_file = '.env'`

---

### File: [app/core/db.py](app/core/db.py)

**Database Engine Setup:**
```python
data_base = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True  # Test connection before using from pool
)

Sessions = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=data_base
)
```

**Dependency Functions:**

- `get_db()` (Generator): Yields a new database session for FastAPI dependency injection. Closes session after request.
  
- `get_db_session()` (Direct): Returns a database session directly without closure (for Celery background tasks, not a generator)

---

### File: [app/core/auth.py](app/core/auth.py)

**JWT Configuration:**
```python
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```

**Password Context:** BCrypt hashing via `passlib`

**Functions:**

1. `password_hash(password: str) -> str`
   - Hashes plaintext password using BCrypt
   - Returns hashed password string

2. `verify_password(plain_password: str, hashed_password: str) -> bool`
   - Verifies plaintext against hashed password
   - Returns True if match, False otherwise

3. `create_access_token(data: dict, expires_delta: timedelta | None = None) -> str`
   - Creates JWT access token
   - Default expiration: `ACCESS_TOKEN_EXPIRE_MINUTES` (60 min)
   - Encodes with `SECRET_KEY` using `HS256` algorithm
   - Returns encoded JWT token string

---

### File: [app/core/rate_limitizer.py](app/core/rate_limitizer.py)

**Rate Limiting Logic:**

Function: `rate_limit(user_id: str, role: str, endpoint: str)`

**Limits:**
- **Admin users:** Higher rate limits (e.g., 100 requests/min)
- **Regular users:** Lower rate limits (e.g., 20 requests/min)

**Purpose:** Prevent abuse, ensure fair resource allocation across tenants

---

## API Endpoints

### Base URL: `http://localhost:8000/api`

---

### **Authentication Routes** (`/api/auth`)

**File:** [app/routes/auth_route.py](app/routes/auth_route.py)

#### 1. **Tenant Registration (SaaS)**

**Endpoint:** `POST /api/auth/tenant/register`

**Description:** Register a new tenant (organization) and create first admin user.

**Request Body:**
```json
{
  "tenant_name": "Acme Corp",
  "admin_name": "John Doe",
  "admin_email": "john@acme.com",
  "admin_password": "SecurePass123",
  "plan": "professional"
}
```

**Response:** 
```json
{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "admin_email": "john@acme.com",
  "status": "success",
  "access_token": "eyJh...",
  "token_type": "bearer"
}
```

**Related Code:**
- Service: `app/services/tenant_registration_service.py::TenantRegistrationService.register_tenant()`

---

#### 2. **User Registration**

**Endpoint:** `POST /api/auth/register`

**Description:** Register new admin user and create tenant.

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@company.com",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "status": "success",
  "access_token": "eyJh...",
  "token_type": "bearer"
}
```

**Related Code:**
- Controller: `app/controllers/auth_controller.py::AuthController.register()`

---

#### 3. **User Login**

**Endpoint:** `POST /api/auth/login`

**Description:** Authenticate user and return JWT access token.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "status": "success",
  "access_token": "eyJh...",
  "token_type": "bearer",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Related Code:**
- Controller: `app/controllers/auth_controller.py::AuthController.login()`

---

#### 4. **Get Current User Profile**

**Endpoint:** `GET /api/auth/profile`

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "user-uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "role": "admin",
  "tenant_id": "tenant-uuid",
  "approval_status": "approved"
}
```

**Related Code:**
- Dependency: `app/services/auth_services/auth_service.py::get_current_user()`

---

#### 5. **Send Invitation**

**Endpoint:** `POST /api/auth/invitation/send`

**Description:** Admin sends invitation to register new user.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "invited_email": "newuser@company.com",
  "invited_by": "admin-user-id"
}
```

**Response:**
```json
{
  "invitation_id": "invitation-uuid",
  "token": "unique_token_string",
  "status": "pending",
  "expires_at": "2026-03-07T00:00:00"
}
```

**Related Code:**
- Service: `app/services/invitation_service.py::InvitationService.send_invitation()`

---

#### 6. **Validate Invitation Token**

**Endpoint:** `POST /api/auth/invitation/validate`

**Request Body:**
```json
{
  "token": "unique_token_string"
}
```

**Response:**
```json
{
  "is_valid": true,
  "tenant_id": "tenant-uuid",
  "organizer_name": "Acme Corp"
}
```

---

#### 7. **Register via Invitation**

**Endpoint:** `POST /api/auth/invitation/register`

**Request Body:**
```json
{
  "token": "unique_token_string",
  "name": "New User",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "status": "success",
  "access_token": "eyJh...",
  "tenant_id": "tenant-uuid"
}
```

---

### **Ingestion Routes** (`/api/ingest-rag`)

**File:** [app/routes/ingest_rag_route.py](app/routes/ingest_rag_route.py)

#### 1. **Upload and Ingest File**

**Endpoint:** `POST /api/ingest-rag/upload_file` (Multipart Form Data)

**Description:** Upload document file (PDF, DOCX, TXT, HTML) for ingestion into RAG system.

**Access:** Admin only (enforced by `user_role == "admin"`)

**Form Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant_id` | str | Yes | Tenant identifier |
| `file` | File | Yes | Uploaded file (PDF, DOCX, TXT, HTML) |
| `source` | str | Yes | Source name for metadata |
| `author` | str | Yes | Author name for metadata |
| `current_user` | str | Yes | Current user ID |
| `user_role` | str | Yes | User role (must be "admin") |
| `recursive` | bool | No | Recursively process directories |
| `file_extensions` | str | No | Comma-separated extensions to process |

**Response:**
```json
{
  "status": "queued",
  "message": "File queued for ingestion",
  "file_path": "app/files/uploads/document.pdf",
  "mlflow_run_id": "run-uuid"
}
```

**Processing Steps:**
1. Verify admin role
2. Apply rate limiting
3. Create upload directory if not exists
4. Save file to `app/files/uploads/`
5. Log to MLflow with tags: `{tenant_id, admin_id, uploaded_file}`
6. Queue Celery task to `ingest_data_queue`

**Related Code:**
- Service: `app/services/rag_services/ingest_rag_service.py::ingest_file_task()` (Celery task)
- Pipeline: `app/rag/ingest_data_pipline.py::RAGPipeline.process_file()`

---

### **Query Routes** (`/api/query`)

**File:** [app/routes/query_route.py](app/routes/query_route.py)

#### 1. **Ask Question (RAG Query)**

**Endpoint:** `POST /api/query/ask` (Streaming Response)

**Description:** Query documents using RAG pipeline with streaming answer.

**Headers:**
- `Authorization: Bearer <token>` (optional)
- `tenant-id: <tenant-id>` (required)
- `current-user: <user-id>` (optional)

**Request Body:**
```json
{
  "query": "What is the company's revenue for Q4?",
  "top_k": 10,
  "use_reranker": true,
  "reranker_strategy": "hybrid"
}
```

**Response:** Server-Sent Events (text/event-stream)
```
data: {"type":"document", "id":"chunk-1", "content":"...", "metadata":{...}}
data: {"type":"answer", "chunk":"Generated answer text..."}
data: {"type":"complete", "latency":1.23, "cache_hit":false}
```

**Processing Steps:**
1. Apply rate limiting (standard user limits)
2. Initialize RetrievalPipeline for tenant
3. Check Redis semantic cache:
   - If cache hit: return cached answer (cache_hit=true)
   - If cache miss: proceed to retrieval
4. Qdrant hybrid search (dense + sparse, tenant-scoped):
   - Retrieve top_k*fetch_multiplier documents
5. Optional reranking (cross-encoder, BM25, or hybrid)
6. Generate answer using local LLM
7. Cache result in Redis (TTL: 24h, distance_threshold: 0.2)
8. Log query run and costs (async Celery task)
9. Stream results to client via SSE

**Related Code:**
- Pipeline: `app/rag/retrivel_data_pipline.py::RetrievalPipeline.ask_stream()`
- Logging: `app/services/rag_services/query_logging_service.py::trigger_query_logging()`

---

### **Agent Routes** (`/api/agent`)

**File:** [app/routes/agent_route.py](app/routes/agent_route.py)

#### 1. **Ask Agent (Agentic Reasoning)**

**Endpoint:** `POST /api/agent/ask-agent` (Streaming Response)

**Description:** Ask question to intelligent agent that can use SQL and retrieval tools.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Request Body:**
```json
{
  "question": "How many users registered in Q4 and what are their geographic locations?"
}
```

**Response:** Server-Sent Events (text/event-stream)
```
data: {"type":"tool_start", "tool":"Thinking"}
data: {"type":"thought", "content":"The user is asking for user registration stats..."}
data: {"type":"tool_start", "tool":"SQL Query"}
data: {"type":"tool_end", "tool":"SQL Query"}
data: {"type":"tool_start", "tool":"Document Retrieval"}
data: {"type":"tool_end", "tool":"Document Retrieval"}
data: {"type":"answer", "content":"Based on the data gathered..."}
data: {"type":"complete", "final_answer":"..."}
```

**Agent Execution Flow:**
1. Initialize LangGraph agent with user question
2. **THINK Node:** Analyze question, decide action (sql/retrieval/finish)
3. **ROUTER:** Route to appropriate tool or finish based on decision
4. **SQL Node (if needed):**
   - Generate SQL query from question
   - Validate SQL (inject tenant_id, check for dangerous keywords)
   - Execute query and capture results
   - Return observation
5. **RETRIEVAL Node (if needed):**
   - Query Qdrant hybrid search with question
   - Rerank if enabled
   - Return retrieved documents as observations
6. **Loop back to THINK** until max_steps (10) exceeded or finish action chosen
7. **FINISH Node:** Synthesize final answer from observation history
8. Log execution to database (async Celery task)
9. Stream all events to client via SSE

**Related Code:**
- Graph: `app/agent/core/graph.py::agent_app`
- Nodes: `app/agent/nodes/{thought,sql,retrieval,finish}_node.py`
- Router: `app/agent/core/router.py::route_action()`
- Logging: `app/services/rag_services/agent_logging_service.py::trigger_agent_logging()`

---

### **Evaluation Routes** (`/api/eval`)

**File:** [app/routes/eval_pipline.py](app/routes/eval_pipline.py)

**Description:** Evaluation pipeline endpoints for assessing RAG quality.

**Endpoints:** Vary by evaluation type; generally follow pattern:
- `POST /api/eval/evaluate_retrieval` - Evaluate retrieval quality
- `POST /api/eval/evaluate_reranking` - Evaluate reranking effectiveness
- `POST /api/eval/evaluate_answer` - Evaluate answer generation quality

---

### **Health Check Route** (from [main.py](main.py))

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "Atlas AI Platform",
  "version": "1.0.0"
}
```

---

## RAG Pipeline

### Overview

The RAG (Retrieval-Augmented Generation) pipeline processes documents through ingestion, retrieval, and generation stages with hybrid search capabilities.

### 1. Ingestion Pipeline

**Main Orchestrator:** `app/rag/ingest_data_pipline.py::RAGPipeline`

#### Step 1: **File Hash Calculation**

**Module:** `app/rag/steps/file_tracker.py::FileTracker`

```python
class FileTracker:
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of file content"""
        # Read file in chunks
        # Compute SHA-256 digest
        # Return hex digest
```

**Purpose:** Detect if file content has changed; skip re-processing identical files

**Storage:** Stored in `TRACKER_DB_FILE.file_hash` column

---

#### Step 2: **Duplicate Detection**

**Function:** `FileTracker.is_file_processed(tenant_id, file_hash, db) -> bool`

**Query:** Check if combination of `(tenant_id, file_hash)` exists in `tracker_db_file` table with status="completed"

**Action:** If found, skip processing and return skipped status

---

#### Step 3: **File Loading**

**Module:** `app/rag/steps/loader.py::DocumentLoader`

```python
class DocumentLoader:
    @staticmethod
    def load_file(file_path: str, custom_metadata: Dict[str, Any]) -> List[Document]:
        """Load file based on extension and attach metadata"""
```

**Supported File Types:**
- `.pdf`: PyPDFLoader (LangChain)
- `.docx`: UnstructuredWordDocumentLoader
- `.txt`: TextLoader (UTF-8 encoding for Arabic support)
- `.html`: UnstructuredHTMLLoader

**Output:** List of `langchain_core.documents.Document` objects, each with:
- `page_content`: Text from page/section
- `metadata`: Original file metadata + custom_metadata (tenant_id, source, author)

**Error Handling:** Raises `FileNotFoundError` or `ValueError` for invalid files

---

#### Step 4: **Text Combination**

**Process:** Combine all loaded documents' `page_content` into single text string separated by `"\n\n"`

**Rationale:** Prepare for semantic/token chunking on full document text

---

#### Step 5: **Semantic Chunking**

**Module:** `app/rag/steps/semantic_chunking_function.py::SemanticChunkingFunction`

**Two-Stage Chunking:**

**Stage 1 - Token-Based Chunking:**
```python
RecursiveCharacterTextSplitter(
    chunk_size=2000,      # characters per chunk
    chunk_overlap=50,     # overlap between chunks
    separators=["\n\n", "\n", ".", " "]  # split on these, in order
)
```

**Stage 2 - Semantic Chunking:**
```python
LangChain SemanticChunker(
    embeddings=embedding_model,
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=95  # 95th percentile of distance
)
```

**Timeout Protection:**
```python
try:
    # Attempt semantic chunking
    chunks = semantic_chunker.split_documents(docs)
except TimeoutError:
    # Fallback to token-based chunks if exceeds semantic_chunking_timeout (900s)
    chunks = token_splitter.split_documents(docs)
```

**Chunk ID Generation:**
```python
chunk_id = generate_chunk_id(
    text=chunk.page_content,
    tenant_id=metadata["tenant_id"],
    source=metadata["source"]
)
# Returns stable hash-based ID for deduplication
```

---

#### Step 6: **Embedding Generation**

**Module:** `app/design_pattern/embedded_model.py::EmbeddedModel` (Singleton)

**Dense Embeddings:**
- **Model:** BAAI/bge-m3 (HuggingFace)
- **Dimensions:** 1024
- **Output:** Vector per chunk

**Sparse Embeddings:**
- **Model:** Qdrant/bm25 (BM25 algorithm)
- **Output:** Sparse vector per chunk

**Endpoint:** Calls HuggingFace Inference API with `HF_TOKEN_M` authentication

---

#### Step 7: **Qdrant Insertion**

**Module:** `app/repositories/qdrant.py::QdrantRepository`

**Collection:** `atlas_documents1`

**Process:**

```python
def add_hybrid_documents(self, collection_name: str, documents: list[dict]):
    """
    documents format:
    [
        {
            "id": chunk_id,
            "text": chunk_text,
            "metadata": {"tenant_id": "...", "source": "...", "author": "..."}
        },
        ...
    ]
    """
    # 1. Extract point IDs from incoming documents
    point_ids = [doc.get("id") for doc in documents]
    
    # 2. Check for existing points in Qdrant (deduplication)
    existing_points = self.client.retrieve(
        collection_name=collection_name,
        ids=point_ids,
        with_payload=False,
        with_vectors=False
    )
    existing_ids = {point.id for point in existing_points}
    
    # 3. Filter out already-existing documents
    new_documents = [doc for doc in documents if doc.get("id") not in existing_ids]
    
    # 4. Skip if all documents already exist
    if not new_documents:
        return
    
    # 5. Generate dense and sparse embeddings for new documents only
    texts = [doc["text"] for doc in new_documents]
    dense_vectors = self.dense_model.embed_documents(texts)
    sparse_vectors = list(self.sparse_model.embed(texts))
    
    # 6. Create PointStruct objects with dense+sparse vectors and payload
    points = [
        PointStruct(
            id=new_documents[i].get("id"),
            vector={
                "dense": dense_vectors[i],
                "sparse": sparse_vectors[i]
            },
            payload={
                "content": new_documents[i]["text"],
                "metadata": new_documents[i]["metadata"]
            }
        )
        for i in range(len(new_documents))
    ]
    
    # 7. Upload to Qdrant
    self.client.upsert(
        collection_name=collection_name,
        points=points
    )
```

---

#### Step 8: **File Tracker Update**

**Module:** `app/rag/steps/file_tracker.py::FileTracker`

**Status Updates:**
- **Mark Processing:** `FileTracker.mark_processing(tenant_id, file_name, file_hash, db)`
  - Status: "processing"
  - Sets `started_at` timestamp
  
- **Mark Completed:** `FileTracker.mark_completed(tenant_id, file_hash, db)`
  - Status: "completed"
  - Sets `completed_at` timestamp
  
- **Mark Failed:** `FileTracker.mark_failed(tenant_id, file_hash, db)`
  - Status: "failed"
  - Log error details

---

### 2. Retrieval Pipeline

**Main Class:** `app/rag/retrivel_data_pipline.py::RetrievalPipeline`

**Initialization:**
```python
def __init__(
    self,
    tenant_id: int,
    use_reranker: bool = True,
    reranker_strategy: str = None,  # "cross-encoder", "bm25", "hybrid"
    db: Session = None
):
    self.tenant_id = tenant_id
    self.retriever = get_retriever(tenant_id)  # Tenant-scoped
    self.use_reranker = use_reranker
    self.ranking_service = _get_ranking_service(strategy=reranker_strategy) if use_reranker else None
    self.embedding_model = _embedding_model  # Singleton
    self.local_llm = _cached_llm  # Singleton
    self.qa_chain = create_retrieval_chain(self.retriever, self.document_chain)
```

#### Retriever Setup

**Module:** `app/rag/steps/retriever.py::get_retriever()`

```python
def get_retriever(tenant_id: int):
    # Use cached retriever if available (per-tenant singleton)
    if tenant_id in _retrievers_cache:
        return _retrievers_cache[tenant_id]
    
    # Create Qdrant vectorstore with:
    # - embedding: BGE-M3 singleton
    # - sparse_embedding: BM25
    # - retrieval_mode: HYBRID
    vectorstore = QdrantVectorStore(
        client=qdrant_client,
        collection_name="atlas_documents1",
        embedding=_embedding_model,
        vector_name="dense",
        sparse_embedding=sparse_embeddings,
        sparse_vector_name="sparse",
        retrieval_mode=RetrievalMode.HYBRID,
        content_payload_key="content",
        metadata_payload_key="payload"
    )
    
    # Create retriever with tenant-scoped filter
    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 5,  # Default top-k
            "filter": models.Filter(
                must=[
                    models.FieldCondition(
                        key="payload.tenant_id",
                        match=models.MatchValue(value=tenant_id)
                    )
                ]
            )
        }
    )
    
    # Cache for reuse
    _retrievers_cache[tenant_id] = retriever
    return retriever
```

**Key Features:**
- Tenant isolation via Filter with `payload.tenant_id`
- Hybrid search combines dense (semantic) + sparse (keyword) results
- Cached singleton per tenant for performance

---

#### Redis Semantic Cache

**Module:** `app/rag/retrivel_data_pipline.py` (RetrievalPipeline.__init__)

**Configuration:**
```python
cache = RedisSemanticCache(
    redis_url=settings.REDIS_URL_NO_DB,
    embeddings=self.embedding_model,  # Use same embedding model for consistency
    ttl=86400,              # 24 hours
    distance_threshold=0.2  # Similar queries within 0.2 distance score
)
set_llm_cache(cache)  # Global LangChain cache
```

**How It Works:**
1. New query comes in
2. Query is embedded using BGE-M3 model
3. Redis searches similar embeddings (distance < 0.2)
4. If similar cached query found: return cached answer (cache_hit=true)
5. If no match: proceed with retrieval, cache result

**TTL:** Cached answers expire after 24 hours

---

#### Document Reranking

**Module:** `app/rag/reranker.py::RankingService`

**Reranking Strategies:**

1. **Cross-Encoder:** Neural cross-encoder model for relevance scoring
   ```python
   model = cross_encoder("ms-marco-MiniLM-L-12-v2")
   scores = model.predict([[query, doc] for doc in docs])
   ```

2. **BM25:** Keyword-based ranking via sparse embeddings
   - Higher score if query keywords appear in document

3. **Hybrid:** Combine and normalize both scores
   ```python
   hybrid_score = (cross_encoder_score + bm25_score) / 2
   ```

**Process:**
```python
def retrieve(self, query: str, top_k: int = 10, fetch_multiplier: int = 2):
    # Fetch more docs initially for better reranking
    fetch_count = top_k * fetch_multiplier
    docs = self.retriever.invoke(query)  # Hybrid search
    
    if self.use_reranker:
        # Rerank fetched documents
        ranked_docs = self.ranking_service.rerank(query, docs, top_k)
        return ranked_docs[:top_k]  # Return top_k after reranking
    
    return docs[:top_k]  # Return raw top_k if no reranking
```

---

#### LLM for Answer Generation

**Module:** `app/services/llm_runner.py::CustomLocalLLM`

**Model:** Qwen2.5-1.5B-Instruct (or configured local model)

**Access:** HuggingFace Inference API with `HF_TOKEN_M`

**Chain Setup:**
```python
prompt = ChatPromptTemplate.from_template(
    "Answer the following question based only on the provided context:\n\n"
    "Context: {context}\n\n"
    "Question: {input}\n\n"
    "Answer:"
)

document_chain = create_stuff_documents_chain(self.local_llm, prompt)
qa_chain = create_retrieval_chain(self.retriever, self.document_chain)
```

**Streaming:**
```python
def ask_stream(self, query: str):
    for chunk in self.qa_chain.stream({"input": query}):
        if "answer" in chunk:
            yield chunk["answer"]  # Yield answer chunks
```

---

#### Query Logging (Async Celery Task)

**Module:** `app/services/rag_services/query_logging_service.py`

**Function:** `trigger_query_logging()`

**Celery Task:** `log_query_run_and_cost()`

**Logged Information:**
- Query text
- Answer text
- Latency (seconds)
- Cache hit status
- Retrieved document IDs
- Input/output tokens
- Cost in USD
- Model name used

**Storage:**
- `Runs` table: query, answer, latency, cache_hit, retrieved_docs_ids
- `CostLog` table: input_tokens, output_tokens, model_name, cost_usd

---

## Agent System

### Overview

The Agent system is built on **LangGraph**, a framework for building multi-step, stateful reasoning workflows. Agents can think, make decisions, execute tools (SQL or retrieval), and synthesize final answers.

### Architecture

**File:** `app/agent/core/graph.py`

**Graph Structure:**

```
                    ┌─────────────────┐
                    │   Entry Point   │
                    │    (THINK)      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     ROUTER      │
                    │  (Conditional)  │
                    └────┬────────┬───┘
                         │        │
                    ┌────▼─┐  ┌──▼────┐
                    │ SQL  │  │RETRIEV│
                   │TOOL  │  │AL TOOL│
                    └────┬─┘  └──┬────┘
                         │       │
                         └───┬───┘
                             │
                             ▼
                      ┌──────────────┐
                      │   THINK      │
                      │  (Loop back) │
                      └──────┬───────┘
                             │
                    ┌────────▼────────┐
                    │   FINISH NODE   │
                    │  (Synthesize)   │
                    └─────────────────┘
```

**Builder Code:**
```python
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("think", thought_node)
builder.add_node("sql_tool", sql_node)
builder.add_node("retrieval_tool", retrieval_node)
builder.add_node("finish", finish_node)

# Entry point
builder.set_entry_point("think")

# Conditional routing from think node
builder.add_conditional_edges(
    "think",
    route_action,  # Routing function
    {
        "sql": "sql_tool",
        "retrieval": "retrieval_tool",
        "finish": "finish"
    }
)

# Edges back to think for looping
builder.add_edge("sql_tool", "think")
builder.add_edge("retrieval_tool", "think")
builder.add_edge("finish", END)

# Compile
agent_app = builder.compile()
```

---

### Agent State

**File:** `app/agent/core/state.py`

**TypedDict:** `AgentState`

**Fields:**

| Field | Type | Purpose |
|-------|------|---------|
| `question` | str | User's question or task |
| `tenant_id` | int | Tenant identifier |
| `thought` | Optional[str] | Current reasoning/thought |
| `last_action` | Optional[str] | Last action taken (sql/retrieval/finish) |
| `observation` | Optional[str] | Feedback from last action |
| `observation_history` | List[str] | All observations from all steps |
| `last_sql` | Optional[str] | Last SQL query generated |
| `retrieval_context` | Optional[str] | Results from document retrieval |
| `sql_result` | Optional[str] | Results from SQL execution |
| `step_count` | int | Number of steps taken (max 10) |
| `total_cost` | float | Total cost accumulated |
| `thoughts` | List[str] | All thoughts during execution |
| `final_answer` | Optional[str] | Final synthesized answer |

---

### Agent Nodes

#### 1. Thought Node

**File:** `app/agent/nodes/thought_node.py::thought_node()`

**Function Signature:**
```python
def thought_node(state: AgentState) -> dict:
    """Generate thought and decide next action"""
```

**Process:**

1. **Analyze Question:**
   - Check for data-related keywords (how many, count, total, revenue, stats)
   - Check for knowledge-related keywords (what is, explain, describe)

2. **Context Building:**
   - Track what actions have been completed
   - Determine question type (data vs knowledge)

3. **Decision Making:**
   - Call LLM to generate thought and decide action

4. **LLM Prompt:**
   ```
   Question: <user_question>
   Question Type: <data/knowledge/mixed>
   Actions Already Taken: <list of prior actions>
   
   Think step-by-step about what information is needed.
   Decide the next action: 'sql', 'retrieval', or 'finish'
   
   Respond in JSON format:
   {"thought": "...", "action": "sql|retrieval|finish"}
   ```

5. **JSON Parsing:**
   - Extract JSON from LLM response
   - Parse `ActionDecision` Pydantic model

6. **State Update:**
   ```python
   return {
       "thought": thought_content,
       "last_action": action,
       "step_count": state["step_count"] + 1,
       "thoughts": state["thoughts"] + [thought_content]
   }
   ```

---

#### 2. SQL Node

**File:** `app/agent/nodes/sql_node.py::sql_node()`

**Function Signature:**
```python
def sql_node(state: AgentState) -> dict:
    """Execute SQL query on database"""
```

**Process:**

1. **SQL Generation:**
   - LLM generates SQL from question and context
   - Prompt includes database schema

2. **SQL Validation:**
   - Inject tenant_id filter: `WHERE tenant_id = <current_tenant>`
   - Check for dangerous keywords (DROP, DELETE, ALTER, TRUNCATE)
   - Validate syntax

3. **Error Handling:**
   - Catch SQL syntax errors
   - Return error observation if validation fails

4. **Execution:**
   - Connect to PostgreSQL
   - Execute validated query
   - Capture results (up to 100 rows)

5. **Result Formatting:**
   - Convert results to formatted string
   - Example: `"SQL Result: [{'user_id': '1', 'count': 5}]"`

6. **State Update:**
   ```python
   return {
       "last_sql": generated_sql,
       "sql_result": formatted_result,
       "observation": f"[DATABASE] {observation_text}",
       "observation_history": state["observation_history"] + [observation]
   }
   ```

---

#### 3. Retrieval Node

**File:** `app/agent/nodes/retrieval_node.py::retrieval_node()`

**Function Signature:**
```python
def retrieval_node(state: AgentState) -> dict:
    """Retrieve documents from knowledge base"""
```

**Process:**

1. **Retrieval:**
   - Query Qdrant hybrid search with question
   - Tenant-scoped filter applied

2. **Reranking (Optional):**
   - Apply reranking if configured
   - Get top-k most relevant documents

3. **Context Formatting:**
   - Extract document text and metadata
   - Format as readable context string
   - Example: `"Document 1: [source] text..."`

4. **Error Handling:**
   - Catch retrieval errors
   - Return error observation if retrieval fails

5. **State Update:**
   ```python
   return {
       "retrieval_context": formatted_documents,
       "observation": f"Retrieved {len(docs)} documents",
       "observation_history": state["observation_history"] + [observation]
   }
   ```

---

#### 4. Finish Node

**File:** `app/agent/nodes/finish_node.py::finish_node()`

**Function Signature:**
```python
def finish_node(state: AgentState) -> dict:
    """Synthesize final answer from gathered information"""
```

**Process:**

1. **Context Compilation:**
   - Gather all observations
   - Include SQL results if available
   - Include retrieval context if available
   - Include thought history

2. **Final Answer Generation:**
   - LLM prompt includes all gathered data
   - Request comprehensive answer
   - Prompt: `"Based on the information gathered, answer the user's question..."`

3. **State Update:**
   ```python
   return {
       "final_answer": generated_answer,
       "observation": f"[FINISH] {generated_answer}"
   }
   ```

---

### Router

**File:** `app/agent/core/router.py::route_action()`

**Function Signature:**
```python
def route_action(state: AgentState) -> str:
    """Route to next node based on agent decision and state"""
```

**Routing Logic:**

1. **Check Step Limit:**
   - Max 10 steps to prevent infinite loops
   - Return "finish" if reached

2. **Analyze Last Decision:**
   - Get `last_action` from state
   - Validate (must be sql/retrieval/finish)

3. **Prevent Infinite Retry:**
   - Track if action was attempted before
   - If retrieval was attempted and no data → move to finish
   - If SQL was attempted and no data → try retrieval if not attempted

4. **Force Data Gathering:**
   - If agent wants to finish but no data gathered
   - And question appears to need data
   - Force SQL or retrieval attempt

5. **Return Decision:**
   ```python
   if step_count >= 10:
       return "finish"
   elif last_action == "sql":
       return "sql" # or "retrieval" if SQL attempted but failed
   elif last_action == "retrieval":
       return "retrieval"
   else:  # "finish"
       return "finish"
   ```

---

### SQL Tools

**Module:** `app/agent/tools/sql_engine/`

#### Generator

**File:** `generator.py`

**Function:** Generates SQL from natural language question

**Input:** User question + database schema + context

**Process:**
1. Format database schema (table names, column names, types)
2. Send prompt to LLM with question
3. LLM generates SQL query
4. Extract SQL from response

**Output:** SQL query string

#### Validator

**File:** `validator.py`

**Function:** Validates SQL for safety and correctness

**Checks:**
- Syntax validation (parse as AST/use sqlparse)
- No dangerous keywords (DROP, DELETE, ALTER, TRUNCATE, EXEC)
- Inject tenant_id filter automatically
- No schema modification attempts

**Output:** Validated, tenant-scoped SQL or error

#### Executor

**File:** `executor.py`

**Function:** Executes validated SQL on PostgreSQL

**Process:**
1. Create database connection
2. Execute query with timeout (default 30s)
3. Fetch results (limit to 100 rows)
4. Format results as string

**Output:** Query results or error message

---

### Retrieval Tool

**File:** `app/agent/tools/retrieval.py`

**Function:** Retrieves documents from knowledge base

**Process:**
1. Query Qdrant with agent question
2. Tenant-scoped filter applied
3. Optional reranking
4. Format documents

**Output:** Retrieved documents with metadata

---

## Services & Controllers

### Authentication Services

**Module:** `app/services/auth_services/`

#### File: `auth_service.py`

**Dependency Function:** `get_current_user(Authorization: Annotated[str, Header()] = None)`

**Process:**
1. Extract Bearer token from Authorization header
2. Decode JWT token using SECRET_KEY
3. Validate token expiration
4. Return User object or raise HTTPException(401)

**Usage:** `Depends(get_current_user)` in route parameters

---

#### File: `auth_admin_service.py`

**Class:** `AuthService`

**Methods:**

1. `register_admin_user(name, email, password, db) → User`
   - Hash password with BCrypt
   - Create user with role="admin"
   - Return User object

2. `authenticate_user(email, password, db) → User`
   - Query user by email
   - Verify password
   - Return User or raise exception

3. `create_tenant(tenant_name, db) → Tenant`
   - Create new tenant in database
   - Return Tenant object

---

#### File: `invites_service.py`

**Class:** `InvitationService`

**Methods:**

1. `send_invitation(invited_email, invited_by, tenant_id, db) → Invitation`
   - Generate unique token (secrets.token_urlsafe(32))
   - Create invitation record with status="pending"
   - Set expiration (7 days from now)

2. `validate_invitation(token, db) → Invitation`
   - Query by token
   - Check status == "pending"
   - Check not expired
   - Return invitation or raise exception

3. `accept_invitation(token, user_id, db) → Invitation`
   - Validate invitation exists
   - Update status to "accepted"
   - Set user_id
   - Set accepted_at timestamp

---

### RAG Services

**Module:** `app/services/rag_services/`

#### File: `ingest_rag_service.py`

**Celery Task:** `ingest_file_task(file_path, tenant_id, source, author)`

**Implementation:**
```python
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5},
    time_limit=600,
    soft_time_limit=550
)
def ingest_file_task(self, file_path: str, tenant_id: str, source: str, author: str):
    """
    Async task to ingest files into RAG pipeline.
    Automatically retries on failure (up to 5 times).
    Soft limit: 550s, Hard limit: 600s (10 min)
    """
    try:
        db = get_db_session()
        from app.rag.ingest_data_pipline import RAGPipeline
        
        custom_metadata = {
            "tenant_id": tenant_id,
            "source": source,
            "author": author
        }
        return RAGPipeline.process_file(
            file_path=file_path,
            custom_metadata=custom_metadata,
            db=db
        )
    except MemoryError:
        self.retry(countdown=60, exc=MemoryError(...), max_retries=3)
    except Exception as exc:
        self.retry(countdown=10, exc=exc)
```

---

#### File: `query_logging_service.py`

**Function:** `trigger_query_logging(run_data, cost_data, db)`

**Celery Task:** `log_query_run_and_cost(run_id, tenant_id, query, answer, latency, cache_hit, input_tokens, output_tokens, model_name, cost_usd)`

**Process:**
1. Create Runs record in database
2. Create CostLog record linked to run
3. Return success status

---

#### File: `agent_logging_service.py`

**Function:** `trigger_agent_logging(agent_result, db)`

**Celery Task:** `log_agent_run(agent_result_data)`

**Process:**
1. Extract execution data from agent result
2. Log to Runs table (query=question, answer=final_answer)
3. Log costs if applicable
4. Return success status

---

### MLflow Service

**Module:** `app/services/mlflow_service.py`

**Class:** `MLflowService`

**Class Variables:**
```python
DEFAULT_EXPERIMENT_INGEST = "atlas_ingestion"
DEFAULT_EXPERIMENT_QUERY = "atlas_queries"
DEFAULT_EXPERIMENT_AGENT = "atlas_agent"
```

**Methods:**

1. `start_run(experiment_name, run_name, tags={}) → run_id`
   - Create or get experiment
   - Start new MLflow run with tags
   - Return run_id

2. `log_param(key, value)` - Log parameter

3. `log_metric(key, value)` - Log metric

4. `end_run()` - End current run

**Usage Example:**
```python
mlflow_run_id = MLflowService.start_run(
    experiment_name="atlas_queries",
    run_name=f"query_{tenant_id}_{time}",
    tags={"tenant_id": tenant_id, "user_id": current_user}
)
mlflow.log_param("query_length", len(query))
mlflow.end_run()
```

---

### LLM Runner Service

**Module:** `app/services/llm_runner.py`

**Class:** `CustomLocalLLM` (LangChain compatible)

**Purpose:** Wrapper around local/remote LLM for answer generation

**Methods:**

1. `__call__(prompt: str) → str`
   - Send prompt to configured LLM
   - Return generated text

2. `generate()` - Generate response

**Configuration:**
- Model: Qwen2.5-1.5B-Instruct or configured
- API: HuggingFace Inference API
- Token tracking: Tracks input/output tokens for cost calculation

---

## Repositories & Data Access

**Pattern:** Repository pattern for clean data access abstraction

**Module:** `app/repositories/`

### File: `user_repository.py`

**Class:** `UserRepository(db: Session)`

**Methods:**

1. `create_user(name, email, hashed_password, role, tenant_id) → User`
   - Create new user record
   - Return User object

2. `get_user_by_email(email) → User`
   - Query user by email
   - Return User or None

3. `get_user_by_id(user_id) → User`
   - Query user by ID
   - Return User or None

4. `update_approval_status(user_id, status, approved_by) → User`
   - Update approval_status, approved_by, approved_at

---

### File: `tenant_repository.py`

**Class:** `TenantRepository(db: Session)`

**Methods:**

1. `create_tenant(name, plan) → Tenant`
   - Create new tenant record
   - Return Tenant object

2. `get_tenant_by_id(tenant_id) → Tenant`
   - Query tenant by ID
   - Return Tenant or None

3. `get_tenant_by_name(name) → Tenant`
   - Query tenant by organization name

---

### File: `runs_repository.py`

**Class:** `RunsRepository(db: Session)`

**Methods:**

1. `create_run(run_id, tenant_id, query, answer, latency, cache_hit, retrieved_docs_ids) → Runs`
   - Create new run record
   - Return Runs object

2. `get_run_by_id(run_id) → Runs`
   - Query run by run_id
   - Return Runs or None

3. `get_tenant_runs(tenant_id, limit=100) → List[Runs]`
   - Get all runs for tenant
   - Order by created_at DESC

4. `calculate_average_latency(tenant_id) → float`
   - Get average query latency for tenant

---

### File: `cost_log_repository.py`

**Class:** `CostLogRepository(db: Session)`

**Methods:**

1. `create_cost_log(log_id, run_id, input_tokens, output_tokens, model_name, cost_usd) → CostLog`
   - Create new cost log record
   - Return CostLog object

2. `get_cost_by_run_id(run_id) → CostLog`
   - Query cost log by run_id
   - Return CostLog or None

3. `calculate_total_cost(tenant_id, start_date, end_date) → float`
   - Sum all costs for tenant in date range

4. `get_token_usage_stats(tenant_id) → dict`
   - Return total/average input/output tokens

---

### File: `qdrant.py`

**Class:** `QdrantRepository`

**Methods:**

1. `create_collection(collection_name, vector_size=1024)`
   - Create Qdrant collection with dense+sparse vectors if not exists

2. `add_hybrid_documents(collection_name, documents)`
   - Upsert documents with hybrid (dense+sparse) embeddings
   - Deduplication by document ID
   - Only embed new documents to save resources

3. `delete_by_tenant(collection_name, tenant_id)`
   - Delete all documents for tenant

4. `search_hybrid(collection_name, query_vector, query_sparse_vector, tenant_id, top_k)`
   - Perform hybrid search (dense + sparse)
   - Return top_k results with scoring

---

### File: `trakcer_db_file_repositorie.py`

**Class:** `TrackerRepository(db: Session)`

**Methods:**

1. `create_tracker(tenant_id, file_name, file_hash) → TRACKER_DB_FILE`
   - Create new file tracker record with status="processing"

2. `is_processed(tenant_id, file_hash) → bool`
   - Check if file with same hash already processed for tenant

3. `mark_completed(tenant_id, file_hash)`
   - Update status to "completed", set completed_at

4. `mark_failed(tenant_id, file_hash, error_message)`
   - Update status to "failed", log error

---

### File: `invitation_repository.py`

**Class:** `InvitationRepository(db: Session)`

**Methods:**

1. `create_invitation(...) → Invitation`
   - Create new invitation record

2. `get_by_token(token) → Invitation`
   - Query by token

3. `get_pending_for_email(email) → List[Invitation]`
   - Get all pending invitations for email

4. `update_status(invitation_id, status, user_id=None)`
   - Update status and optional user_id

---

## Task Queue (Celery)

### Configuration

**File:** `app/celery/celery_config.py`

**Broker:** RabbitMQ

```python
celery_app = Celery(
    "atlas_ai",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "rpc://")
)
```

**Queues:**

| Queue Name | Routing Key | Purpose |
|-----------|-------------|---------|
| `ingest_data_queue` | "ingest" | File ingestion tasks |
| `eval_data_queue` | "eval" | Evaluation pipeline tasks |
| `logging_queue` | "logging" | Query/cost logging tasks |
| `queue_dead` | "dead" | Dead letter queue for failed tasks |

**Task Routing:**

```python
celery_app.conf.task_routes = {
    "app.services.rag_services.ingest_rag_service.ingest_file_task": {
        "queue": "ingest_data_queue",
        "routing_key": "ingest"
    },
    "app.services.rag_services.eval_pipline.evaluate_task": {
        "queue": "eval_data_queue",
        "routing_key": "eval"
    },
    "app.services.rag_services.query_logging_service.log_query_run_and_cost": {
        "queue": "logging_queue",
        "routing_key": "logging"
    }
}
```

**Worker Settings:**

```python
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Windows compatibility
    worker_pool="threads",
    worker_max_tasks_per_child=10,
    worker_prefetch_multiplier=1,
    
    # Timeouts
    task_soft_time_limit=550,   # Graceful shutdown
    task_time_limit=600,         # Hard kill at 10 min
    
    # Retries
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=30,
    task_max_retries=3,
    
    # Tracking
    task_track_started=True,
    timezone="UTC"
)
```

---

## Authentication & Authorization

### JWT-Based Authentication

**Components:**
1. **Secret Key:** Defined in `app/core/auth.py` from environment variable
2. **Algorithm:** HS256 (HMAC with SHA-256)
3. **Token Expiration:** 60 minutes (configurable)

**Token Flow:**

```
User Login (email + password)
    ↓
[auth_controller.login()]
    ├─ Query user by email
    ├─ Verify password (verify_password)
    ├─ Create JWT token (create_access_token)
    └─ Return token + tenant_id
    
User Stores Token Locally
    ↓
User Makes API Request
    ├─ Include "Authorization: Bearer <token>" header
    
API Route Handler
    ├─ Depends on get_current_user
    ├─ Extract token from header
    ├─ Decode JWT (jwt.decode)
    ├─ Validate expiration
    ├─ Query user from database
    └─ Return User object or raise 401
```

### Role-Based Access Control (RBAC)

**Roles:**
- **admin:** Full access to tenant features (ingestion, user management)
- **user:** Read-only access to tenant data (can query but not ingest)

**Enforcement:**

1. **Ingestion Endpoint:** Checks `user_role == "admin"`
   ```python
   user_role_lower = (user_role or "").lower().strip()
   if user_role_lower != "admin":
       raise HTTPException(status_code=403, detail="Only admins can ingest data")
   ```

2. **Rate Limiting:** Different limits for admin vs user roles

3. **Approval Workflow:** Users can be marked "pending" requiring admin approval before access

---

### Multi-Tenant Data Isolation

**Strategy:** Filter-based isolation at every query

**Implementation:**

1. **Database Level:**
   - All queries include `WHERE tenant_id = <current_tenant>`
   - Foreign key relationships ensure referential integrity

2. **Vector Store Level:**
   - Qdrant retriever includes tenant filter:
     ```python
     filter=models.Filter(
         must=[
             models.FieldCondition(
                 key="payload.tenant_id",
                 match=models.MatchValue(value=tenant_id)
             )
         ]
     )
     ```

3. **Application Level:**
   - Current user's tenant_id passed to all services
   - Services validate tenant ownership before returning data

---

## Frontend

### Overview

**Framework:** React 18 with React Router v6

**File:** `frontend/package.json`

**Dependencies:**
- `react@^18.2.0` - Core React library
- `react-dom@^18.2.0` - React DOM rendering
- `react-router-dom@^6.20.0` - Client-side routing

**Build Tool:** `react-scripts` (Create React App)

**Development Server:** Runs on http://localhost:3000

**CORS Configuration:** FastAPI allows requests from `http://localhost:3000` and `http://127.0.0.1:3000`

### API Integration

**Base URL:** `http://localhost:8000/api`

**Authentication:**
- Stores JWT token in localStorage (`access_token`)
- Sends token as `Authorization: Bearer <token>` header on protected requests

**Headers for Requests:**
```javascript
{
  "Authorization": `Bearer ${localStorage.getItem('access_token')}`,
  "tenant-id": "current_tenant_id",
  "current-user": "current_user_id"
}
```

---

## Deployment & Docker

### Dockerfile Structure

**File:** `Dockerfile`

**Build Strategy:** Multi-stage build (builder + runtime)

**Build Stage:**
1. Base image: `python:3.11-slim`
2. Install build dependencies (gcc, libpq-dev)
3. Install Python packages from requirements.txt
4. Creates compiled packages in /usr/local/lib

**Runtime Stage:**
1. Base image: `python:3.11-slim`
2. Install runtime dependencies (libpq5, curl)
3. Create non-root user (atlas:1000)
4. Copy Python packages from builder stage
5. Copy application code
6. Create directories: /app/logs, /app/data, /app/uploads
7. Set environment variables
8. Expose port 8000
9. Health check: curl http://localhost:8000/health every 30s

**Entrypoint:**
```bash
CMD ["uvicorn", "main:app", 
     "--host", "0.0.0.0",
     "--port", "8000",
     "--workers", "4",
     "--log-config", "logging_setup.py"]
```

---

### Docker Compose

**File:** `docker-compose.yml`

**Services:**

#### 1. **PostgreSQL**
```yaml
postgres:
  image: postgres:15-alpine
  container_name: atlas-postgres
  environment:
    POSTGRES_USER: atlas_user
    POSTGRES_PASSWORD: atlas_secure_password
    POSTGRES_DB: atlas_db
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck: pg_isready check
```

#### 2. **Qdrant Vector Database**
```yaml
qdrant:
  image: qdrant/qdrant:latest
  container_name: atlas-qdrant
  environment:
    QDRANT_API_KEY: atlas_qdrant_key
  ports:
    - "6333:6333"  # REST API
    - "6334:6334"  # gRPC
  volumes:
    - qdrant_data:/qdrant/storage
```

#### 3. **Redis**
```yaml
redis:
  image: redis:7-alpine
  container_name: atlas-redis
  command: redis-server --appendonly yes --requirepass atlas_redis_password
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

#### 4. **FastAPI Application**
```yaml
api:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: atlas-api
  ports:
    - "8000:8000"
  depends_on:
    postgres:
      condition: service_healthy
    qdrant:
      condition: service_healthy
    redis:
      condition: service_healthy
  environment:
    POSTGRES_HOST: postgres
    QDRANT_URL: http://qdrant:6333
    REDIS_HOST: redis
    CELERY_BROKER_URL: amqp://...
```

#### 5. **RabbitMQ (if included)**
```yaml
rabbitmq:
  image: rabbitmq:3.12-alpine
  container_name: atlas-rabbitmq
  ports:
    - "5672:5672"
    - "15672:15672"  # Management UI
  environment:
    RABBITMQ_DEFAULT_USER: guest
    RABBITMQ_DEFAULT_PASS: guest
```

**Networks:** All services on `atlas-network` for inter-service communication

**Volumes:**
- `postgres_data` - PostgreSQL data persistence
- `qdrant_data` - Qdrant data persistence
- `redis_data` - Redis data persistence

**Startup Command:**
```bash
docker-compose up -d
```

---

### Deployment Checklist

1. **Environment Variables:** Create `.env` file with:
   ```
   POSTGRES_USER=atlas_user
   POSTGRES_PASSWORD=<secure_password>
   POSTGRES_DB=atlas_db
   REDIS_PASSWORD=<secure_password>
   SECRET_KEY=<jwt_secret>
   HF_TOKEN_M=<huggingface_token>
   SENTRY_DSN=<sentry_dsn> (optional)
   ```

2. **Database Migrations:** Run Alembic:
   ```bash
   alembic upgrade head
   ```

3. **Secrets Management:** Use environment variables or secrets manager (K8s, AWS Secrets Manager, etc.)

4. **Monitoring:** Set up Prometheus scraping and Grafana dashboards

5. **Logging:** Configure centralized logging (ELK stack, CloudWatch, Datadog)

---

## Monitoring & Observability

### Prometheus Metrics

**Module:** `app/core/monitors.py`

**Metrics Categories:**

#### 1. HTTP Request Metrics
- `atlas_http_requests_total` (Counter) - Total HTTP requests by method/endpoint/status
- `atlas_http_request_duration_seconds` (Histogram) - Request latency
- `atlas_http_request_size_bytes` (Histogram) - Request payload size
- `atlas_http_response_size_bytes` (Histogram) - Response payload size

#### 2. RAG Pipeline Metrics
- `atlas_documents_ingested_total` (Counter) - Total documents processed
- `atlas_document_ingestion_duration_seconds` (Histogram) - Time to ingest document
- `atlas_document_chunks_created` (Histogram) - Chunks per document
- `atlas_duplicate_documents_detected` (Counter) - Duplicate documents skipped
- `atlas_embeddings_generated_total` (Counter) - Total embeddings created
- `atlas_embedding_generation_duration_seconds` (Histogram) - Embedding latency
- `atlas_vector_search_queries_total` (Counter) - Total vector searches

#### 3. Agent Metrics
- `atlas_agent_executions_total` (Counter) - Total agent runs
- `atlas_agent_steps_total` (Counter) - Total steps taken by agents
- `atlas_agent_sql_executions_total` (Counter) - SQL tool invocations
- `atlas_agent_retrieval_executions_total` (Counter) - Retrieval tool invocations

#### 4. Cost Metrics
- `atlas_query_cost_usd_total` (Counter) - Total cost in USD
- `atlas_tokens_used_total` (Counter) - Total tokens consumed
- `atlas_average_query_cost_usd` (Gauge) - Average cost per query

#### 5. Cache Metrics
- `atlas_cache_hits_total` (Counter) - Semantic cache hits
- `atlas_cache_misses_total` (Counter) - Semantic cache misses
- `atlas_cache_hit_ratio` (Gauge) - Cache hit ratio

#### 6. System Metrics
- `atlas_cpu_usage_percent` (Gauge) - CPU usage
- `atlas_memory_usage_percent` (Gauge) - Memory usage
- `atlas_database_connection_pool_size` (Gauge) - Active DB connections

---

### Instrumentator Integration

**File:** `main.py`

**Prometheus FastAPI Instrumentator:**
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose()
```

**Exposes metrics at:** `GET /metrics` (Prometheus format)

---

### MLflow Experiment Tracking

**Module:** `app/services/mlflow_service.py`

**Experiments:**
- `atlas_ingestion` - File ingestion runs
- `atlas_queries` - Query execution runs
- `atlas_agent` - Agent execution runs

**Tracked Parameters:**
- File names, sources, authors
- Query lengths, user IDs
- LLM model names

**Tracked Metrics:**
- Ingestion duration
- Query latency
- Cache hit status
- Token counts
- Costs

**Access:** MLflow UI at http://localhost:5000 (if running locally)

---

### Sentry Error Tracking

**Module:** Configured in `main.py`

**Initialization:**
```python
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0
)

app.add_middleware(SentryAsgiMiddleware)
```

**Captures:**
- Unhandled exceptions
- HTTP 5xx errors
- Performance issues
- Tracing across services

---

### Structured Logging

**Module:** `logging_setup.py`

**Configuration:**
```python
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
```

**Output Format:** JSON (machine-readable)

**Log Levels:** INFO, WARNING, ERROR, DEBUG

**Docker Integration:** Logs printed to stdout captured by Docker logging driver

---

## External Dependencies

### Python Packages

**Framework & Web Server:**
- `fastapi==0.104.1` - Modern async web framework
- `uvicorn[standard]==0.24.0` - ASGI web server
- `python-multipart==0.0.6` - Multipart form data parsing

**Database:**
- `sqlalchemy==2.0.23` - ORM
- `psycopg2-binary==2.9.9` - PostgreSQL adapter
- `alembic` - Database migration tool (implicit in setup)

**Authentication:**
- `python-jose[cryptography]==3.3.0` - JWT handling
- `passlib[bcrypt]==1.7.4` - Password hashing (BCrypt)
- `pydantic==2.5.0` - Data validation

**Vector & RAG:**
- `qdrant-client==1.17.0` - Qdrant client
- `langchain==0.1.1` - LLM framework
- `langgraph==0.0.21` - Agent graph framework
- `sentence-transformers==2.2.2` - Embedding models
- `python-dotenv==1.0.0` - Environment variable management

**Task Queue:**
- `celery==5.3.4` - Distributed task queue
- `redis==5.0.1` - Redis client

**LLM Integration:**
- `openai==1.13.3` - OpenAI API (optional)
- `langchain-openai==0.0.5` - LangChain OpenAI integration

**Monitoring:**
- `prometheus-client==0.19.0` - Prometheus metrics
- `prometheus-fastapi-instrumentator==6.1.0` - FastAPI Prometheus integration
- `sentry-sdk==1.38.0` - Sentry error tracking

**Experiment Tracking:**
- `mlflow==2.10.1` - MLflow tracking

**HTTP:**
- `requests==2.31.0` - Synchronous HTTP client
- `aiohttp==3.9.1` - Async HTTP client
- `httpx==0.25.2` - Modern HTTP client

**Logging:**
- `python-json-logger` (implicitly imported as jsonlogger)

**Development (Optional):**
- `pytest==7.4.3` - Testing framework
- `black==23.12.0` - Code formatter
- `flake8==6.1.0` - Linter

---

### External Services

1. **Hugging Face Inference API**
   - Embedding models: BAAI/bge-m3 (1024-dim embeddings)
   - Authentication: `HF_TOKEN_M` environment variable
   - Usage: Text embedding for RAG indexing

2. **Local/Remote LLM**
   - Default model: Qwen2.5-1.5B-Instruct
   - Access: HuggingFace Inference API
   - Purpose: Answer generation, SQL/retrieval tool operation

3. **PostgreSQL Database**
   - Host: localhost or `postgres` (Docker service name)
   - Port: 5432
   - Database: atlas_db
   - User: atlas_user

4. **Qdrant Vector Database**
   - Host: localhost or `qdrant` (Docker service name)
   - Port: 6333 (REST), 6334 (gRPC)
   - Collection: atlas_documents1
   - Purpose: Hybrid vector search (dense + sparse)

5. **Redis Cache**
   - Host: localhost or `redis` (Docker service name)
   - Port: 6379
   - Purpose: Semantic cache, Celery result backend
   - Auth: Password protected

6. **RabbitMQ Message Broker**
   - Host: localhost or `rabbitmq` (Docker service name)
   - Port: 5672 (AMQP)
   - Purpose: Celery task queue broker

7. **Sentry**
   - Optional error tracking and performance monitoring
   - Configured via `SENTRY_DSN` environment variable

---

## Summary

The Atlas AI Platform is a comprehensive multi-tenant RAG and LLM application that combines:

1. **RAG Pipeline:** Document ingestion with semantic + token-based chunking, hybrid embeddings (dense BGE-M3 + sparse BM25), and Qdrant vector storage
2. **Intelligent Agents:** LangGraph-based reasoning with SQL and retrieval tools, adaptive routing, cost tracking
3. **Multi-Tenancy:** Complete data isolation at database and vector store levels with tenant-scoped querying
4. **Production Ready:** Async task processing (Celery), semantic caching (Redis), comprehensive monitoring (Prometheus, MLflow, Sentry), structured logging (JSON), and Docker containerization
5. **Security:** JWT authentication, role-based access control (RBAC), password hashing (BCrypt), SQL injection prevention
6. **Scalability:** Designed for multi-user, multi-tenant deployment with rate limiting and resource management

---

**End of Documentation**

*Generated: February 28, 2026*
