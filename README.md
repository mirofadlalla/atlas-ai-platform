# Atlas AI Platform - Complete System Documentation

**Version**: 1.0.0  
**Last Updated**: March 2026

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Getting Started](#getting-started)
5. [Core Features](#core-features)
6. [Module Documentation](#module-documentation)
7. [API Endpoints](#api-endpoints)
8. [Monitoring & Observability](#monitoring--observability)
9. [Deployment](#deployment)
10. [Development Workflow](#development-workflow)

---

## 🚀 Overview

**Atlas AI** is a sophisticated multi-tenant SaaS platform that combines Retrieval-Augmented Generation (RAG) with autonomous AI agent reasoning. The system enables organizations to:

- **Build intelligent knowledge bases** through advanced document ingestion and semantic search
- **Execute complex queries** using AI agents that reason, retrieve data, and synthesize answers
- **Scale across tenants** with complete data isolation and role-based access control
- **Monitor performance** through comprehensive observability with Prometheus, Grafana, and Sentry
- **Track costs** with detailed LLM usage metrics and billing analytics

### Key Capabilities

✅ **Intelligent RAG Pipeline**
- Hybrid semantic search (Dense embeddings + BM25 sparse search)
- Cross-encoder reranking for relevance optimization
- 3-tier caching: RAM → Redis → Database for performance

✅ **Autonomous Agent System**
- Multi-step reasoning using LangGraph state machines
- Dynamic question decomposition for complex queries
- SQL query generation with security constraints
- Real-time streaming responses via Server-Sent Events (SSE)

✅ **Multi-tenant Architecture**
- Complete data isolation at every layer
- Tenant-scoped rate limiting and cost tracking
- User invitation & approval workflows
- Role-based access control (RBAC)

✅ **Enterprise Observability**
- Prometheus metrics for all operations
- Grafana dashboards for real-time monitoring
- Sentry error tracking with full context
- Structured JSON logging for container environments
- MLflow integration for experiment tracking

✅ **Async Processing**
- Celery workers for background tasks
- Document ingestion pipeline automation
- Non-blocking metrics collection
- RabbitMQ message broker

---

## 🏗️ Architecture

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                             │
│              Running on http://localhost:3000                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS/WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Main.py)                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Route Handlers (5 Main API Groups)            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ 1. /api/auth/*         → Authentication & Authorization │   │
│  │ 2. /api/agent/*        → Agent Reasoning                │   │
│  │ 3. /api/query/*        → Direct RAG Queries             │   │
│  │ 4. /api/ingest-rag/*   → Document Ingestion             │   │
│  │ 5. /api/eval-rag/*     → Evaluation Pipeline            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Middleware Stack:                                              │
│  ├─ CORS (Origin: localhost:3000)                              │
│  ├─ Prometheus Metrics Instrumentation                         │
│  ├─ Rate Limiting (Tenant-based)                               │
│  ├─ Sentry Error Tracking                                      │
│  └─ Request/Response Logging (JSON format)                     │
└──────┬──────────┬──────────┬──────────┬──────────────────────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
   │Agent   │ │  RAG   │ │  Core  │ │ Services │
   │System  │ │Pipeline│ │Modules │ │          │
   └────────┘ └────────┘ └────────┘ └──────────┘
       │          │          │          │
       └──────────┴──────────┴──────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌──────────┐  ┌───────────┐
│PostgreSQL   │ Qdrant │  │ Redis   │
│(Primary DB) │(Vector │  │ (Cache) │
│             │Search) │  │         │
└─────────┘  └──────────┘  └───────────┘

┌────────────────────────────────────────┐
│   Async Processing (Celery + RabbitMQ) │
├────────────────────────────────────────┤
│ • Document Ingestion                   │
│ • Metrics Collection                   │
│ • Evaluation Tasks                     │
│ • Background Logging                   │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│   Monitoring Stack                     │
├────────────────────────────────────────┤
│ • Prometheus (:9090)                   │
│ • Grafana (:3000)                      │
│ • Sentry (Cloud)                       │
│ • MLflow (:5000)                       │
└────────────────────────────────────────┘
```

### Data Flow Architecture

#### 1. **Document Ingestion Flow**
```
File Upload (PDF/Text)
    ↓
File Hash Calculation (Deduplication)
    ↓
Document Loading & Parsing
    ↓
Semantic Chunking (with timeout fallback)
    ↓
Embedding Generation (Dense + Sparse)
    ├─ Dense: Sentence Transformers (all-MiniLM-L6-v2)
    └─ Sparse: BM25 (FastEmbed)
    ↓
Qdrant Vector Insert (Hybrid Index)
    ↓
Processing Status Tracking (DB)
    ↓
Metrics Logging (Prometheus)
```

#### 2. **Query Retrieval Flow**
```
User Query
    ↓
Redis Semantic Cache Check (Embedding-based)
    ├─ HIT → Return cached result + metrics
    └─ MISS → Continue
    ↓
Qdrant Hybrid Search
    ├─ Dense Search (vector similarity)
    └─ Sparse Search (BM25 text matching)
    ↓
Merge & Rerank Results
    └─ Cross-encoder (ms-marco-MiniLM-L-6-v2)
    ↓
Top-K Selection (reranked chunks)
    ↓
LLM Generation (Context-aware synthesis)
    ↓
Result Caching (Redis + DB)
    ↓
Response to User + Metrics
```

#### 3. **Agent Reasoning Flow**
```
User Question
    ↓
Decompose Node (Question Analysis)
    ├─ Is it compound? → Generate sub-questions
    └─ Generate execution plan
    ↓
Thought Node Loop (for each sub-question)
    ├─ Analyze: Does it need SQL or Retrieval?
    ├─ Decide: Which tool to invoke
    └─ Track: Cost & tokens
    ↓
SQL Node OR Retrieval Node (Parallel)
    ├─ SQL: Generate secure query + execute
    └─ Retrieval: Semantic search via RAG
    ↓
Finish Node (Answer Synthesis)
    ├─ Aggregate results
    └─ Generate final response
    ↓
Stream via SSE (Real-time Updates)
    ↓
Log Everything (Runs DB + Prometheus)
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React + Axios | Web UI & API communication |
| **Backend Framework** | FastAPI 0.104.1 | REST API server |
| **Application Server** | Uvicorn | ASGI server |
| **Agent Orchestration** | LangGraph + LangChain | Multi-step reasoning workflows |
| **LLM Integration** | OpenAI API | Language model access |
| **Vector Search** | Qdrant 1.17.0 | Hybrid semantic search |
| **Embeddings** | Sentence Transformers 2.2.2 | Dense embeddings (all-MiniLM-L6-v2) |
| **Lexical Search** | BM25 (FastEmbedding) | Sparse embeddings for keyword matching |
| **Reranking** | Cross-Encoder (MiniLM-L-6-v2) | Document relevance scoring |
| **Primary Database** | PostgreSQL 13+ | Relational data storage |
| **ORM** | SQLAlchemy 2.0.23 | Database abstraction layer |
| **Cache Layer** | Redis 5.0.1 | Semantic cache + session storage |
| **Message Broker** | RabbitMQ | Celery task queue |
| **Task Queue** | Celery 5.3.4 | Background job processing |
| **Authentication** | JWT + Passlib | Token-based auth + password hashing |
| **Monitoring** | Prometheus 0.19.0 | Metrics collection |
| **Visualization** | Grafana | Dashboard rendering |
| **Error Tracking** | Sentry 1.38.0 | Exception monitoring |
| **Experiment Tracking** | MLflow 2.10.1 | ML experiment logging |
| **Container Orchestration** | Docker Compose | Multi-container deployment |
| **Rate Limiting** | Python built-in | Request throttling per tenant |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Qdrant (vector database)
- RabbitMQ (message broker)
- Docker & Docker Compose (for deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd atlas-ai
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration:
   # - Database credentials
   # - Redis connection details
   # - Qdrant host/port
   # - OpenAI API key
   # - Sentry DSN
   ```

3. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

7. **Start the backend server**
   ```bash
   uvicorn main:app --reload
   ```

8. **Start Celery workers** (in separate terminal)
   ```bash
   celery -A app.celery.celery_config worker --loglevel=info
   ```

9. **Start the frontend** (in separate terminal)
   ```bash
   cd frontend
   npm install
   npm start
   ```

Access the application at http://localhost:3000

### Quick Verification

```bash
# Health check
curl http://localhost:8000/health

# View Prometheus metrics
curl http://localhost:8000/metrics

# Access Grafana dashboards
# Visit http://localhost:3000 (Grafana)

# View Prometheus UI
# Visit http://localhost:9090
```

---

## 💡 Core Features

### 1. Document Ingestion & RAG

- **Hybrid Artifact Chunking**: Semantically intelligent document splitting
- **Deduplication**: Hash-based duplicate detection across uploads
- **Tenant Isolation**: Each tenant's documents completely isolated
- **Multi-format Support**: PDF, TXT, DOCX processing
- **Caching Layer**: 3-tier cache (RAM → Redis → DB) for sub-second queries

**See**: [app/rag/README.md](app/rag/README.md)

### 2. Autonomous Agent System

- **Multi-step Reasoning**: Decompose complex questions into sub-questions
- **Conditional Routing**: Intelligently route to SQL, Retrieval, or Finish nodes
- **Real-time Streaming**: SSE-based response streaming
- **Cost Tracking**: Accurate token/cost accounting per query
- **Telemetry**: Comprehensive logging of agent thought process

**See**: [app/agent/README.md](app/agent/README.md)

### 3. Multi-tenant Architecture

- **Complete Isolation**: Data segregated by `tenant_id` across all tables
- **Rate Limiting**: Per-tenant, role-based throttling
- **User Management**: Invitation system with admin approval workflow
- **Audit Logging**: All operations tracked for compliance

**See**: [app/models/README.md](app/models/README.md)

### 4. Enterprise Observability

- **40+ Prometheus Metrics**: HTTP requests, RAG performance, agent metrics, costs
- **Grafana Dashboards**: Real-time visualization of system health
- **Sentry Integration**: Automatic error tracking with full context
- **Structured Logging**: JSON logs compatible with ELK stacks

**See**: [app/core/README.md](app/core/README.md)

### 5. Async Processing

- **Celery Workers**: Background document processing
- **RabbitMQ Broker**: 4-queue system for task distribution
- **Non-blocking Operations**: Metrics/logging don't impact response times
- **Task Tracking**: Monitor job progress via database

**See**: [app/celery/README.md](app/celery/README.md)

---

## 📁 Module Documentation

Each major module has detailed documentation:

| Layer | Module | Purpose | Key Features |
|-------|--------|---------|--------------|
| **📡 API Layer** | [Routes](app/routes/README.md) | HTTP endpoint handlers | 18+ REST endpoints, JWT auth, rate limiting |
| **🎮 Adapter Layer** | [Controllers](app/controllers/README.md) | Request preprocessing | Input validation, error handling, dependency injection |
| **(Layer 1)** | [Auth Controller](app/controllers/README.md) | Authentication workflows | User registration, login, token refresh |
| | [Ingest Controller](app/controllers/README.md) | Document upload handling | File validation, ingestion queuing |
| **🧠 Business Logic** | [Services](app/services/README.md) | Business orchestration | LLM execution, RAG orchestration, auth workflows |
| **(Layer 2)** | [Agent Service](app/agent/README.md) | Multi-step reasoning | LangGraph 5-node workflow, SSE streaming, cost tracking |
| | [RAG Service](app/rag/README.md) | Document retrieval | Hybrid search, reranking, 3-tier caching |
| | [Auth Service](app/services/README.md) | Authentication logic | JWT tokens, password hashing, approval workflows |
| **💾 Data Access** | [Repositories](app/repositories/README.md) | ORM data persistence | Repository pattern, tenant filtering, pagination |
| **(Layer 3)** | [User/Run/Cost Repositories](app/repositories/README.md) | Domain-specific queries | Aggregation, filtering, isolation |
| **🗄️ Data Model** | [Models](app/models/README.md) | Database schema | Multi-tenant design, 10+ tables with indexes |
| **(Layer 4)** | [SQLAlchemy ORM](app/models/README.md) | Relational mapping | UUID keys, relationships, constraints |
| **⚙️ Infrastructure** | [Core](app/core/README.md) | Config, DB, auth, monitoring | Settings, connection pooling, RBAC, 40+ metrics |
| **(Layer 5)** | [Config](app/core/README.md) | Pydantic settings | Environment variables, validation |
| | [Database](app/core/README.md) | SQLAlchemy engine | Connection pool, session management |
| | [Monitoring](app/core/README.md) | Prometheus client | Custom metrics, middleware instrumentation |
| | [Rate Limiter](app/core/README.md) | Tenant-based throttling | Per-user, per-resource limits |
| **⚡ Async Processing** | [Celery](app/celery/README.md) | Background jobs | 4-queue system, Celery workers, task routing |
| **(Parallel)** | [Task Queue](app/celery/README.md) | Async task execution | Document ingestion, evaluation, logging |
| | [Message Broker](app/celery/README.md) | RabbitMQ integration | Durable queues, dead letter handling |
| **🎨 Design Patterns** | [Patterns](app/design_pattern/README.md) | Reusable solutions | Singleton, Factory, Strategy patterns |
| **(Utilities)** | [Singleton](app/design_pattern/README.md) | Embedding model | Thread-safe global instance, lazy loading |
| | [Factory](app/design_pattern/README.md) | Object creation | User factory, upload factory, strategy selection |

---

### Recommended Reading Order

**For First-Time Contributors:**
1. ✅ Start: [README.md](README.md) (you are here)
2. 📖 Architecture: [System Overview](#architecture)
3. 🔌 API: [Routes](app/routes/README.md) - understand exposed endpoints
4. 🧠 Logic: [Services](app/services/README.md) - business workflows
5. 💾 Data: [Models](app/models/README.md) - database design

**For Feature Development:**
1. 🎯 Choose: Which endpoint/feature?
2. 🔍 Map: Routes → Controllers → Services → Repositories
3. 📚 Read: Relevant module READMEs above
4. 💻 Code: Follow established patterns
5. ✅ Test: Against example in docs

**For Performance Optimization:**
1. 📊 Check: [Monitoring](app/core/README.md) for metrics
2. ⚡ Find: Bottleneck (RAG cache hits? Agent loops?)
3. 🔧 Optimize: 
   - RAG: Improve cache strategy or reranker
   - Agent: Reduce tool invocations or parallel execution
   - DB: Add indexes, optimize queries
4. 📈 Validate: Prometheus dashboard improvements

---

## 🔌 API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/login` | User login with email/password |
| POST | `/api/auth/refresh` | Refresh JWT token |
| GET | `/api/auth/me` | Get current user profile |
| POST | `/api/auth/logout` | Logout |

### Agent Reasoning (`/api/agent`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/agent/reason` | Execute agent reasoning with streaming |
| GET | `/api/agent/runs` | List agent runs (paginated) |
| GET | `/api/agent/runs/{run_id}` | Get specific run with full trace |
| GET | `/api/agent/metrics` | Agent performance metrics |

### Query/RAG (`/api/query`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/query/search` | Direct RAG query without agent |
| GET | `/api/query/cache-stats` | Cache hit/miss statistics |
| DELETE | `/api/query/clear-cache` | Clear semantic cache (admin only) |

### Document Ingestion (`/api/ingest-rag`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ingest-rag/upload` | Upload document(s) for ingestion |
| GET | `/api/ingest-rag/status/{file_id}` | Track ingestion progress |
| DELETE | `/api/ingest-rag/document/{doc_id}` | Delete processed document |
| GET | `/api/ingest-rag/documents` | List ingested documents |

### Evaluation (`/api/eval-rag`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/eval-rag/evaluate` | Run evaluation on queries |
| GET | `/api/eval-rag/results` | Retrieve evaluation results |
| GET | `/api/eval-rag/metrics` | RAG pipeline metrics |

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health status |
| GET | `/metrics` | Prometheus metrics export |

---

## 📊 Monitoring & Observability

### Prometheus Metrics

The system exposes 40+ metrics across multiple categories:

**HTTP Metrics**
- `atlas_http_requests_total` - Total requests by method/endpoint/status
- `atlas_http_request_duration_seconds` - Request latency histogram
- `atlas_http_request_size_bytes` - Request payload size
- `atlas_http_response_size_bytes` - Response payload size

**RAG Metrics**
- `atlas_documents_ingested_total` - Documents processed
- `atlas_document_ingestion_duration_seconds` - Ingestion time
- `atlas_document_chunks_created` - Chunks generated
- `atlas_embedding_requests_total` - Embedding API calls
- `atlas_vector_search_queries_total` - Vector search operations
- `atlas_vector_search_duration_seconds` - Search latency
- `atlas_cache_hits_total` - Cache success count
- `atlas_cache_misses_total` - Cache miss count
- `atlas_reranking_queries_total` - Reranker invocations

**Agent Metrics**
- `atlas_agent_executions_total` - Agent runs
- `atlas_agent_execution_duration_seconds` - Agent latency
- `atlas_agent_thought_count` - Reasoning steps
- `atlas_agent_tool_invocations_total` - Tool usage count

**Cost Metrics**
- `atlas_llm_tokens_used_total` - Token consumption
- `atlas_llm_cost_usd_total` - USD cost tracker
- `atlas_embedding_tokens_used_total` - Embedding tokens

### Dashboards

**Grafana Dashboards** available at http://localhost:3000

1. **System Overview** - HTTP requests, latency, error rates
2. **RAG Performance** - Document ingestion, cache stats, search latency
3. **Agent Reasoning** - Execution times, success rates, cost analysis
4. **Multi-tenant Metrics** - Per-tenant usage and costs
5. **Resource Utilization** - CPU, memory, disk usage

### Error Tracking (Sentry)

All exceptions are automatically sent to Sentry with:
- Full stack traces
- Request context (headers, body, user)
- User identification
- Breadcrumbs for event timeline
- Custom tags for filtering

### Structured Logging

JSON-formatted logs output to stdout for container environments:

```json
{
  "timestamp": "2026-03-05T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.rag.retrivel_data_pipline",
  "message": "Retrieved 15 chunks for query",
  "request_id": "uuid-xxx",
  "tenant_id": 42,
  "duration_ms": 234,
  "cache_hit": true
}
```

---

## 🐳 Deployment

### Docker Compose

The `docker-compose.yml` defines all services:

```yaml
services:
  backend:        # FastAPI application
  frontend:       # React web UI
  postgres:       # Primary database
  qdrant:         # Vector search
  redis:          # Cache & semantic storage
  rabbitmq:       # Message broker
  celery:         # Background workers
  prometheus:     # Metrics collection
  grafana:        # Dashboard visualization
```

**Deploy**:
```bash
docker-compose up -d
docker-compose logs -f backend
```

**Stop**:
```bash
docker-compose down
```

### Production Checklist

- [ ] Enable HTTPS/TLS certificates
- [ ] Configure CORS for production domain
- [ ] Set strong secret keys (JWT, Redis password)
- [ ] Enable PostgreSQL backups (daily)
- [ ] Configure alerts in Grafana
- [ ] Set Sentry to appropriate error threshold
- [ ] Add rate limiting rules for endpoints
- [ ] Enable audit logging for compliance
- [ ] Configure database connection pooling
- [ ] Set up log rotation for JSON logs

---

## 👨‍💻 Development Workflow

### Local Development

1. **Start all services**
   ```bash
   docker-compose up -d
   ```

2. **Start backend in development mode**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Start frontend**
   ```bash
   cd frontend && npm start
   ```

4. **Start Celery worker (optional)**
   ```bash
   celery -A app.celery.celery_config worker --loglevel=debug
   ```

### Code Structure

```
atlas-ai/
├── main.py                    # FastAPI app entry point
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Multi-container setup
├── alembic/                   # Database migrations
│   └── versions/              # Migration files
├── app/
│   ├── __init__.py
│   ├── agent/                 # Agent reasoning system (LangGraph)
│   │   ├── core/              # Graph definition & state
│   │   ├── nodes/             # Decompose, Thought, SQL, Retrieval, Finish
│   │   ├── tools/             # Tool implementations
│   │   └── schemas.py         # Pydantic models
│   ├── rag/                   # RAG pipeline (ingestion & retrieval)
│   │   ├── ingest_data_pipline.py    # Document ingestion
│   │   ├── retrivel_data_pipline.py  # Query retrieval
│   │   ├── reranker.py               # Cross-encoder reranking
│   │   ├── steps/                    # Sub-pipelines
│   │   └── data/                     # Sample data
│   ├── core/                  # Core modules
│   │   ├── config.py          # Settings from .env
│   │   ├── db.py              # Database connection
│   │   ├── auth.py            # JWT & authentication
│   │   ├── monitors.py        # Prometheus metrics
│   │   └── rate_limitizer.py  # Rate limiting
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py, tenant.py, runs.py, etc.
│   │   └── base.py            # Base model class
│   ├── repositories/          # Data access layer
│   │   ├── user_repository.py
│   │   ├── runs_repository.py
│   │   ├── qdrant.py          # Vector search wrapper
│   │   └── ...
│   ├── services/              # Business logic
│   │   ├── rag_services/      # RAG-related
│   │   ├── auth_services/     # Authentication
│   │   └── llm_runner.py      # LLM integration
│   ├── routes/                # API endpoint handlers
│   │   ├── agent_route.py
│   │   ├── query_route.py
│   │   ├── ingest_rag_route.py
│   │   └── ...
│   ├── controllers/           # Request preprocessing
│   ├── design_pattern/        # Singleton/Factory patterns
│   ├── celery/                # Celery task configuration
│   └── files/                 # Upload storage
├── frontend/                  # React application
├── monitoring/               # Prometheus & Grafana config
└── README.md                 # This file
```

### Common Development Tasks

**Run database migration**:
```bash
alembic revision --autogenerate -m "Add new column"
alembic upgrade head
```

**Run tests**:
```bash
pytest app/ -v
```

**Format code**:
```bash
black app/
flake8 app/
```

**View logs**:
```bash
docker-compose logs -f backend
docker-compose logs -f celery
```

**Access database terminal**:
```bash
docker-compose exec postgres psql -U postgres -d atlas_db
```

**Send test request to agent endpoint**:
```bash
curl -X POST http://localhost:8000/api/agent/reason \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the total revenue?"}'
```

---

## 🔐 Security Considerations

- **JWT Tokens**: All authenticated endpoints require valid JWT in `Authorization: Bearer <token>` header
- **Tenant Isolation**: All queries filtered by `tenant_id` automatically
- **Rate Limiting**: Per-tenant rate limits prevent abuse
- **SQL Injection Protection**: LLM-generated SQL is validated and executed with parameter binding
- **CORS**: Only localhost:3000 allowed in development; configure for production
- **Password Hashing**: Bcrypt with salt for all user passwords
- **Environment Variables**: Sensitive config stored in `.env` file (never commit)

---

## 📞 Support & Troubleshooting

### Common Issues

**Q: "ConnectionRefusedError" to PostgreSQL**
- A: Ensure Docker containers are running: `docker-compose ps`
- Run: `docker-compose up -d postgres`

**Q: Cache not working**
- A: Check Redis connection in logs
- Verify `REDIS_URL` setting in `.env`
- Restart Redis: `docker-compose restart redis`

**Q: Agent not responding**
- A: Check Celery worker is running
- View logs: `docker-compose logs celery`
- Ensure LangGraph core module loads: `docker-compose logs backend | grep "LangGraph"`

**Q: High latency on queries**
- A: Check Prometheus metrics dashboard
- Review Qdrant search latency
- Verify reranker is responding
- Check cache hit rate

**Q: Out of memory errors**
- A: Increase Docker container memory limits
- Reduce batch size in ingestion pipeline
- Clear Redis cache: `docker-compose exec redis redis-cli FLUSHDB`

### Useful Debug Commands

```bash
# Check all services running
docker-compose ps

# View detailed logs
docker-compose logs -f --tail=100 backend

# Access database
docker-compose exec postgres psql -U postgres -d atlas_db

# Check Redis cache
docker-compose exec redis redis-cli
> KEYS "*"
> GET <key>

# Test Qdrant connection
curl http://localhost:6333/health

# Verify Prometheus scraping
curl http://localhost:9090/api/v1/targets
```

---

## 📚 Additional Resources

- [System Diagrams](SYSTEM_DIAGRAMS.md) - Visual architecture & data flows
- [RAG Module](app/rag/README.md) - Document ingestion & retrieval details
- [Agent Module](app/agent/README.md) - Reasoning workflow documentation
- [Core Module](app/core/README.md) - Configuration & monitoring setup
- [Database Schema](alembic/versions/) - Migration history & schema
- [API Documentation](http://localhost:8000/docs) - Swagger UI (when running)

---

## 📝 License

[Your License Here]

---

**Last Updated**: March 2026  
**Maintainer**: Atlas AI Team
