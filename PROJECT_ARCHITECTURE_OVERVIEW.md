# Atlas AI Platform - Comprehensive Architecture Overview

**Status**: Production-Ready Multi-Tenant SaaS Application  
**Last Updated**: March 5, 2026  
**Stack**: Python/FastAPI + LangGraph + LLM + RAG + PostgreSQL + Qdrant + Redis + Celery

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [Main Entry Point](#main-entry-point)
5. [Core Modules & Components](#core-modules--components)
6. [Data Flow & Pipelines](#data-flow--pipelines)
7. [Multi-Tenant Architecture](#multi-tenant-architecture)
8. [API Routes & Endpoints](#api-routes--endpoints)
9. [Monitoring & Observability](#monitoring--observability)
10. [Deployment & Infrastructure](#deployment--infrastructure)

---

## Project Overview

**Atlas AI Platform** is a production-grade, multi-tenant SaaS application that combines:

- **Retrieval-Augmented Generation (RAG)**: Answer user questions by retrieving relevant documents and synthesizing responses
- **Intelligent Agent Reasoning**: Multi-step reasoning agent that decomposes complex questions into sub-problems
- **Multi-Tenant Architecture**: Complete tenant isolation with role-based access control
- **Advanced Monitoring**: Prometheus metrics, Grafana dashboards, cost tracking, and Sentry error tracking
- **Workflow Orchestration**: Celery task queues for async processing (document ingestion, RAG evaluation, logging)

**Key Features**:
- ✅ Multi-tenant SaaS registration and management
- ✅ User authentication with email invitations and admin approval workflows
- ✅ Document ingestion with intelligent chunking
- ✅ Hybrid semantic search (dense + sparse embeddings) with cross-encoder reranking
- ✅ Multi-step reasoning agent with SQL and knowledge base access
- ✅ Real-time streaming responses (Server-Sent Events)
- ✅ Cost tracking and billing analytics
- ✅ MLflow experiment tracking
- ✅ Prometheus + Grafana monitoring
- ✅ Sentry error tracking

---

## Technology Stack

### Framework & Runtime
| Component | Technology | Version |
|-----------|-----------|---------|
| **Web Framework** | FastAPI | 0.104.1 |
| **ASGI Server** | Uvicorn | 0.24.0 |
| **Language** | Python | 3.10+ |

### LLM & Agent
| Component | Technology | Version |
|-----------|-----------|---------|
| **Agent Framework** | LangGraph | 0.0.21 |
| **LLM Chain Framework** | LangChain | 0.1.1 |
| **LLM API** | OpenAI | 1.13.3 |
| **Embeddings** | Sentence Transformers | 2.2.2 |

### Databases
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Primary DB** | PostgreSQL | Users, tenants, runs, costs, invitations |
| **Vector DB** | Qdrant | Document embeddings and semantic search |
| **Cache** | Redis | Query caching, semantic cache |
| **ORM** | SQLAlchemy | 2.0.23 |

### Task Queue & Async
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Task Queue** | Celery | Async background jobs |
| **Broker** | RabbitMQ/AMQP | Message broker for Celery |
| **Worker Pool** | Thread-based | Multi-threaded workers |

### Monitoring & Observability
| Component | Technology | Version |
|-----------|-----------|---------|
| **Metrics Collection** | Prometheus Client | 0.19.0 |
| **FastAPI Instrumentation** | prometheus-fastapi-instrumentator | 6.1.0 |
| **Error Tracking** | Sentry SDK | 1.38.0 |
| **Experiment Tracking** | MLflow | 2.10.1 |
| **Logging** | Python JSON Logger | Custom setup |

### Authentication & Security
| Component | Technology | Version |
|-----------|-----------|---------|
| **JWT Tokens** | python-jose | 3.3.0 |
| **Password Hashing** | Passlib + bcrypt | 1.7.4 |
| **Data Validation** | Pydantic | 2.5.0 |

### Development Tools
| Component | Technology | Version |
|-----------|-----------|---------|
| **Testing** | Pytest | 7.4.3 |
| **Code Formatting** | Black | 23.12.0 |
| **Linting** | Flake8 | 6.1.0 |
| **Configuration** | python-dotenv | 1.0.0 |

---

## System Architecture

### High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                        │
│                     (localhost:3000)                             │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼ HTTP REST & SSE
┌──────────────────────────────────────────────────────────────────┐
│                     FASTAPI APPLICATION                          │
│                    (Uvicorn Server)                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               API ROUTES & MIDDLEWARES                   │  │
│  │  • /api/auth         (Authentication & Tenant Mgmt)     │  │
│  │  • /api/ingest-rag   (Document Ingestion)               │  │
│  │  • /api/query        (RAG Query Pipeline)               │  │
│  │  • /api/agent        (Reasoning Agent)                  │  │
│  │  • /api/eval-rag     (RAG Evaluation)                   │  │
│  │                                                          │  │
│  │  MIDDLEWARES:                                            │  │
│  │  • CORS (Frontend allowed origins)                      │  │
│  │  • Rate Limiting (User/Role based)                      │  │
│  │  • Metrics Collection (Prometheus)                      │  │
│  │  • Sentry Error Tracking                                │  │
│  └──────────┬───────┬───────┬────────┬──────────────────┬──┘  │
│             │       │       │        │                  │      │
└─────────────┼───────┼───────┼────────┼──────────────────┼──────┘
              │       │       │        │                  │
    ┌─────────▼─┐ ┌──▼──┐ ┌──▼───┐ ┌─▼─────────┐ ┌───────▼────┐
    │ SERVICES  │ │CORE │ │AGENT │ │ RAG       │ │REPOSITORIES│
    │           │ │     │ │      │ │PIPELINE   │ │            │
    │ • Auth    │ │ DB  │ │Graph │ │• Ingest  │ │ • User     │
    │ • RAG     │ │ Auth│ │Nodes │ │• Retrieve│ │ • Tenant   │
    │ • Tenant  │ │ Rate│ │State │ │• Rerank  │ │ • Runs     │
    │ • Celery  │ │Limit│ │Router│ │• Hybrid  │ │ • Costs    │
    │ • MLflow  │ │Metrs│ │      │ │• Search  │ │ • Invites  │
    │           │ │     │ │      │ │          │ │            │
    └────┬──────┘ └──┬──┘ └──┬───┘ └─┬────────┘ └───────┬────┘
         │           │       │       │                  │
         │           ▼       │       │                  │
         │      ┌────────────────────────────────────┐  │
         │      │   PostgreSQL Database               │  │
         │      │  ┌──────────────────────────────┐  │  │
         │      │  │ • Users & Tenants            │  │  │
         │      │  │ • Runs & Costs (Tracking)    │  │  │
         │      │  │ • Invitations & Approvals    │  │  │
         │      │  │ • Tracker DB Files           │  │  │
         │      │  └──────────────────────────────┘  │  │
         │      └────────────────────────────────────┘  │
         │                                               │
         └─────────────┬──────────────────────────┬──────┘
                       │                          │
                       ▼                          ▼
            ┌──────────────────┐      ┌────────────────────┐
            │ Qdrant Vector DB │      │  Redis Cache       │
            │ (port 6333)      │      │  (port 6379)       │
            │                  │      │                    │
            │• Document chunks │      │• Query cache       │
            │• Dense embeddings│      │• Semantic cache    │
            │• Sparse (BM25)   │      │• Session data      │
            └──────────────────┘      └────────────────────┘
                       │
                       │ Hybrid Search + Reranking
                       │
            ┌──────────▼────────────┐
            │   Ranking Service     │
            │  (Cross-Encoder)      │
            │   + BM25 Lexical      │
            └───────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                  ASYNC TASK QUEUE (Celery)                       │
│                   RabbitMQ Broker (AMQP)                         │
│                                                                  │
│  QUEUES:                                                         │
│  • ingest_data_queue    → Document ingestion tasks              │
│  • eval_data_queue      → RAG evaluation tasks                  │
│  • logging_queue        → Query & agent logging (async)         │
│  • queue_dead           → Failed tasks                          │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│              MONITORING & OBSERVABILITY                          │
│                                                                  │
│  • Prometheus         (Metrics collection & scraping)           │
│  • Grafana            (Dashboards & visualization)              │
│  • Sentry             (Error tracking & alerts)                 │
│  • MLflow             (Experiment tracking)                     │
│  • JSON Logging       (Structured logs to stdout)               │
└──────────────────────────────────────────────────────────────────┘
```

---

## Main Entry Point

### File: [main.py](main.py)

The entry point initializes and configures the FastAPI application with:

1. **Logging Setup** (`setup_logging()`):
   - JSON formatted logging to stdout (for Docker/container logs)
   - Integration with Sentry for error tracking

2. **FastAPI Application**:
   - Title: "Atlas AI Platform"
   - Version: 1.0.0
   - OpenAPI/Swagger documentation enabled

3. **CORS Middleware**:
   - Allows requests from `http://localhost:3000` (frontend)
   - Allows credentials and all HTTP methods

4. **Route Registration**:
   - `/api/auth` - Authentication & tenant registration
   - `/api/ingest-rag` - Document ingestion
   - `/api/query` - RAG query pipeline
   - `/api/agent` - Reasoning agent
   - `/api/eval-rag` - RAG evaluation

5. **Middleware Stack**:
   - **SentryAsgiMiddleware**: Error tracking and reporting
   - **MetricsMiddleware**: HTTP request/response metrics collection
   - **Rate Limiting**: Per-user/role limits

6. **Health Check Endpoint** (`/health`):
   - Used by container orchestration and load balancers
   - Returns: `{"status": "healthy", "service": "Atlas AI Platform", "version": "1.0.0"}`

7. **Prometheus Metrics**:
   - Exposed on `/metrics` endpoint
   - Tracks HTTP requests, system resources, RAG performance, agent metrics
   - Integrated with Grafana for visualization

---

## Core Modules & Components

### 1. **app/core/** - Platform Core Engine

**Purpose**: Foundational services and configuration for the entire platform.

#### Key Files:

| File | Purpose |
|------|---------|
| [config.py](app/core/config.py) | Loads environment variables (API keys, DB URLs, Qdrant, Redis) via Pydantic Settings |
| [db.py](app/core/db.py) | SQLAlchemy base and session management for PostgreSQL |
| [auth.py](app/core/auth.py) | Bearer token validation and user authentication dependency |
| [monitors.py](app/core/monitors.py) | Global Prometheus metrics registry (Counters, Histograms, Gauges) |
| [rate_limitizer.py](app/core/rate_limitizer.py) | Rate limiting by user/role to prevent abuse |

**Architecture**:
- **Pydantic Settings**: Type-safe configuration from `.env`
- **SQLAlchemy ORM**: Declarative base for all models
- **JWT Authentication**: FastAPI dependency injection for token validation
- **Prometheus Integration**: Metrics pushed to collectors

---

### 2. **app/models/** - Database Models

**Purpose**: SQLAlchemy ORM models defining database schema and relationships.

#### Key Models:

| Model | Purpose |
|-------|---------|
| `Users` | Multi-tenant users with roles, approval status, tenant association |
| `Tenants` | Organizations/workspaces with tenant-level isolation |
| `Runs` | Execution logs for RAG queries and agent operations |
| `CostLog` | Track API costs (LLM tokens, vector searches) for billing |
| `TRACKER_DB_FILE` | Metadata for uploaded documents (hash, chunks, status) |
| `Invitations` | Email invitations for user onboarding with admin workflow |

**Multi-Tenant Design**:
- Every user is associated with a `tenant_id`
- All queries filter by `tenant_id` for data isolation
- No cross-tenant data leakage by design

---

### 3. **app/agent/** - Intelligent Reasoning Agent

**Purpose**: Multi-step reasoning agent built with LangGraph that decomposes questions and gathers information from multiple sources.

#### Architecture: State Machine with 5 Nodes

```
decompose → think ↔ (sql_tool | retrieval_tool) → finish → END
             ▲ └─────────────────────────────────┘─────┐
             └───────────────────────────────────────────┘
```

#### Submodules:

**[core/state.py](app/agent/core/state.py)** - Agent State Definition

`AgentState` (TypedDict) tracks:
- `question`: Original user question
- `thought`: Current reasoning step
- `last_action`: Previous action (sql, retrieval, finish)
- `observation`: Results from last tool
- `observation_history`: Complete action history
- `sql_result`, `retrieval_context`: Gathered data
- `sub_questions`, `sub_answers`: For compound questions
- `total_cost`: Accumulated API costs
- `final_answer`: Synthesized result

**[core/graph.py](app/agent/core/graph.py)** - LangGraph Workflow

Defines the state machine:
1. Entry point: `decompose` node
2. Conditional routing from `think` node
3. Tool nodes: `sql_tool`, `retrieval_tool`
4. Finish node with sub-question handling
5. Compiled agent: `agent_app`

**[core/router.py](app/agent/core/router.py)** - Conditional Routing Logic

Routes agent flow based on:
- Question type (SQL vs knowledge base)
- Data availability
- Step limits (max 10 iterations)
- Sub-question completion status

#### Node Breakdown:

**[nodes/decompose_node.py](app/agent/nodes/decompose_node.py)**
- Analyzes user's initial question
- Determines if compound (multi-part) or simple
- Splits compound questions into sub-questions
- Example: "Who registered in Q4 and what are their roles?" → ["Who registered in Q4?", "What are their roles?"]

**[nodes/thought_node.py](app/agent/nodes/thought_node.py)** (Current File: e:\pyDS\atlas-ai\app\agent\nodes\thought_node.py)
- Main decision hub of the agent
- For current active sub-question, decides next action:
  - `sql`: Quantitative/DB queries
  - `retrieval`: Knowledge base lookups
  - `finish`: Question answered, move to next sub-question or finalize
- Uses LLM to reason about action needed
- Logs thoughts to state for transparency

**[nodes/sql_node.py](app/agent/nodes/sql_node.py)**
- Generates SQL queries using LLM
- Enforces tenant-level access (WHERE tenant_id = X)
- Cost-limiting safeguards to prevent expensive queries
- Executes query via SQLAlchemy
- Returns results to observation

**[nodes/retrieval_node.py](app/agent/nodes/retrieval_node.py)**
- Executes semantic search against Qdrant
- Uses hybrid search (dense + sparse embeddings)
- Reranks results with cross-encoder
- Returns top relevant document chunks

**[nodes/finish_node.py](app/agent/nodes/finish_node.py)**
- Compiles data from SQL and retrieval nodes
- Synthesizes final answer using LLM
- For compound questions: answers each sub-question, then aggregates
- Handles multi-step finalization

#### Tools:

**[tools/retrieval.py](app/agent/tools/retrieval.py)**
- Qdrant search wrapper
- Embedding integration

**[tools/sql_engine/](app/agent/tools/sql_engine/)**
- SQL generation and execution
- Query validation
- Tenant isolation enforcement

---

### 4. **app/rag/** - Retrieval-Augmented Generation Pipeline

**Purpose**: Document ingestion and semantic search capabilities with hybrid ranking.

#### Key Components:

**[retrivel_data_pipline.py](app/rag/retrivel_data_pipline.py)** - Query Pipeline

Features:
- **LangChain LCEL**: Composable pipeline using LangChain Expression Language
- **Multi-Layer Caching**:
  - L1: Local RAM cache (`_query_cache`)
  - L2: Redis semantic cache (embeddings-based matching)
  - L3: Database storage (queries logged for analytics)
- **Workflow**:
  1. Embed query (Sentence Transformers)
  2. Qdrant hybrid search (dense + sparse)
  3. Cross-encoder reranking (MiniLM-L-6-v2)
  4. BM25 lexical fallback
  5. Return top-K ranked chunks

**[ingest_data_pipline.py](app/rag/ingest_data_pipline.py)** - Document Ingestion

Pipeline:
1. **File Loading**: PDF, TXT, JSON support
2. **Semantic Chunking**: Intelligent chunking preserving meaning
3. **Embedding**: Dense embeddings (Sentence Transformers) + Sparse (BM25)
4. **Qdrant Loading**: Push embeddings to QdrantVectorStore
5. **Tenant Isolation**: Filter documents by tenant_id

Features:
- **Duplicate Detection**: MD5 hash to skip previously ingested documents
- **Metadata Preservation**: Track source, tenant, document type
- **Async Processing**: Via Celery for large batches

**[reranker.py](app/rag/reranker.py)** - Ranking Service

Two-tier reranking:
1. **Cross-Encoder Reranking**: Using `cross-encoder/ms-marco-MiniLM-L-6-v2`
   - Evaluates relevance of retrieved chunks
   - Boosts exact match chunks
2. **BM25 Fallback**: Lexical relevance for keyword-heavy queries
3. **Hybrid Scoring**: 70% semantic + 30% lexical

#### RAG Architecture Diagram

```
User Query
    ↓
Embedding (HF)
    ↓
Qdrant Hybrid Search
├─ Dense Search (HNSW)
├─ Sparse Search (BM25)
└─ Combine scores
    ↓
Candidate Chunks (Top 10)
    ↓
Cross-Encoder Reranking (MiniLM-L-6-v2)
    ↓
BM25 Lexical Scoring
    ↓
Hybrid Score (70/30 blend)
    ↓
Top-K Ranked Chunks (K=5)
    ↓
Context to LLM
```

---

### 5. **app/services/** - Business Logic Services

**Purpose**: Encapsulate domain-specific logic and external integrations.

#### Key Services:

| Service | Purpose |
|---------|---------|
| `auth_services/auth_service.py` | User authentication and token validation |
| `auth_services/auth_admin_service.py` | Admin user management and approval workflows |
| `invitation_service.py` | Email invitations and user onboarding |
| `tenant_registration_service.py` | SaaS tenant registration (new organizations) |
| `rag_services/ingest_rag_service.py` | Orchestrate document ingestion (async tasks) |
| `rag_services/query_logging_service.py` | Log RAG queries async (cost, latency, results) |
| `rag_services/agent_logging_service.py` | Log agent executions |
| `rag_services/eval_pipline.py` | RAG evaluation framework |
| `mlflow_service.py` | MLflow experiment tracking integration |
| `hash_service.py` | Document deduplication (MD5) |

---

### 6. **app/repositories/** - Data Access Layer

**Purpose**: Abstract database access with repository pattern.

#### Repositories:

| Repository | Purpose |
|------------|---------|
| `user_repository.py` | CRUD operations for users |
| `tenant_repository.py` | Tenant management |
| `runs_repository.py` | Log and query execution runs |
| `cost_log_repository.py` | Track API costs |
| `invitation_repository.py` | Manage invitations |
| `qdrant.py` | QdrantVectorStore operations |
| `trakcer_db_file_repositorie.py` | Document metadata tracking |

---

### 7. **app/routes/** - API Endpoints

**Purpose**: FastAPI routes exposing business logic as HTTP endpoints.

#### Route Files:

| Route | Purpose | Key Endpoints |
|-------|---------|---------------|
| [auth_route.py](app/routes/auth_route.py) | Authentication & tenant management | `/auth/register`, `/auth/login`, `/auth/tenant/register`, `/auth/invitations/*` |
| [query_route.py](app/routes/query_route.py) | RAG query endpoint | `/query/ask` (streaming) |
| [agent_route.py](app/routes/agent_route.py) | Agent reasoning endpoint | `/agent/ask-agent` (SSE streaming) |
| [ingest_rag_route.py](app/routes/ingest_rag_route.py) | Document ingestion | `/ingest-rag/upload`, `/ingest-rag/ingest-file` |
| [eval_pipline.py](app/routes/eval_pipline.py) | RAG evaluation | `/eval-rag/evaluate` |

**Response Format**: All endpoints support streaming via Server-Sent Events (SSE) for real-time updates.

---

### 8. **app/design_pattern/** - Design Patterns

**Purpose**: Implement common design patterns for flexibility and reusability.

#### Patterns:

| Pattern | File | Purpose |
|---------|------|---------|
| Singleton | `llm_singlton.py` | Single LLM instance (currently commented out - using OpenAI API) |
| Factory | `upload_factory.py` | Create upload handlers for different file types |
| Factory | `user_factory.py` | Create user objects |
| Embedded Model | `embedded_model.py` | Manage sentence-transformer embeddings |

---

### 9. **app/celery/** - Async Task Queue

**Purpose**: Background job processing for long-running operations.

#### Configuration: [celery_config.py](app/celery/celery_config.py)

```
Broker: RabbitMQ (AMQP)
Backend: RPC (RabbitMQ)
Queues:
  • ingest_data_queue     → Document ingestion
  • eval_data_queue       → RAG evaluation
  • logging_queue         → Async logging (default)
  • queue_dead            → Failed tasks
```

**Features**:
- Thread-based worker pool (Windows compatible)
- JSON serialization
- Auto-retry on failure (max 3 retries)
- Task time limits (10 minutes max)
- Soft limit: 9m 10s

---

## Data Flow & Pipelines

### Pipeline 1: Document Ingestion

```
User Upload File
    ↓
API: POST /ingest-rag/upload
    ↓
Hash Check (Deduplication)
├─ Already ingested? → Return cached chunks
└─ New file? → Continue
    ↓
Load Document (PDF/TXT parser)
    ↓
Semantic Chunking
├─ Token-level split (2000 tokens, 50 overlap)
└─ Preserve semantic meaning
    ↓
Generate Embeddings
├─ Dense: Sentence Transformers
└─ Sparse: BM25
    ↓
Upsert to Qdrant
├─ Tenant namespace isolation
├─ Metadata: source, doc_id, chunk_idx
└─ Store embeddings
    ↓
Log Metadata (PostgreSQL)
├─ Document tracker record
├─ Chunk count
└─ Embedding status
    ↓
**Celery Task** (Async Logging)
    ↓
Return: Chunk count, embedding status to client
```

### Pipeline 2: RAG Query

```
User Query
    ↓
API: POST /query/ask
    ↓
Rate Limit Check
├─ User role quota
└─ Endpoint limits
    ↓
MLflow Experiment Start
├─ Create run for tracking
└─ Tag with tenant_id, user_id
    ↓
Cache Lookup (3-tier)
├─ L1 RAM? → Hit → Skip to Answer
├─ L2 Redis? → Semantic match → Use cached
└─ L3 DB? → Log reference
    ↓
Retrieval Pipeline
├─ Embed query
├─ Qdrant hybrid search
├─ Cross-encoder rerank
└─ Top-K chunks
    ↓
LLM Answer Generation
├─ Prompt + Context
├─ Token count → Cost
└─ Stream response
    ↓
**Celery Task** (Async Logging - runs in background)
├─ Log query to database
├─ Record latency
├─ Save cost
├─ Push to Prometheus
└─ Update MLflow
    ↓
Response to Client (StreamingResponse)
```

### Pipeline 3: Agent Reasoning

```
User Question
    ↓
API: POST /agent/ask-agent
    ↓
Start Agent Graph (LangGraph)
    ↓
Node 1: DECOMPOSE
├─ Analyze question complexity
├─ Create sub-questions if compound
└─ Update state.sub_questions
    ↓
Node 2: THINK (Reasoning Loop)
├─ Analyze current sub-question
├─ Decide action: sql | retrieval | finish
├─ LLM reasoning
└─ Update state.thought
    ↓
Router → Action Decision
├─ SQL: Quantitative data needed
├─ Retrieval: Knowledge base needed
└─ Finish: Question resolved
    ↓
Conditional Node Execution
│
├─ SQL Node
│  ├─ Generate SQL query
│  ├─ Validate & enforce tenant isolation
│  ├─ Execute query
│  └─ Return results
│
├─ Retrieval Node
│  ├─ Semantic search
│  ├─ Cross-encoder reranking
│  └─ Return top chunks
│
└─ Finish Node
   ├─ Synthesize answer from observations
   ├─ For compound Qs: aggregate sub-answers
   └─ Update state.final_answer
    ↓
Router → Continue or End?
├─ More sub-questions? → Back to THINK
└─ All done? → END
    ↓
Stream SSE to Client
├─ tool_start events
├─ thought events
├─ answer event
└─ complete event
    ↓
**Celery Task** (Async Logging)
├─ Log agent execution
├─ Record steps, costs, latency
└─ Push metrics
```

---

## Multi-Tenant Architecture

### Tenant Isolation Strategy

**1. Data Isolation**:
- Every user record has `tenant_id`
- Every document in Qdrant tagged with `tenant_id`
- All queries filter: `WHERE tenant_id = current_tenant`
- RAG retrieval: `Filter by tenant in Qdrant search`

**2. Authentication**:
- User registration → Create tenant + admin user
- Tenant invitation workflow → Users join existing tenants
- JWT token includes `tenant_id`
- Headers require `tenant-id` for all requests

**3. Authorization**:
- Roles: `admin`, `user`
- Admin approval workflow for new users
- Role-based rate limiting

**4. Cost Tracking**:
- Per-tenant cost logging
- Billing by tenant

### Multi-Tenant Database Schema

```
Tenants (Top-level organizations)
├─ id (UUID)
├─ name
├─ created_at
└─ admin_user_id

Users (Scoped to Tenant)
├─ id (UUID)
├─ tenant_id (FK → Tenants)
├─ email
├─ role (admin | user)
├─ approval_status (pending | approved | rejected)
└─ hashed_password

Invitations
├─ id
├─ tenant_id
├─ invited_email
├─ status (pending | accepted)
└─ created_at

Runs (Query & Agent Executions)
├─ id
├─ tenant_id
├─ user_id
├─ query/agent data
└─ timestamp

CostLog
├─ id
├─ tenant_id
├─ user_id
├─ cost_amount
├─ type (llm_tokens | vector_search)
└─ timestamp

QdrantVectorDB
├─ Collections by tenant (tenant_123_documents)
├─ Each chunk tagged: {"tenant_id": "123"}
└─ Filter at query time
```

---

## API Routes & Endpoints

### Authentication Routes (`/api/auth`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/tenant/register` | Register new organization (SaaS) |
| POST | `/auth/register` | Register new user (existing tenant) |
| POST | `/auth/login` | Login and get JWT token |
| POST | `/auth/invitations/send` | Admin sends user invitation |
| POST | `/auth/invitations/validate` | Validate invitation token |
| POST | `/auth/invitations/register` | User registers via invitation |
| GET | `/auth/invitations/pending` | List pending invitations (admin) |
| POST | `/auth/invitations/resend` | Resend invitation email |

**Authentication**: Bearer token in `Authorization` header

---

### RAG Routes (`/api/query`)

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| POST | `/query/ask` | Answer query via RAG | StreamingResponse (SSE) |

**Request**:
```json
{
  "question": "What are the main benefits of RAG?"
}
```

**Response** (Streaming):
```
event: answer
data: "The main benefits of RAG include..."

event: complete
data: {"status": "success"}
```

**Headers Required**:
- `Authorization: Bearer <token>`
- `tenant-id: <tenant_id>`
- `current-user: <user_id>`

---

### Agent Routes (`/api/agent`)

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| POST | `/agent/ask-agent` | Multi-step reasoning | StreamingResponse (SSE) |

**Request**:
```json
{
  "question": "How many users registered in Q4 and what are their roles?"
}
```

**Response** (Streaming):
```
event: tool_start
data: {"tool": "think"}

event: thought
data: "Analyzing the question... this requires two steps: user count and role analysis"

event: tool_start
data: {"tool": "sql"}

event: tool_end
data: {"result": "SQL executed: found 15 users"}

event: answer
data: "In Q4, 15 users registered with the following roles: 10 standard users, 5 admins"

event: complete
data: {"status": "success", "steps": 4, "cost": 0.025}
```

**Headers Required**: Same as RAG routes

---

### Document Ingestion Routes (`/api/ingest-rag`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/ingest-rag/upload` | Upload document file |
| POST | `/ingest-rag/ingest-file` | Ingest file to RAG |

**Async Processing**: Celery workers process documents in background

---

### RAG Evaluation Routes (`/api/eval-rag`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/eval-rag/evaluate` | Evaluate RAG system performance |

**Metrics Tracked**: Precision, recall, MRR, NDCG

---

### Health & Monitoring Routes

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check (liveness probe) |
| GET | `/metrics` | Prometheus metrics |

---

## Monitoring & Observability

### 1. Prometheus Metrics

**Exposed on**: `GET /metrics`

**Metrics Collected**:

| Metric | Type | Purpose |
|--------|------|---------|
| `http_requests_total` | Counter | Total HTTP requests by method, endpoint, status |
| `http_request_duration_seconds` | Histogram | Request latency |
| `http_response_size_bytes` | Histogram | Response payload size |
| `llm_tokens_total` | Counter | Total tokens consumed |
| `llm_cost_total` | Counter | Total API costs |
| `vector_search_duration_seconds` | Histogram | Qdrant search latency |
| `reranking_duration_seconds` | Histogram | Cross-encoder reranking time |
| `retrieved_chunks_count` | Gauge | Number of chunks retrieved |
| `agent_steps_count` | Counter | Agent reasoning steps |
| `agent_execution_duration_seconds` | Histogram | Total agent execution time |

### 2. Grafana Dashboards

**Monitored via**: Prometheus + Grafana (docker-compose)

**Dashboards**:
- HTTP Request Metrics
- RAG Performance (latency, chunk count, reranking time)
- Agent Reasoning (step count, execution time)
- Cost Analytics (by tenant, by query type)
- System Resources (CPU, memory)

---

### 3. Sentry Error Tracking

**Configuration**: Environment variable `SENTRY_DSN`

**Tracks**:
- Uncaught exceptions
- HTTP error responses
- Database errors
- Service integration failures

**Features**:
- Error grouping by type
- Stack trace capture
- User/tenant context
- Automatic release tracking

---

### 4. MLflow Experiment Tracking

**Purpose**: Track query and agent runs for analysis

**Logged Data**:
- Query text and response
- Latency
- Tokens consumed
- Cost
- Retrieved chunk count
- Agent steps

**Stored in**: `mlruns/` directory (default local backend)

---

### 5. JSON Structured Logging

**Configuration**: [logging_setup.py](logging_setup.py)

**Format**: JSON to stdout (Docker-friendly)

Example log:
```json
{
  "timestamp": "2026-03-05T10:30:45Z",
  "level": "INFO",
  "message": "Agent executed successfully",
  "tenant_id": "abc123",
  "user_id": "user456",
  "steps": 4,
  "cost": 0.025
}
```

---

## Deployment & Infrastructure

### Docker Compose Services

**Main Stack** (`docker-compose.yml`):
```yaml
services:
  fastapi:        # Main application
  postgres:       # Primary database
  redis:          # Cache
  qdrant:         # Vector database
  rabbitmq:       # Celery broker
  celery-worker:  # Async task workers
```

**Monitoring Stack** (`docker-compose.monitoring.yml`):
```yaml
services:
  prometheus:     # Metrics collection
  grafana:        # Dashboards
```

### Environment Configuration

**Key Environment Variables** (`.env`):
```
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/atlas_ai
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333

# API Keys
OPENAI_API_KEY=sk-...
SENTRY_DSN=https://...

# Celery
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=rpc://

# Frontend CORS
FRONTEND_URL=http://localhost:3000
```

### Database Migrations

**Tool**: Alembic (SQLAlchemy migrations)

**Versions** (`alembic/versions/`):
- Initial schema creation
- User & tenant tables
- Runs and cost logging
- Invitations workflow
- Document tracking

**Run migrations**:
```bash
alembic upgrade head
```

---

## Key Design Decisions

1. **LangGraph for Orchestration**: Flexible agent architecture with clear node-based workflow
2. **Hybrid Search (Dense + Sparse)**: Better recall than dense-only, better precision than sparse-only
3. **Cross-Encoder Reranking**: Improves relevance of retrieved documents
4. **Async Logging**: Non-blocking cost/metrics tracking via Celery
5. **Multi-Tier Caching**: RAM → Redis → DB for optimal query performance
6. **Server-Sent Events (SSE)**: Real-time streaming of agent reasoning and answers
7. **Multi-Tenant by Default**: Every data access enforced with tenant filtering
8. **Singleton LLM**: Efficient token usage (currently OpenAI API)
9. **Repository Pattern**: Clean separation of data access logic
10. **Prometheus + Grafana**: Production-grade observability

---

## Development Workflow

### Starting the Application

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with actual keys

# 3. Start Docker services
docker-compose up -d

# 4. Run migrations
alembic upgrade head

# 5. Start FastAPI server
uvicorn main:app --reload

# 6. (Optional) Start Celery workers
celery -A app.celery.celery_config worker -l info

# 7. Access services
# - Frontend: http://localhost:3000
# - API Docs: http://localhost:8000/docs
# - Grafana: http://localhost:3000
```

### Testing

```bash
pytest              # Run all tests
pytest -v           # Verbose
pytest tests/test_agent.py  # Specific test file
```

### Code Quality

```bash
black app/          # Format code
flake8 app/         # Lint
isort app/          # Sort imports
```

---

## Summary

**Atlas AI Platform** is a sophisticated, production-ready multi-tenant SaaS application that combines:

- **RAG**: Document ingestion + semantic search for knowledge base Q&A
- **Agent Reasoning**: Multi-step decomposition and problem solving via LangGraph
- **Multi-Tenant SaaS**: Complete tenant isolation, user management, invitations, approval workflows
- **Advanced Monitoring**: Prometheus metrics, Grafana dashboards, Sentry error tracking, MLflow experiments
- **Scalable Architecture**: Async task queues, streaming responses, cost tracking, rate limiting

The codebase is well-modularized with clear separation of concerns:
- **Routes** → **Services** → **Repositories** → **Database/External Services**
- **Core** → Platform services (auth, config, monitoring)
- **Agent** → State machine reasoning with tool execution
- **RAG** → Document ingestion and retrieval pipeline
- **Models** → Database schema

This architecture supports rapid feature development, easy testing, and production-grade deployment.

---

**Documentation Generated**: March 5, 2026  
**Next Steps**: Deploy to production, configure monitoring, scale Celery workers
