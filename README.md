# Atlas AI - Multi-Tenant RAG & Agent Platform

## Table of Contents
1. [Project Overview](#project-overview)
2. [Problem Statement & Solution](#problem-statement--solution)
3. [Architecture](#architecture)
4. [Key Features](#key-features)
5. [Technology Stack](#technology-stack)
6. [System Components](#system-components)
7. [Monitoring & Observability](#monitoring--observability)
8. [Metrics Flow](#metrics-flow)
9. [Getting Started](#getting-started)
10. [API Documentation](#api-documentation)
11. [Frontend Analytics](#frontend-analytics)
12. [Dashboard Access](#dashboard-access)
13. [Cost Tracking](#cost-tracking)
14. [Troubleshooting](#troubleshooting)

---

## Project Overview

**Atlas AI** is a comprehensive multi-tenant Retrieval-Augmented Generation (RAG) and AI Agent platform designed to enable organizations to build intelligent applications on top of their proprietary data.

### What is RAG?

Retrieval-Augmented Generation (RAG) combines the power of large language models (LLMs) with retrieval systems to:
- Answer questions grounded in your documents
- Reduce hallucinations by referencing actual data
- Enable knowledge base queries with AI understanding
- Provide cost-effective inference compared to fine-tuning

### What are AI Agents?

AI Agents are autonomous systems that can:
- Reason about complex problems
- Execute multiple tools/actions in sequence
- Retrieve both structured (SQL) and unstructured (documents) data
- Synthesize final answers from multiple information sources
- Think through multi-step problems autonomously

---

## Problem Statement & Solution

### The Problem

Organizations struggle with:
1. **Scattered Knowledge**: Knowledge exists in documents, databases, and systems
2. **Limited Context**: LLMs lack access to proprietary data without fine-tuning
3. **Cost**: Fine-tuning and maintaining custom models is expensive
4. **Multi-Tenancy**: Supporting multiple organizations while isolating data
5. **Observability**: No visibility into RAG/Agent performance, costs, and quality
6. **Scalability**: Hard to scale document ingestion and query processing

### The Solution: Atlas AI

Atlas AI addresses these challenges with:

1. **Unified Knowledge Base**: 
   - Ingest documents (PDF, DOCX, TXT)
   - Store embeddings in Qdrant vector database
   - Retrieve semantically similar chunks for context

2. **RAG Pipeline**:
   - Retrieve relevant documents from vector DB
   - Re-rank results for better relevance
   - Generate answers using retrieved context
   - Automatic cost and latency tracking

3. **AI Agents**:
   - Multi-step reasoning engine
   - SQL query execution for structured data
   - Document retrieval for unstructured data
   - Self-contained reasoning thread

4. **Multi-Tenant Architecture**:
   - Isolated data per tenant
   - Per-tenant metrics and analytics
   - Separate knowledge bases
   - Role-based access control

5. **Complete Observability**:
   - Real-time metrics via Prometheus
   - Historical analysis via MLflow
   - Admin dashboards in Grafana
   - Cost tracking and analytics

6. **Scalability**:
   - Async task processing via Celery
   - Redis caching for performance
   - Connection pooling for databases
   - Distributed request processing

---

## Architecture

### System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  - Dashboard  - Analytics  - Document Ingestion  - Query UI   │
└──────────────────────────┬─────────────────────────────────────┘
                           │ HTTPS/CORS
┌──────────────────────────┴─────────────────────────────────────┐
│                    FastAPI Backend (8000)                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              API Routes                                  │  │
│  │  - /auth (Authentication & Authorization)               │  │
│  │  - /query/ask (RAG Query Endpoint)                       │  │
│  │  - /agent/ask-agent (Agent Reasoning Endpoint)          │  │
│  │  - /ingest (Document Ingestion)                         │  │
│  │  - /metrics (Prometheus Metrics Endpoint)               │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │           Core Services                                  │  │
│  │  - RAG Pipeline (retrieval + generation)                │  │
│  │  - Agent Engine (reasoning + tool use)                  │  │
│  │  - Embedding Service                                    │  │
│  │  - Reranking Service                                    │  │
│  │  - Cost Calculation                                     │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────┬──────────────────────────────┬──────────────────┘
             │                              │
       ┌─────┴──────┐             ┌────────┴────────┐
       │             │             │                 │
   ┌───▼────┐   ┌──▼────┐   ┌───▼────┐   ┌───────▼──┐
   │PostgreSQL  │ Qdrant │   │ Redis  │   │ Celery  │
   │(Metadata)  │(Vectors)  │(Cache) │   │(Tasks)  │
   └───────┘   └───────┘   └────────┘   └────────┘

   Monitoring & Observability:
   ┌───────────────┐  ┌──────────────┐  ┌──────────┐
   │ Prometheus    │  │ Grafana      │  │ MLflow   │
   │(Metrics DB)   │  │(Dashboards)  │  │Analytics │
   └───────────────┘  └──────────────┘  └──────────┘
```

### Data Flow for Query Processing

```
User Query 
    │
    ▼
┌─────────────────────────────────┐
│ 1. Retrieve Documents           │
│  - Vector similarity search      │
│  - Semantic cache lookup         │
│  - Return top-k chunks          │
└──────────────┬──────────────────┘
               │
               ▼
         ┌─────────────────────┐
         │ 2. Rerank Results   │
         │  - Cross-encoder    │
         │  - BM25 scoring     │
         │  - Hybrid approach  │
         └──────────┬──────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │ 3. Generate Answer       │
         │  - LLM with context      │
         │  - Temperature control   │
         │  - Token tracking        │
         └──────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │ 4. Log & Track Metrics   │
         │  - Save to database      │
         │  - Record to Prometheus  │
         │  - Calculate costs       │
         └──────────────────────────┘
```

---

## Key Features

### 1. **Multi-Tenant RAG**
- Separate knowledge bases per tenant
- Document ingestion with chunking
- Vector embeddings with semantic search
- Configurable token limits and costs
- Stream-based responses for low latency

### 2. **AI Agents with Reasoning**
- Multi-step reasoning engine
- Tool integration (SQL queries, document retrieval)
- Thought streaming for transparency
- Error recovery and retry logic
- Configurable reasoning depth

### 3. **Advanced Retrieval**
- Semantic cache for redundant queries
- Multiple reranking strategies
- Hybrid search (semantic + keyword)
- Document metadata filtering
- Duplicate detection

### 4. **Cost & Token Tracking**
- Per-query cost calculation
- Model-specific pricing
- Tenant-level cost aggregation
- Token usage analytics
- Monthly billing summaries

### 5. **Real-Time Monitoring**
- Prometheus metrics exposure
- 50+ custom metrics
- System resource tracking
- Request latency histograms
- Error rate monitoring

### 6. **Comprehensive Analytics**
- MLflow experiment tracking
- Query performance analysis
- Cost trend visualization
- Success rate tracking
- Cache hit rate monitoring

### 7. **Security & Access Control**
- JWT authentication
- Role-based permissions (user, admin, super-admin)
- Tenant isolation
- Approval workflow for new users
- Secure password hashing

### 8. **Scalability**
- Async task processing with Celery
- Connection pooling
- Redis caching
- Load balancing ready
- Horizontal scaling support

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python) - Modern async web framework
- **Database**: PostgreSQL - Relational data (metadata, users, runs, costs)
- **Vector DB**: Qdrant - Vector similarity search for embeddings
- **Cache**: Redis - Caching and Celery message broker
- **Task Queue**: Celery - Async task processing
- **LLM**: Qwen 2.5 (1.5B) - Local language model
- **Embeddings**: All-MiniLM-l6-v2 - Sentence embeddings

### Monitoring & Observability
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **MLflow**: Experiment tracking and analytics
- **Sentry**: Error tracking and logging

### Frontend
- **Framework**: React - Interactive UI
- **Styling**: CSS - Custom design
- **HTTP Client**: Fetch API - API communication

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Server**: Uvicorn - ASGI server for FastAPI

---

## System Components

### 1. **Authentication Service** (`app/core/auth.py`)
- User login/registration
- JWT token generation
- Role-based access control
- Tenant isolation

### 2. **RAG Pipeline** (`app/rag/retrivel_data_pipline.py`)
- **Retrieval**: Vector similarity search
- **Reranking**: Multiple strategies
- **Generation**: LLM-based answer synthesis
- **Caching**: Semantic cache with Redis

**Key Methods**:
```python
pipeline = RetrievalPipeline(tenant_id=123)
answer = pipeline.ask_stream(query="What is...?")  # Generator
documents = pipeline.retrieve(query="...")
```

### 3. **Agent Engine** (`app/agent/core/graph.py`)
- **Reasoning**: Multi-step thought process
- **Tool Use**: SQL + Document Retrieval
- **Synthesis**: Final answer generation
- **State Management**: Maintains context

**Supported Tools**:
- SQL Executor: Execute queries on tenant databases
- Document Retriever: Search knowledge base
- Calculator: Mathematical operations

### 4. **Embedding Service** (`app/design_pattern/embedded_model.py`)
- **Model**: All-MiniLM-l6-v2 sentence transformer
- **Singleton Pattern**: Single instance across app
- **Batch Processing**: Efficient batch embedding

### 5. **Reranking Service** (`app/rag/reranker.py`)
- **Cross-Encoder**: Neural re-ranking
- **BM25**: Keyword-based ranking
- **Hybrid**: Combination of both

### 6. **Cost Tracking** (`app/repositories/cost_log_repository.py`)
- Per-query cost calculation
- Token-based pricing
- Model-specific rates
- Tenant aggregation

### 7. **Monitoring** (`app/core/monitors.py`)
- **System Metrics**: CPU, memory, disk, network
- **Application Metrics**: HTTP requests, latency, errors
- **RAG Metrics**: Retrieval latency, token usage, cache hits
- **Agent Metrics**: Reasoning steps, decision time, tool calls

### 8. **Background Tasks** (`app/services/rag_services/`)
- **Query Logging**: Asynchronous logging of query runs
- **Agent Logging**: Asynchronous logging of agent executions
- **Cost Persistence**: Database storage of cost records

---

## Monitoring & Observability

### Metrics Collection Architecture

```
┌─────────────────────────────────────┐
│  Application Code                   │
│  ├─ Query Routes                    │
│  ├─ Agent Routes                    │
│  └─ Logging Services                │
└──────────────────┬──────────────────┘
                   │ Records metrics
                   ▼
┌──────────────────────────────────────┐
│  Prometheus Client Library           │
│  ├─ Counters (totals)                │
│  ├─ Histograms (distributions)       │
│  ├─ Gauges (instantaneous values)    │
│  └─ Summaries (percentiles)          │
└──────────────────┬───────────────────┘
                   │ Exposes via /metrics
                   ▼
┌──────────────────────────────────────┐
│  Prometheus Server                   │
│  ├─ Scrapes /metrics every 10s       │
│  ├─ Time-series database             │
│  ├─ Data retention: 15 days          │
│  └─ PromQL query evaluation          │
└──────────────────┬───────────────────┘
                   │ Queries for visualization
                   ▼
┌──────────────────────────────────────┐
│  Grafana Dashboards                  │
│  ├─ System Health Monitor             │
│  ├─ RAG Performance Metrics           │
│  ├─ Cost Analytics                    │
│  └─ Request Latency Breakdown         │
└──────────────────────────────────────┘
```

### Available Metrics

#### 1. **HTTP Request Metrics**
- `atlas_http_requests_total` - Count of HTTP requests by method, endpoint, status
- `atlas_http_request_duration_seconds` - Request latency distribution
- `atlas_http_request_size_bytes` - Request payload sizes
- `atlas_http_response_size_bytes` - Response payload sizes

#### 2. **RAG Pipeline Metrics**
- `atlas_documents_ingested_total` - Documents added to knowledge base
- `atlas_document_ingestion_duration_seconds` - Time to ingest documents
- `atlas_embeddings_generated_total` - Embeddings created
- `atlas_vector_search_queries_total` - Vector search operations
- `atlas_vector_search_duration_seconds` - Search latency
- `atlas_retrieved_chunks_count` - Documents retrieved per query
- `atlas_reranking_queries_total` - Re-ranking operations
- `atlas_reranking_duration_seconds` - Re-ranking latency

#### 3. **LLM & Token Metrics**
- `atlas_llm_queries_total` - LLM calls made
- `atlas_llm_query_duration_seconds` - LLM response time
- `atlas_llm_tokens_consumed` - Input + output tokens
- `atlas_llm_tokens_generated` - Output tokens only

#### 4. **Agent Metrics**
- `atlas_agent_queries_total` - Agent queries processed
- `atlas_agent_reasoning_steps_count` - Number of reasoning steps
- `atlas_agent_reasoning_duration_seconds` - Time spent reasoning
- `atlas_agent_tool_calls_total` - Tool invocations
- `atlas_agent_decision_duration_seconds` - Decision time

#### 5. **Cost Metrics**
- `atlas_api_calls_cost_total` - Total API costs in USD
- `atlas_tokens_cost_total` - Token-based costs
- `atlas_cost_per_query` - Query cost distribution
- `atlas_tenant_monthly_cost` - Per-tenant monthly costs

#### 6. **Cache Metrics**
- `atlas_cache_hits_total` - Successful cache retrievals
- `atlas_cache_misses_total` - Cache misses
- `atlas_cache_size_bytes` - Current cache size

#### 7. **System Metrics**
- `atlas_system_cpu_usage_percent` - System CPU utilization
- `atlas_system_memory_usage_percent` - RAM usage
- `atlas_system_disk_usage_percent` - Disk usage
- `atlas_process_cpu_usage_percent` - Process CPU usage
- `atlas_process_memory_usage_mb` - Process RAM usage
- `network_io_bytes_sent` - Network bytes transmitted
- `network_io_bytes_received` - Network bytes received

#### 8. **Database Metrics**
- `atlas_database_connection_pool_size` - Active connections
- `atlas_database_query_duration_seconds` - Query latency
- `atlas_database_errors_total` - Failed queries

#### 9. **Error Metrics**
- `atlas_application_errors_total` - Application errors by type
- `atlas_exceptions_total` - Exception counts by type

#### 10. **Authentication Metrics**
- `atlas_authentication_attempts_total` - Auth attempts (success/failure)
- `atlas_authentication_duration_seconds` - Auth latency
- `atlas_active_user_sessions` - Current sessions
- `atlas_invalid_token_attempts` - Invalid token attempts

---

## Metrics Flow

### How Metrics are Recorded

#### 1. **Automatic Collection via Middleware**
```python
# In main.py - MetricsMiddleware
┌─────────────────────────────────────┐
│ HTTP Request arrives                │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ MetricsMiddleware.dispatch()        │
│  - Records start time               │
│  - Processes request                │
│  - Measures duration                │
│  - Records response size            │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Prometheus Metrics Updated          │
│  - http_requests_total.inc()        │
│  - http_request_duration.observe()  │
│  - http_response_size.observe()     │
└─────────────────────────────────────┘
```

#### 2. **Manual Collection in Routes**
```python
# Query Route: query_route.py
┌─────────────────────────────────────┐
│ POST /query/ask                     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Process Query                       │
│  - Track start time                 │
│  - Run RAG pipeline                 │
│  - Extract tokens                   │
│  - Calculate cost                   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ trigger_query_logging()             │
│  - Queue background task via Celery │
│  - Return immediately to client     │
└────────────┬────────────────────────┘
             │
             ▼ (Background Task)
┌─────────────────────────────────────┐
│ log_query_run_and_cost()            │
│  - Save to database (runs)          │
│  - Save to database (costs)         │
│  - Record Prometheus metrics:       │
│    * track_llm_cost()               │
│    * llm_tokens_consumed.inc()      │
│    * llm_tokens_generated.inc()     │
│    * query_pipeline_duration.obs()  │
└─────────────────────────────────────┘
```

#### 3. **System Resource Collection**
```python
# In main.py startup_event()
┌─────────────────────────────────────┐
│ record_metrics_periodically()       │
│  - Runs every 10 seconds            │
│  - Calls record_resource_metrics()  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ record_resource_metrics()           │
│  (from app/core/monitors.py)        │
│  - CPU: psutil.cpu_percent()        │
│  - Memory: psutil.virtual_memory()  │
│  - Disk: psutil.disk_usage()        │
│  - Network: psutil.net_io_counters()│
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Update Gauge Metrics                │
│  - system_cpu_usage_percent.set()   │
│  - system_memory_usage_percent.set()│
│  - system_disk_usage_percent.set()  │
│  - process_memory_usage_mb.set()    │
└─────────────────────────────────────┘
```

### Why We See Metrics in Grafana

**Critical Insight**: When you open Grafana and see a blank dashboard with only system metrics (CPU, memory, disk):

1. ✅ **System Metrics Work** - These are collected every 10 seconds automatically
2. ❌ **Application Metrics Missing** - These required explicit recording in code

**The Issue We Fixed**:
- Metrics were defined in `monitors.py` but never recorded when queries/agents ran
- Logging services only saved to database, didn't update Prometheus
- Frontend analytics showed data (from database) but Grafana showed nothing (no Prometheus metrics)

**The Solution**:
1. Added metric recording to `query_logging_service.py` - Now records `track_llm_cost()`, `llm_tokens_consumed.inc()`, etc.
2. Added metric recording to `agent_logging_service.py` - Now records agent metrics
3. Updated `query_route.py` to explicitly call `trigger_query_logging()`
4. Updated `agent_route.py` to explicitly call `trigger_agent_logging()`

Now when you run a query:
1. Query completes and triggers background logging
2. Background task records to database (for frontend analytics)
3. Background task records to Prometheus (for Grafana dashboards)
4. Prometheus scrapes `/metrics` every 10 seconds
5. Grafana queries Prometheus and displays updated graphs

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- 4GB RAM minimum
- 10GB disk space

### Installation

1. **Clone and Setup**
```bash
cd atlas-ai
cp .env.example .env
# Edit .env with your settings
```

2. **Build and Start Services**
```bash
docker-compose up -d
```

3. **Monitor Startup**
```bash
# Check all services are healthy
docker ps
# View API logs
docker logs atlas-api
```

### Verify Installation

1. **API Health Check**
```bash
curl http://localhost:8000/health
```

2. **Prometheus Metrics**
```bash
curl http://localhost:9091/api/v1/targets
```

3. **Access Grafana**
- URL: http://localhost:3100
- Username: admin
- Password: admin123 (from docker-compose.yml)

4. **Access MLflow**
- URL: http://localhost:5000
- View experiment runs and metrics

5. **Frontend**
- URL: http://localhost:3100 (Grafana port)
- Or http://localhost:3000 (React frontend, if configured)

---

## API Documentation

### Authentication Endpoints

#### Register New User
```bash
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "User Name",
  "tenant_name": "Tenant Name"
}
```

#### Login
```bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}
# Returns: { "access_token": "jwt_token", "user": {...} }
```

### Query Endpoints

#### Ask Question (RAG)}
```bash
POST /api/query/ask
Headers:
  Authorization: Bearer {token}
  tenant-id: {tenant_id}
  current-user: {user_id}

{
  "query": "What is the company's revenue?"
}

Response: StreamingResponse (streaming plain text answer)
```

#### Retrieve Documents
```bash
POST /api/query/retrieve
Headers: (same as above)

{
  "query": "What is the company's revenue?"
}

Response: 
{
  "query": "...",
  "documents_count": 5,
  "documents": [
    {
      "id": "doc_1",
      "content": "...",
      "source": "document.pdf",
      "metadata": {...}
    }
  ]
}
```

#### Get Cost Analytics
```bash
GET /api/query/cost-analytics
Headers: (same as above)

Response:
{
  "total_cost": 0.45,
  "total_input_tokens": 5000,
  "total_output_tokens": 1200,
  "by_model": [
    {
      "model": "Qwen2.5-1.5B",
      "cost": 0.45,
      "input_tokens": 5000,
      "output_tokens": 1200
    }
  ]
}
```

#### Get Runs
```bash
GET /api/query/runs
Headers: (same as above)

Response:
{
  "runs": [
    {
      "run_id": "uuid",
      "query": "What is...?",
      "answer": "The answer is...",
      "latency": 2.5,
      "cache_hit": false,
      "retrieved_docs_ids": "doc1,doc2",
      "created_at": "2024-03-02T10:30:00"
    }
  ],
  "count": 10
}
```

### Agent Endpoints

#### Ask Agent (Streaming)
```bash
POST /api/agent/ask-agent
Headers:
  Authorization: Bearer {token}

{
  "question": "What is the question?"
}

Response: StreamingResponse (Server-Sent Events)
Events:
  - { "type": "tool_start", "tool": "Thinking" }
  - { "type": "thought", "content": "..." }
  - { "type": "tool_end", "tool": "SQL Query" }
  - { "type": "answer", "content": "..." }
  - { "type": "done", "status": "success" }
```

#### Ask Agent (Batch)
```bash
POST /api/agent/ask-agent-batch
Headers: (same as above)

{
  "question": "What is the question?"
}

Response:
{
  "success": true,
  "question": "...",
  "final_answer": "...",
  "thoughts": ["...", "..."],
  "step_count": 3,
  "total_cost": 0.25,
  "sql_queries": ["SELECT ..."],
  "retrieved_context": "..."
}
```

### Document Ingestion

#### Ingest Document
```bash
POST /api/ingest/upload
Headers:
  Authorization: Bearer {token}
  tenant-id: {tenant_id}

Form Data:
  file: multipart file (PDF, DOCX, TXT)
  document_name: "Document Name"

Response:
{
  "success": true,
  "document_id": "doc_uuid",
  "chunks_created": 25,
  "status": "processing"
}
```

### Metrics Endpoint

#### Export Prometheus Metrics
```bash
GET /metrics

Response: Prometheus text format
# HELP atlas_http_requests_total Total number of HTTP requests
# TYPE atlas_http_requests_total counter
atlas_http_requests_total{endpoint="/api/query/ask",method="POST",status_code="200"} 125.0
...
```

---

## Frontend Analytics

### Available KPIs on Dashboard

The frontend displays analytics from two sources:

#### 1. From Database (Runs & Costs Tables)
- **Total Queries**: Count of all query runs
- **Average Latency**: Mean query response time
- **Cache Hit Rate**: Percentage of cached responses
- **Cost per Query**: Average cost per query
- **By Model Breakdown**: Cost and token usage by LLM model
- **Total Input Tokens**: Sum of all input tokens
- **Total Output Tokens**: Sum of all output tokens

#### 2. From Prometheus (via Grafana)
- **Request Rate**: Requests per second by endpoint
- **P95/P99 Latency**: Latency percentiles
- **Error Rate**: Percentage of failed requests
- **CPU Usage**: System CPU utilization
- **Memory Usage**: RAM consumption
- **Disk Usage**: Storage utilization

### Data Flow for Frontend Analytics

```
┌──────────────────────────┐
│   User Query Executed    │
└────────┬─────────────────┘
         │
         ├──► trigger_query_logging()
         │           │
         │           ▼
         │    ┌──────────────────────┐
         │    │ Background Task      │
         │    │ (Celery)             │
         │    │                      │
         │    ├─► Save to DB         │
         │    │   ✓ Runs table       │
         │    │   ✓ Costs table      │
         │    │                      │
         │    └─► Record Prometheus  │
         │        ✓ Gauge metrics    │
         │        ✓ Counter metrics  │
         │
         └────► Response to Client

Later:
┌──────────────────────────────────┐
│  Frontend: GET /api/query/runs   │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Backend: Query Runs table         │
│  - query_route.py:get_runs()       │
│  - Returns last 50 runs            │
│  - Includes latency, costs         │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Frontend: Display Analytics       │
│  - Total queries                   │
│  - Average latency                 │
│  - Cache hit rate                  │
│  - Cost per query                  │
└────────────────────────────────────┘

Similarly:
┌──────────────────────────────────┐
│  Frontend: GET /api/query/       │
│          cost-analytics          │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Backend: Query Costs table        │
│  - query_route.py:get_cost_analytics│
│  - Group by model                  │
│  - Sum costs & tokens              │
└────────┬───────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Frontend: Display Cost Report     │
│  - Total cost                      │
│  - By-model breakdown              │
│  - Token usage trends              │
└────────────────────────────────────┘
```

---

## Dashboard Access

### Grafana Dashboards

**URL**: http://localhost:3100

**Default Credentials**:
- Username: `admin`
- Password: `admin123`

**Available Dashboards**:

1. **System Health Monitor**
   - CPU utilization
   - Memory usage
   - Disk usage
   - Network I/O

2. **HTTP Request Metrics**
   - Requests per second by endpoint
   - Request latency (P50, P95, P99)
   - Response sizes
   - Error rates by status code

3. **RAG Pipeline Performance**
   - Document ingestion rate
   - Embedding generation latency
   - Vector search latency
   - Retrieval count distribution
   - Reranking performance

4. **LLM & Token Metrics**
   - Total LLM queries
   - Query latency distribution
   - Token consumption (input/output)
   - Cost trends

5. **Agent Performance**
   - Agent queries executed
   - Reasoning steps distribution
   - Decision latency
   - Tool call frequency

6. **Cost Analytics**
   - Total API costs
   - Cost per query
   - Cost by model
   - Monthly cost trends
   - Per-tenant costs

### Creating Custom Dashboards

1. Go to Prometheus data source
2. Write PromQL queries:
   ```promql
   # Total requests
   sum(rate(atlas_http_requests_total[5m]))
   
   # P95 latency
   histogram_quantile(0.95, rate(atlas_http_request_duration_seconds_bucket[5m]))
   
   # Token usage per tenant
   sum by (tenant_id) (atlas_llm_tokens_consumed)
   ```
3. Create panels and save dashboard

---

## Cost Tracking

### Cost Calculation

**Token-based Pricing Model**:
```
cost = (input_tokens × input_rate) + (output_tokens × output_rate)

Default rates (configurable):
- Input tokens: $0.0000001 per token
- Output tokens: $0.0000002 per token

Example:
- Input: 1000 tokens → $0.0001
- Output: 500 tokens → $0.0001
- Total: $0.0002
```

### Cost Tracking Flow

```
1. Query Executed
   │
   ├─ Extract token counts from LLM response
   ├─ Calculate: cost = (input × rate1) + (output × rate2)
   │
2. Log Query Run
   ├─ Save to database (runs table)
   ├─ Save to database (costs table)
   │
3. Record Metrics
   ├─ Prometheus: api_calls_cost_total.inc(cost)
   ├─ Prometheus: tokens_cost_total.inc(cost)
   ├─ Prometheus: cost_per_query.observe(cost)
   │
4. Analytics Available
   ├─ Frontend: Cost breakdown by model
   ├─ Frontend: Total costs paid
   ├─ Frontend: Cost per query
   ├─ Grafana: Cost trends over time
   └─ Grafana: Per-tenant cost analysis
```

### Viewing Cost Data

#### In Frontend (CostAnalyticsPage.jsx)
- Calls: `GET /api/query/cost-analytics`
- Shows: Total cost, by-model breakdown
- Calls: `GET /api/query/runs`
- Shows: Average latency, cache hit rate, cost per query

#### In Grafana
- Metric: `atlas_api_calls_cost_total`
- Metric: `atlas_cost_per_query`
- Dashboard: **Cost Analytics**

#### In MLflow
- Experiment: Query runs
- Logged metrics: `cost_usd`, `latency_seconds`
- Tracked artifacts: Query logs

---

## Troubleshooting

### Issue 1: Grafana Shows Only System Metrics

**Symptom**: 
- CPU, memory, disk metrics show data
- Token usage, cost metrics show no data
- Agent metrics are empty

**Root Cause**: 
- Prometheus wasn't being updated with application metrics
- Logging services weren't recording metrics

**Solution** (Already Applied):
✅ Modified `query_logging_service.py` to call `track_llm_cost()`
✅ Modified `agent_logging_service.py` to call agent metrics
✅ Updated `query_route.py` to call `trigger_query_logging()`
✅ Updated `agent_route.py` to call `trigger_agent_logging()`

**Verification**:
```bash
# 1. Make a query
curl -X POST http://localhost:8000/api/query/ask \
  -H "tenant-id: 1" \
  -H "current-user: user123" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this?"}'

# 2. Wait 15 seconds (Prometheus scrape interval)

# 3. Check metrics exist
curl http://localhost:9091/api/v1/query?query=atlas_llm_tokens_consumed

# 4. View in Grafana after a few seconds
# Go to http://localhost:3100 and check dashboards
```

### Issue 2: Frontend Analytics Show No Data

**Symptom**:
- CostAnalyticsPage loads but shows zeros
- No cost breakdown by model
- No usage metrics

**Root Cause**:
- No queries have been executed yet
- Database tables are empty

**Solution**:
1. Execute a query: `POST /api/query/ask`
2. Wait 10 seconds for background task to complete
3. Refresh the analytics page
4. Data should appear

**Verify Database**:
```bash
# Connect to PostgreSQL
docker exec atlas-postgres psql -U atlas_user -d atlas_db

# Check runs table
SELECT COUNT(*) FROM runs;

# Check costs table
SELECT * FROM cost_logs;
```

### Issue 3: Prometheus Says No Data

**Symptom**:
- Grafana queries return "No data"
- `/metrics` endpoint shows metrics but they don't appear in Prometheus

**Root Cause**:
- Prometheus isn't scraping the API
- Network connectivity issue

**Solution**:
```bash
# 1. Verify API /metrics endpoint works
curl http://localhost:8000/metrics | head -20

# 2. Check Prometheus targets
curl http://localhost:9091/api/v1/targets

# 3. Look for atlas-api target
# Should show "UP" if healthy
# If DOWN, check docker-compose.yml networking

# 4. View Prometheus scrape logs
docker logs atlas-prometheus | grep "atlas-api"

# 5. Restart Prometheus if needed
docker restart atlas-prometheus
```

### Issue 4: Agent Executions Not Logged

**Symptom**:
- Agent queries work but don't appear in analytics
- No agent metrics in Grafana
- No agent runs in database

**Root Cause**:
- `trigger_agent_logging()` not being called
- Background tasks not processing

**Solution**:
1. Verify Celery worker is running:
```bash
docker logs atlas-celery-worker
# Should show: "celery@... ready."
```

2. Make an agent query:
```bash
curl -X POST http://localhost:8000/api/agent/ask-agent \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this?"}'
```

3. Check Celery task status:
```bash
# View task queue
docker exec atlas-redis redis-cli KEYS "*"
```

4. Verify logging service is imported:
```bash
grep "trigger_agent_logging" app/routes/agent_route.py
```

### Issue 5: High Latency on Queries

**Symptom**:
- Queries take 30+ seconds
- Grafana shows high P95/P99 latency

**Root Cause**:
- Embedding model is slow
- Vector search is inefficient
- LLM response time is slow

**Solution**:
1. **Profile Query**:
```python
import time
start = time.time()
# Run query
duration = time.time() - start
print(f"Total: {duration}s")
```

2. **Check Embedding Latency**:
- Metric: `atlas_embedding_generation_duration_seconds`
- Typical: 0.5-2 seconds

3. **Check Retrieval Latency**:
- Metric: `atlas_vector_search_duration_seconds`
- Typical: 0.1-0.5 seconds

4. **Check LLM Latency**:
- Metric: `atlas_llm_query_duration_seconds`
- Typical: 5-30 seconds (depends on model size)

5. **Optimization**:
- Enable semantic caching
- Reduce number of retrieved chunks
- Use faster LLM model
- Increase Qdrant pool size

### Issue 6: Out of Memory

**Symptom**:
- Container crashes
- `OOMKilled` in docker logs
- Grafana memory usage at 100%

**Root Cause**:
- Large embeddings in memory
- Unbounded cache growth
- Memory leak in agent

**Solution**:
```bash
# 1. Check memory usage
docker stats atlas-api

# 2. Clear Redis cache
docker exec atlas-redis redis-cli FLUSHALL

# 3. Increase container memory in docker-compose.yml
# Add: mem_limit: 4g

# 4. Restart services
docker-compose down
docker-compose up -d
```

### Issue 7: Database Connection Errors

**Symptom**:
- "Connection refused" errors
- Queries fail with database errors
- Health check fails

**Root Cause**:
- PostgreSQL not running
- Network connectivity issue
- Credentials mismatch

**Solution**:
```bash
# 1. Check PostgreSQL
docker logs atlas-postgres

# 2. Verify connection
docker exec atlas-postgres pg_isready -U atlas_user

# 3. Check env variables
docker exec atlas-api env | grep POSTGRES

# 4. Restart PostgreSQL
docker-compose down postgres
docker-compose up postgres -d
```

---

## Metrics Implementation Summary

### What Was Fixed

| Issue | Before | After |
|-------|--------|-------|
| **Query Metrics** | Not recorded to Prometheus | ✅ Recorded in logging service |
| **Agent Metrics** | Not recorded to Prometheus | ✅ Recorded in logging service |
| **Token Tracking** | No Prometheus metrics | ✅ `llm_tokens_consumed` recorded |
| **Cost Tracking** | Only in database | ✅ Added to Prometheus + database |
| **Grafana Dashboard** | Empty application panels | ✅ Now shows token/cost data |
| **Frontend Analytics** | Worked (from DB) | ✅ Still works, now also in Grafana |

### Files Modified

1. **app/services/rag_services/query_logging_service.py**
   - Added Prometheus metric imports
   - Added `track_llm_cost()` call
   - Added token consumption tracking

2. **app/services/rag_services/agent_logging_service.py**
   - Added agent metric imports
   - Added `agent_queries_total.inc()`
   - Added `agent_reasoning_duration_seconds.observe()`

3. **app/routes/query_route.py**
   - Added `trigger_query_logging` import
   - Call `trigger_query_logging()` after query completes
   - Improved documentation

4. **app/routes/agent_route.py**
   - Enhanced docstrings
   - Improved error handling
   - Better logging

5. **app/core/metrics.py**
   - Added comprehensive docstring

6. **main.py**
   - Enhanced monitoring documentation
   - Clearer metric collection explanation

---

## Future Enhancements

### Planned Features

1. **Advanced Reranking**
   - LLM-based reranking
   - Cross-lingual reranking
   - Domain-specific rankers

2. **Extended Agent Capabilities**
   - Web search integration
   - PDF parsing tools
   - Code execution tooling
   - Multi-document analysis

3. **Analytics Enhancements**
   - Real-time dashboards
   - Anomaly detection
   - Cost forecasting
   - Performance regression detection

4. **Scalability**
   - Kubernetes support
   - Multi-replica deployment
   - Load balancing
   - Auto-scaling policies

5. **Security**
   - End-to-end encryption
   - Audit logging
   - IP whitelisting
   - Rate limiting per tenant

6. **Model Support**
   - LLaMA integration
   - GPT-4 compatibility
   - Anthropic Claude support
   - Local model switching

---

## Support & Contributions

### Getting Help

1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `docker logs <service-name>`
3. Check Prometheus: http://localhost:9091
4. Check Grafana: http://localhost:3100
5. Check MLflow: http://localhost:5000

### Contributing

Contributions are welcome! Areas to contribute:

- New reranking strategies
- Agent tools
- Monitoring improvements
- Documentation
- Bug fixes
- Performance optimizations

---

## License

This project is proprietary software. All rights reserved.

---

## Architecture Decision Records

### Why Prometheus + Grafana?

- **Prometheus**: Time-series database, perfect for metrics
- **Grafana**: Beautiful dashboards, alerting support
- **MLflow**: Experiment tracking for model development
- **Three-pronged approach**: Real-time (Prometheus), Historical (MLflow), Reporting (Grafana)

### Why Background Tasks for Logging?

- Metrics recording (DB + Prometheus) is synchronous and fast (~10ms)
- Response doesn't block on logging
- Database writes are reliable with retries
- Metrics are available immediately

### Why Metrics at Query Completion?

- All data is available (latency, tokens, cost)
- Single point of truth
- No need for distributed tracing
- Simple and efficient

---

**Last Updated**: March 2, 2026

**Status**: ✅ Production Ready

**Metrics System**: ✅ Fully Functional

