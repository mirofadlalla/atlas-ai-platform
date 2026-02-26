<div align="center">

<h1>🌍 Atlas AI Platform</h1>

<p>
  <strong>A production-ready, multi-tenant RAG (Retrieval-Augmented Generation) platform with advanced authentication, document ingestion, semantic retrieval, and enterprise-grade evaluation</strong><br/>
  Built with FastAPI · Qdrant · PostgreSQL · Celery · MLflow
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Qdrant-Vector%20DB-ef6c00?style=for-the-badge&logo=databricks&logoColor=white"/>
  <img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/MLflow-Tracking-0194E2?style=for-the-badge&logo=mlflow&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
</p>

<p>
  <em>Authenticate → Upload Documents → Semantic Search → LLM-Powered Answers → Evaluate Quality → Track Costs</em>
</p>

</div>

---

## 📖 Table of Contents

- [What is Atlas AI?](#-what-is-atlas-ai)
- [Completed Features](#-completed-features)
- [Architecture Overview](#-architecture-overview)
- [Key Components](#-key-components)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [API Reference](#-api-reference)
- [Authentication System](#-authentication-system)
- [Multi-Tenancy Architecture](#-multi-tenancy-architecture)
- [Document Management](#-document-management)
- [RAG Pipeline Deep Dive](#-rag-pipeline-deep-dive)
- [Query Pipeline](#-query-pipeline)
- [Evaluation Framework](#-evaluation-framework)
- [Cost Tracking & Analytics](#-cost-tracking--analytics)
- [Design Patterns](#-design-patterns)
- [Database Schema](#-database-schema)
- [Configuration](#-configuration)
- [Roadmap](#-roadmap)

---

## 🚀 What is Atlas AI?

**Atlas AI** is a comprehensive, enterprise-grade multi-tenant Retrieval-Augmented Generation (RAG) platform that enables organizations to:

- 🔐 **Authenticate users securely** with JWT-based authentication and role-based access control
- 🤝 **Manage team invitations** with admin approval workflows and token-based signup
- 📂 **Ingest structured and unstructured documents** (PDFs, text files, entire directories) with deduplication
- 🔍 **Retrieve semantically relevant chunks** using advanced vector similarity search with reranking
- 💬 **Generate grounded, accurate answers** using LLMs (Qwen 2.5 via Featherless AI)
- 📊 **Evaluate retrieval and generation quality** with comprehensive metrics
- 💰 **Track API costs and usage** with detailed token counting and cost analytics
- 🔐 **Isolate data per tenant** — complete enterprise data segregation with namespace-based vector collections
- 📊 **Monitor experiments** with MLflow integration for experiment tracking and model versioning

Whether you're building an internal knowledge base, document Q&A system, customer support AI, or enterprise-grade semantic search engine, Atlas AI provides the complete production-ready pipeline.

---

## ✅ Completed Features

### Phase 1: Core RAG Infrastructure ✓

- [x] **Multi-tenant vector database** (Qdrant with namespace isolation)
- [x] **Semantic document chunking** (token-based splitting + embedding-based boundary detection)
- [x] **Batch document ingestion** (PDFs, text files, recursive directories)
- [x] **File hash deduplication** (MD5-based duplicate detection)
- [x] **Embedding pipeline** (HuggingFace integration with singleton pattern)
- [x] **Dense vector search** (Qdrant ANN with top-K retrieval)
- [x] **Cross-Encoder reranking** (semantic relevance scoring)
- [x] **BM25 reranking** (traditional lexical ranking)
- [x] **Hybrid reranking** (combined semantic + lexical scoring)

### Phase 2: Authentication & Multi-Tenancy ✓

- [x] **User registration** with secure password hashing (bcrypt)
- [x] **JWT-based login** with configurable token expiration
- [x] **Tenant management** with isolated data per organization
- [x] **Role-based access control** (admin, user roles)
- [x] **User approval workflow** (pending/approved/rejected status)
- [x] **Admin invitation system** (token-based signup with expiration)
- [x] **Invitation resend** (resend expired or lost invitations)
- [x] **User profile endpoints** (retrieve current user information)
- [x] **Pending approval management** (admin dashboard for user approval)
- [x] **User approval/rejection** (admin approval workflow)

### Phase 3: Query & Answer Generation ✓

- [x] **Question answering pipeline** with context-aware prompting
- [x] **Streaming responses** (Server-Sent Events for real-time answer generation)
- [x] **Document retrieval** with configurable top-K results
- [x] **Query embedding** (consistent with ingestion embeddings)
- [x] **Hallucination prevention** (grounded prompting with "I don't know" fallback)
- [x] **LLM integration** (Featherless AI / HuggingFace Inference API)

### Phase 4: Evaluation & Analytics ✓

- [x] **Precision@K metrics** (relevance measurement)
- [x] **Recall@K metrics** (coverage measurement)
- [x] **F1 Score** (harmonic mean of precision and recall)
- [x] **Mean Reciprocal Rank (MRR)** (ranking quality metric)
- [x] **Jaccard Stability** (result consistency across runs)
- [x] **Rephrase Stability** (robustness to paraphrasing)
- [x] **Token F1** (keyword overlap scoring)
- [x] **Synthetic evaluation dataset generation** (automatic Q&A generation)
- [x] **MLflow integration** (experiment tracking and metrics logging)
- [x] **Run evaluation** (multi-run evaluation with aggregate metrics)

### Phase 5: Cost Tracking & Monitoring ✓

- [x] **Token counting** (input + output token tracking)
- [x] **Cost calculation** (per-run LLM cost estimation)
- [x] **Cost logging** (persistent cost tracking in PostgreSQL)
- [x] **Run tracking** (query, answer, latency, retrieved documents)
- [x] **Cache detection** (cache hit tracking)
- [x] **Cost analytics** (aggregated cost data per tenant)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       Client / API Consumer                  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                        │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  /auth       │  │  /ingest-rag    │  │  /eval-rag     │  │
│  │  Register    │  │  Upload Files   │  │  Run Eval      │  │
│  │  Login       │  │  Process Dirs   │  │  Get Metrics   │  │
│  └──────────────┘  └────────┬────────┘  └────────────────┘  │
└───────────────────────────── │ ──────────────────────────────┘
                               │
           ┌───────────────────┴────────────────────┐
           │                                        │
           ▼                                        ▼
┌─────────────────────┐               ┌─────────────────────────┐
│   RAG Ingestion     │               │   RAG Retrieval          │
│   Pipeline          │               │   Pipeline               │
│                     │               │                          │
│  1. Hash Check      │               │  1. Embed Query          │
│  2. Load Document   │               │  2. Vector Search        │
│  3. Token Split     │               │  3. Return Top-K Docs    │
│  4. Semantic Chunk  │               │                          │
│  5. Embed Chunks    │               └─────────────────────────┘
│  6. Store in Qdrant │
└──────────┬──────────┘
           │
     ┌─────┴──────────────────────────┐
     │                                │
     ▼                                ▼
┌──────────┐                  ┌───────────────┐
│ Qdrant   │                  │  PostgreSQL   │
│ (Vectors)│                  │  (Metadata,   │
│          │                  │   Users,      │
│ Per-     │                  │   Tenants,    │
│ tenant   │                  │   File Hashes)│
│ namespaces│                 └───────────────┘
└──────────┘
```

---

## 🔑 Key Components

### Authentication & Authorization
- **Multi-tenant JWT authentication** with role-based access control
- **User approval workflows** with admin dashboard
- **Invitation system** with token-based signup and expiration handling

### Document Processing
- **Smart file ingestion** with MD5-based deduplication
- **Two-stage semantic chunking** (token-based + embedding-based)
- **Batch directory processing** with recursive file handling
- **Factory Pattern** for extensible file type support

### Semantic Search & Retrieval
- **Dense vector search** via Qdrant with per-tenant namespaces
- **Multiple reranking strategies** (cross-encoder, BM25, hybrid)
- **Configurable retrieval parameters** (top-K, reranker selection)

### LLM Integration
- **Featherless AI backend** for scalable LLM access
- **Token counting** for cost estimation
- **Streaming response support** (Server-Sent Events)
- **Hallucination prevention** with grounded prompting

### Evaluation & Analytics
- **Comprehensive evaluation metrics** (Precision, Recall, F1, MRR, etc.)
- **Stability testing** (Jaccard, rephrase stability)
- **Synthetic dataset generation** for evaluation
- **MLflow experiment tracking** for result versioning

### Cost Management
- **Per-run cost tracking** with token counting
- **Aggregated analytics** by tenant
- **Cache detection** for optimization insights

---

## ✨ Key Features

### 🔐 Multi-Tenant Architecture with Complete Data Isolation

- **JWT-based authentication** with secure password hashing (`bcrypt`)
- **Role-based access control** (admin, user roles)
- **Tenant isolation:** every document, embedding, and query is scoped to its tenant with namespace-based separation
- **Per-tenant namespaces** in Qdrant for vector isolation
- **Separate vector collections** ensure zero data leakage between tenants

### 🤝 Enterprise Authentication & Team Management

- **User registration** with email-based validation
- **Password security** with bcrypt hashing and JWT tokens
- **Admin approval workflow** with three-state system (pending, approved, rejected)
- **Token-based user invitations** with 7-day expiration
- **Invitation management** (send, resend, validate, accept)
- **Admin dashboard** for managing pending user approvals
- **User profile endpoints** for account information

### 📥 Smart Document Ingestion Pipeline

- **File hash tracking** via MD5 — identical files are detected and skipped, saving compute
- **Factory Pattern** upload handling — supports PDFs, text files, and recursive directories
- **Batch processing** with configurable file extensions
- **Recursive directory traversal** for mass document ingestion
- **Two-stage chunking strategy:**
  1. **Token-based splitting** — breaks large documents into manageable windows (2000 tokens, 50 overlap)
  2. **Semantic chunking** — uses embedding similarity to split at natural semantic boundaries (90th percentile breakpoint), ensuring each chunk is topically coherent

### 🔍 Advanced Semantic Retrieval with Intelligent Reranking

- **Dense vector search** via **Qdrant** with per-tenant collection namespaces
- **Embeddings** powered by a singleton `EmbeddedModel` (lazy-loaded for efficiency)
- **LangChain Retriever interface** for flexible downstream integration
- **Three advanced reranking strategies** to optimize retrieval quality:
  - **Cross-Encoder Reranking** — Uses transformer models to directly score query-document pairs for semantic relevance
  - **BM25 Reranking** — Traditional lexical ranking function with term frequency weighting
  - **Hybrid Reranking** (Recommended) — Combines semantic and lexical scoring with configurable weighting (default: 70% semantic, 30% lexical)

### 🧠 LLM Answer Generation with Hallucination Prevention

- Powered by **Qwen 2.5-1.5B-Instruct** via **Featherless AI** (HuggingFace Inference API)
- **Context-grounded prompting** — answers extracted from retrieved documents only
- **Explicit fallback mechanism** — "I don't know" responses when confidence is low
- **Streaming responses** with Server-Sent Events for real-time feedback
- **Token counting** for accurate cost estimation

### 📊 Comprehensive Evaluation Suite with MLflow Integration

- **Precision / Recall / F1** — measures whether the right documents were retrieved
- **MRR (Mean Reciprocal Rank)** — how early relevant results appear in the ranking
- **Jaccard Stability** — measures how consistently the retriever returns the same docs across multiple runs
- **Rephrase Stability** — tests if retrieval is robust to paraphrased questions
- **Token F1** — keyword overlap between LLM answer and reference ground truth
- **Synthetic dataset generation** for automatic evaluation data creation
- **MLflow integration** — all experiment metrics are tracked, versioned, and queryable
- **Multi-run evaluation** with aggregate metrics and statistical analysis

### 💰 Cost Tracking & Analytics

- **Per-run token counting** (input + output tokens)
- **LLM cost calculation** with model-specific pricing
- **Persistent cost logging** in PostgreSQL
- **Aggregated cost analytics** by tenant and time period
- **Cache hit detection** for optimization monitoring

### ⚙️ Background Processing & Scalability

- **Celery worker support** for async document ingestion tasks
- **Decoupled processing** — API responds immediately, Celery handles heavy lifting
- **Configurable task queues** for horizontal scaling

---

## 📁 Project Structure

```
atlas-ai/
│
├── main.py                         # FastAPI app entry point
├── docker-compose.yml              # Orchestrates API + PostgreSQL + Qdrant
├── Dockerfile                      # Production container image
├── alembic.ini                     # Database migration config
├── requirements.txt                # Python dependencies
│
├── alembic/                        # Database migration scripts (Alembic auto-generates versions)
│   └── versions/                   # Migration files
│       ├── e3deece2c1ef_create_atlas_db.py           # Initial DB schema
│       ├── dcf644ec6a71_create_atlas_user_and_tentents_db_tabels.py  # Users & Tenants
│       ├── 31ddc81adc69_create_atlas_db_tabels.py    # Documents & tracking
│       ├── add_invitations_table.py                  # Invitations system
│       ├── add_user_approval_workflow.py             # User approval workflow
│       ├── 3c409934de50_added_tracker_db_table.py    # File tracking
│       ├── 84d6c8d986ec_added_costlog_runs.py        # Cost logging & run tracking
│       └── [Additional migrations as needed]
│
├── app/
│   ├── core/                       # Core infrastructure
│   │   ├── auth.py                 # JWT & authentication utilities
│   │   ├── config.py               # Environment & configuration
│   │   ├── db.py                   # Database session & connection
│   │   └── rate_limitizer.py       # Rate limiting
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── base.py                 # Base model class
│   │   ├── uuid.py                 # UUID primary key helper
│   │   ├── user.py                 # Users table (with approval workflow)
│   │   ├── tenant.py               # Tenants table (multi-tenancy)
│   │   ├── invitation.py           # Invitations table (token-based signup)
│   │   ├── documents.py            # Documents metadata tracking
│   │   ├── TRACKER_DB_FILE.py      # File hash tracking (deduplication)
│   │   ├── runs.py                 # Query runs (tracking queries & answers)
│   │   └── costLog.py              # Cost logging (token & cost tracking)
│   │
│   ├── routes/                     # FastAPI endpoint definitions
│   │   ├── auth_route.py           # Authentication & user management
│   │   │   ├── POST /auth/tenant/register      # Register new tenant
│   │   │   ├── POST /auth/register             # Register user
│   │   │   ├── POST /auth/login                # Login & get JWT token
│   │   │   ├── GET  /auth/profile              # Get current user profile
│   │   │   ├── POST /auth/invitations/send     # Send user invitation (admin)
│   │   │   ├── GET  /auth/invitations/validate # Validate invitation token
│   │   │   ├── POST /auth/register-via-invitation  # Accept invitation & register
│   │   │   ├── GET  /auth/invitations/pending  # List pending invitations
│   │   │   ├── POST /auth/invitations/resend   # Resend invitation
│   │   │   ├── GET  /auth/pending-approvals    # List pending user approvals (admin)
│   │   │   ├── POST /auth/approve-user/{id}    # Approve pending user
│   │   │   └── POST /auth/reject-user/{id}     # Reject pending user
│   │   │
│   │   ├── ingest_rag_route.py     # Document ingestion
│   │   │   └── POST /ingest-rag/upload_file    # Ingest file or directory
│   │   │
│   │   ├── query_route.py          # Query & answer endpoints
│   │   │   ├── POST /ask                       # Ask question (streaming)
│   │   │   └── POST /retrieve                  # Retrieve documents only
│   │   │
│   │   └── eval_pipline.py         # Evaluation endpoints
│   │       ├── POST /eval-rag/evaluate         # Run evaluation
│   │       └── GET  /eval-rag/status/{task_id} # Get evaluation status
│   │
│   ├── controllers/                # Request handling & coordination
│   │   ├── auth_controller.py      # Authentication logic
│   │   └── ingest_rag_controller.py # Document ingestion coordination
│   │
│   ├── services/                   # Business logic layer
│   │   ├── auth_services/          # Authentication services
│   │   │   ├── user_approval_service.py        # User approval workflow
│   │   │   └── [Additional auth services]
│   │   ├── token_service.py        # JWT token management
│   │   ├── hash_service.py         # Password hashing & verification
│   │   ├── invitation_service.py   # Invitation lifecycle management
│   │   ├── invitation_management_service.py    # Admin invitation features
│   │   ├── user_profile_service.py # User profile management
│   │   ├── tenant_registration_service.py      # Tenant onboarding
│   │   ├── llm_runner.py           # LLM call abstraction & token counting
│   │   ├── mlflow_service.py       # MLflow experiment tracking
│   │   ├── rag_services/           # RAG-specific services
│   │   └── registertenant.py       # Tenant creation utility
│   │
│   ├── repositories/               # Database access layer (Repository Pattern)
│   │   ├── user_repository.py      # User CRUD operations
│   │   ├── tenant_repository.py    # Tenant CRUD operations
│   │   ├── invitation_repository.py # Invitation CRUD operations
│   │   ├── cost_log_repository.py  # Cost tracking
│   │   ├── runs_repository.py      # Run/query tracking
│   │   ├── trakcer_db_file_repositorie.py  # File tracking (deduplication)
│   │   └── qdrant.py               # Qdrant vector store operations
│   │
│   ├── schema/                     # Pydantic request/response models
│   │   ├── auth_admin.py           # Auth schemas
│   │   ├── invitation_requests.py  # Invitation request/response models
│   │   ├── query_request.py        # Query request schemas
│   │   ├── upload_request.py       # Upload request schemas
│   │   ├── tenant_schema.py        # Tenant schemas
│   │   └── eval_pipline.py         # Evaluation schemas
│   │
│   ├── design_pattern/             # Design pattern implementations
│   │   ├── embedded_model.py       # Singleton embedding model (lazy-loaded)
│   │   ├── llm_singlton.py         # Singleton LLM client (Featherless AI)
│   │   ├── upload_factory.py       # Factory entry point for uploads
│   │   ├── user_factory.py         # User creation factory
│   │   └── upload_factory_pattern/ # Strategy-based file type handlers
│   │       ├── pdf_handler.py      # PDF file processing
│   │       ├── text_handler.py     # Text file processing
│   │       └── [Additional format handlers]
│   │
│   ├── rag/                        # Core RAG Logic & Pipelines
│   │   ├── ingest_data_pipline.py  # Full ingestion pipeline orchestrator
│   │   │   # Stages: hash check → load → split → chunk → embed → store
│   │   │
│   │   ├── retrivel_data_pipline.py # Retrieval pipeline with reranking
│   │   │   # Stages: embed query → search → rerank → return
│   │   │
│   │   ├── reranker.py             # Document reranking strategies
│   │   │   ├── CrossEncoderReranker  # Semantic relevance scoring
│   │   │   ├── BM25Reranker         # Lexical ranking
│   │   │   └── HybridReranker       # Combined scoring
│   │   │
│   │   ├── steps/                  # Individual pipeline steps (modular design)
│   │   │   ├── loader.py           # Document loaders (PDF, TXT, JSONL, etc.)
│   │   │   ├── ingest.py           # Qdrant vector ingestion
│   │   │   ├── retriever.py        # Vector retriever setup with LangChain
│   │   │   ├── embeddings.py       # Embedding computation & caching
│   │   │   ├── semantic_chunking_function.py  # Two-stage chunking algorithm
│   │   │   └── file_tracker.py     # MD5-based file deduplication
│   │   │
│   │   └── evaluation/             # RAG evaluation framework
│   │       ├── eval_pipline.py     # Evaluation orchestrator
│   │       ├── generate_eval_dataset.py    # Synthetic Q&A dataset generation
│   │       ├── relevance_evaluation.py     # Precision/Recall/F1/MRR computation
│   │       ├── retrieval_stability.py      # Jaccard & rephrase stability testing
│   │       └── evaluation_dataset.json     # Sample evaluation dataset
│   │
│   ├── celery/                     # Async task workers
│   │   ├── celery_config.py        # Celery configuration
│   │   └── [Task definitions]
│   │
│   └── files/                      # File storage
│       ├── uploads/                # Temporary upload directory
│       ├── eval_files/             # Evaluation files
│       └── [Generated files]
│
├── frontend/                       # React frontend (optional)
│   ├── package.json
│   ├── public/
│   └── src/
│
├── mlruns/                         # MLflow experiment tracking data
│   ├── 0/                          # Default experiment
│   └── [Production experiment runs]
│
├── digrams/                        # Architecture diagrams
│   ├── archDigram.simp             # Architecture diagram source
│   └── [Visual documentation]
│
└── SRS/                            # Software Requirements Specification
    └── [Detailed requirements documentation]


---

## 🛠️ Tech Stack

| Layer                   | Technology                              | Purpose                              |
| ----------------------- | --------------------------------------- | ------------------------------------ |
| **API Framework**       | FastAPI                                 | High-performance async REST API      |
| **Vector Database**     | Qdrant                                  | Multi-tenant semantic vector storage |
| **Relational DB**       | PostgreSQL 15                           | Users, tenants, file metadata        |
| **ORM**                 | SQLAlchemy + Alembic                    | Database modeling & migrations       |
| **Embeddings**          | HuggingFace (local)                     | Text-to-vector transformation        |
| **LLM**                 | Qwen 2.5-1.5B via Featherless AI        | Grounded answer generation           |
| **Text Splitting**      | LangChain (Recursive + SemanticChunker) | Intelligent document chunking        |
| **Reranking**           | Cross-Encoder / BM25 / Hybrid           | Improve retrieval result quality     |
| **Authentication**      | JWT (python-jose) + bcrypt              | Secure multi-tenant auth             |
| **Task Queue**          | Celery                                  | Async background document processing |
| **Experiment Tracking** | MLflow                                  | Evaluation metrics & run history     |
| **Containerization**    | Docker + Docker Compose                 | One-command deployment               |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- A HuggingFace API token (`HF_TOKEN`)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/atlas-ai.git
cd atlas-ai
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Database
POSTGRES_USER=atlas
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=atlas_db
DATABASE_URL=postgresql://atlas:your_secure_password@db:5432/atlas_db

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=atlas_documents

# Authentication
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM
HF_TOKEN=hf_your_huggingface_token_here
```

### 3. Start with Docker Compose

```bash
docker-compose up --build
```

This spins up:

- 🚀 **API** on `http://localhost:8000`
- 🐘 **PostgreSQL** on `localhost:5432`
- 🔵 **Qdrant** on `http://localhost:6333`

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Local Development (without Docker)

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## � Authentication System

Atlas AI provides a comprehensive, enterprise-grade authentication and authorization system with role-based access control and multi-stage user approval workflows.

### Authentication Workflow

```
User Registration
    ├─► Email + Password
    ├─► bcrypt Password Hashing
    ├─► JWT Token Generation
    ├─► Approval Status: pending (if approval required) or approved
    └─► Response: JWT Token + Tenant Info

User Login
    ├─► Email + Password
    ├─► Password Verification (bcrypt)
    ├─► Check Approval Status
    │   ├─► approved → Generate JWT Token ✓
    │   ├─► pending → Error: Awaiting admin approval
    │   └─► rejected → Error: Registration rejected
    └─► Response: JWT Token (expires in 30 minutes)

Token Validation
    ├─► Decode JWT
    ├─► Verify Signature
    ├─► Check Expiration
    ├─► Load User & Tenant Scope
    └─► Continue with Request
```

### User Invitation System

**Admin sends invitation:**
1. Admin creates invitation with email address
2. Unique token generated and stored (7-day expiration)
3. Invitation email sent with signup link
4. Token stored in PostgreSQL

**User accepts invitation:**
1. User clicks invitation link (validates token)
2. User provides password during registration
3. User account created with status `approved` (bypasses approval workflow)
4. Invitation marked as `accepted`

**Features:**
- Token expiration (7 days default, configurable)
- Invitation resend (expire old, generate new)
- Pending invitation listing (for admin dashboard)
- Validation endpoint for token verification

### User Approval Workflow

**Three-state system:**
- `pending`: User needs admin approval (default on registration if configured)
- `approved`: User can login and use platform
- `rejected`: User registration was rejected

**Admin features:**
- View pending user approvals
- Approve users (set to approved)
- Reject users (set to rejected, send notification)
- Track approval metadata (who approved, when)

### API Endpoints

| Method  | Endpoint                       | Description                            | Auth Required |
| ------- | ------------------------------ | -------------------------------------- | ------------- |
| `POST`  | `/auth/tenant/register`        | Register new tenant (organization)     | ✗             |
| `POST`  | `/auth/register`               | Register user (self-signup)            | ✗             |
| `POST`  | `/auth/login`                  | Login with email & password            | ✗             |
| `GET`   | `/auth/profile`                | Get current user profile               | ✓             |
| `POST`  | `/auth/invitations/send`       | Send user invitation (admin)           | ✓ (admin)     |
| `GET`   | `/auth/invitations/validate`   | Validate invitation token              | ✗             |
| `POST`  | `/auth/register-via-invitation`| Accept invitation & register           | ✗             |
| `GET`   | `/auth/invitations/pending`    | List pending invitations (admin)       | ✓ (admin)     |
| `POST`  | `/auth/invitations/resend`     | Resend invitation (admin)              | ✓ (admin)     |
| `GET`   | `/auth/pending-approvals`      | List pending user approvals (admin)    | ✓ (admin)     |
| `POST`  | `/auth/approve-user/{user_id}` | Approve pending user (admin)           | ✓ (admin)     |
| `POST`  | `/auth/reject-user/{user_id}`  | Reject pending user (admin)            | ✓ (admin)     |

---

## 🏢 Multi-Tenancy Architecture

Atlas AI implements strict multi-tenancy with complete data isolation at every layer:

### Tenant Isolation Strategy

**1. Database Level:**
- `tenant_id` foreign key on all data tables
- Queries filtered by tenant_id in repository layer
- No cross-tenant queries allowed

**2. Vector Store Level:**
- Per-tenant Qdrant collection namespaces
- Vector isolation using namespace prefixing
- No cross-namespace searches

**3. API Authentication Level:**
- JWT token contains tenant_id
- All requests scoped to authenticated user's tenant
- Tenant validation on every endpoint

### Tenant Data Model

```
Tenant (Organization)
├── Tenant Metadata
│   ├── Tenant ID (UUID)
│   ├── Organization Name
│   ├── Pricing Plan
│   └── Created Timestamp
│
└── Associated Data
    ├── Users (all belong to tenant)
    ├── Documents (scoped to tenant)
    ├── Vector Collections (tenant namespace)
    ├── Query Runs (tracking)
    ├── Cost Logs (per-tenant analytics)
    └── Invitations (for tenant)
```

### Key Features

- **Namespace-based vector isolation** in Qdrant
- **SQL-level filtering** with tenant_id checks
- **No tenant-crossing queries** enforced at API layer
- **Separate cost tracking** per tenant
- **Independent evaluation** per tenant
- **Isolated embeddings** per tenant collection

---

## 📂 Document Management

### Ingestion Process

1. **File Upload:** User sends file or directory path
2. **Hash Calculation:** MD5 hash computed on file content
3. **Deduplication Check:** Query PostgreSQL for existing hash
   - If duplicate: Skip (return previous chunks)
   - If new: Continue processing
4. **Document Loading:** Extract text from PDF/TXT/JSONL
5. **Token Splitting:** Split into ~2000-token chunks with 50-token overlap
6. **Semantic Chunking:** Re-split at semantic boundaries (90th percentile)
7. **Chunk Embedding:** Generate vector embeddings
8. **Qdrant Storage:** Store vectors with tenant namespace
9. **Metadata Logging:** Record file hash, status in PostgreSQL

### Two-Stage Chunking Algorithm

**Stage 1: Token-Based Splitting**
- Chunk size: 2000 tokens (LLM context window aware)
- Overlap: 50 tokens (maintain context between chunks)
- Fast, predictable splitting

**Stage 2: Semantic Chunking**
- Compute pairwise embeddings between consecutive chunks
- Calculate similarity scores
- Find natural breakpoints (90th percentile similarity drop)
- Ensures topically coherent chunks

### File Type Support

- **PDF** — text extraction with PyPDF
- **Text Files (.txt)** — direct loading
- **JSONL** — structured data with metadata
- **Extensible** — factory pattern for adding new formats

### API Endpoints

| Method | Endpoint              | Description                              |
| ------ | --------------------- | ---------------------------------------- |
| `POST` | `/ingest-rag/upload_file` | Ingest file(s) or directory          |

**Request:**
```json
POST /ingest-rag/upload_file
{
  "file_path": "/path/to/document.pdf",
  "tenant_id": "tenant-uuid",
  "source": "document.pdf",
  "author": "Jane Doe",
  "recursive": true,
  "file_extensions": [".pdf", ".txt"]
}
```

**Response:**
```json
{
  "message": "File processed successfully",
  "status": "success",
  "chunks_stored": 42,
  "file_hash": "abc123def456...",
  "duplicate": false
}
```

---

## 💬 Query Pipeline

### End-to-End Query Processing

```
User Question
    │
    ├─► 1. Authenticate & Validate
    │       ├─► JWT validation
    │       └─► Tenant scope check
    │
    ├─► 2. Embed Query
    │       └─► Generate embedding (same model as ingestion)
    │
    ├─► 3. Vector Search (Qdrant)
    │       ├─► Search in tenant namespace only
    │       └─► Retrieve top-50 documents
    │
    ├─► 4. Reranking (Optional)
    │       ├─► Cross-Encoder Scoring (semantic relevance)
    │       ├─► BM25 Scoring (lexical matching)
    │       └─► Hybrid Scoring (70% semantic + 30% lexical)
    │
    ├─► 5. LLM Generation
    │       ├─► Format prompt with top-5 documents
    │       ├─► Call Qwen 2.5 via Featherless AI
    │       ├─► Stream tokens in real-time
    │       └─► Count tokens for cost estimation
    │
    ├─► 6. Cost Calculation
    │       ├─► Count input tokens (query + context)
    │       ├─► Count output tokens (answer)
    │       ├─► Look up model pricing
    │       └─► Calculate USD cost
    │
    ├─► 7. Run Logging
    │       ├─► Log query, answer, latency
    │       ├─► Store retrieved document IDs
    │       ├─► Record cache hit status
    │       └─► Save to PostgreSQL
    │
    └─► 8. Stream Response to User
            ├─► Server-Sent Events (SSE)
            ├─► Real-time token streaming
            └─► Include metadata (sources, cost)
```

### API Endpoints

| Method | Endpoint           | Description                  |
| ------ | ------------------ | ---------------------------- |
| `POST` | `/ask`             | Ask question (streaming)     |
| `POST` | `/retrieve`        | Retrieve documents only      |

**Ask Endpoint (Streaming):**
```json
POST /ask
{
  "question": "What was the Q3 revenue in 2023?",
  "top_k": 5,
  "use_reranker": true,
  "reranker_strategy": "hybrid"
}
```

**Response (Streaming via SSE):**
```
data: "The"
data: " Q3"
data: " revenue"
data: " was"
data: " $1.2B"
...
data: {"sources": [...], "tokens": {...}, "cost": 0.0015}
```

**Retrieve Endpoint (Document-Only):**
```json
POST /retrieve
{
  "query": "revenue information",
  "top_k": 5,
  "use_reranker": true
}
```

**Response:**
```json
{
  "documents": [
    {
      "content": "Q3 revenue was $1.2B",
      "score": 0.92,
      "rerank_score": 0.95,
      "source": "annual_report.pdf"
    }
  ]
}
```

---

## 💰 Cost Tracking & Analytics

Atlas AI tracks all LLM and processing costs for accurate billing and analytics.

### Token Counting

- **Input tokens:** Query + context (retrieved documents)
- **Output tokens:** Generated answer
- **Model-specific pricing:** Different rates by model

### Cost Calculation

**Formula:**
```
Cost = (input_tokens * input_price) + (output_tokens * output_price)
```

**Default pricing (Qwen 2.5-1.5B via Featherless):**
- Input: $0.00001 per token
- Output: $0.00001 per token

### Data Model

**Runs Table:**
- run_id, query, answer, latency
- retrieved_docs_ids, cache_hit status
- tenant_id (multi-tenancy)

**CostLog Table:**
- cost_id, run_id (one-to-one)
- input_tokens, output_tokens
- model_name, cost_usd
- created_at (timestamp)

### Analytics Features

- Per-tenant cost aggregation
- Cost trends over time
- Model-specific cost breakdowns
- Cache efficiency metrics
- Document retrieval statistics

---

## 📡 API Reference

Interactive API documentation available at: `http://localhost:8000/docs`

All endpoints require JWT authentication except for login, registration, and invitation validation.

---

## 🔄 RAG Pipeline Deep Dive

### Ingestion Flow

```
File Input
    │
    ├─► 1. Calculate MD5 Hash
    │         │
    │         └─► Already processed? → SKIP (save compute)
    │
    ├─► 2. Load Document (PDF/TXT/etc.)
    │
    ├─► 3. Token-Level Split
    │         Chunk size: 2000 tokens | Overlap: 50 tokens
    │
    ├─► 4. Semantic Chunking
    │         Embedding-based boundary detection
    │         Breakpoint: 90th percentile similarity drop
    │
    ├─► 5. Generate Stable Chunk IDs
    │         MD5(tenant_id + source + chunk_text)
    │
    ├─► 6. Embed Chunks → HuggingFace Embedding Model
    │
    ├─► 7. Store in Qdrant (per-tenant namespace)
    │
    └─► 8. Mark File as Processed (hash + filename stored in PostgreSQL)
```

### Retrieval Flow

```
User Query
    │
    ├─► Embed Query (same model as ingestion)
    │
    ├─► Qdrant ANN Search (tenant-scoped collection)
    │         ↓
    │    Initial Results (top 20-50)
    │
    ├─► Reranking Stage (optional)
    │         ├─► Cross-Encoder Scoring (semantic relevance)
    │         ├─► BM25 Scoring (lexical matching)
    │         └─► Hybrid Scoring (combined ranking)
    │
    └─► Return Top-K Reranked Documents
```

### Reranking Strategies

Atlas AI provides three sophisticated reranking strategies to improve retrieval quality:

#### 1. Cross-Encoder Reranking
- Uses transformer-based models (e.g., `ms-marco-MiniLM-L-12-v2`)
- Directly scores query-document pairs for semantic relevance
- More accurate than bi-encoders but computationally intensive
- Best for: High-accuracy requirements, smaller result sets

**Usage:**
```python
from app.rag.retrivel_data_pipline import RetrievalPipeline

pipeline = RetrievalPipeline(
    tenant_id="tenant-1",
    use_reranker=True,
    reranker_strategy="cross-encoder"
)
```

#### 2. BM25 Reranking
- Traditional lexical ranking function with term frequency weighting
- Fast and efficiently scores keyword matching
- Complements semantic retrieval for hybrid results
- Best for: Speed, exact keyword matching, combining with other signals

**Usage:**
```python
pipeline = RetrievalPipeline(
    tenant_id="tenant-1",
    use_reranker=True,
    reranker_strategy="bm25"
)
```

#### 3. Hybrid Reranking (Recommended)
- Combines cross-encoder and BM25 scores
- Configurable weighting: Cross-Encoder 70%, BM25 30% (by default)
- Balances semantic relevance with lexical precision
- Best for: Production deployments, balanced quality

**Usage:**
```python
pipeline = RetrievalPipeline(
    tenant_id="tenant-1",
    use_reranker=True,
    reranker_strategy="hybrid"  # default
)
```

#### Disabling Reranking
```python
pipeline = RetrievalPipeline(
    tenant_id="tenant-1",
    use_reranker=False  # Use only vector similarity
)
```

### Example: Retrieve with Reranking

```python
# Initialize pipeline with reranking
pipeline = RetrievalPipeline(tenant_id="1234", use_reranker=True)

# Retrieve documents
documents = pipeline.retrieve(
    query="What was the effective tax rate in 2023?",
    top_k=5
)

# Access reranking scores
for doc in documents:
    print(f"Content: {doc.page_content[:100]}")
    print(f"Original Score: {doc.metadata.get('original_score')}")
    print(f"Rerank Score: {doc.metadata.get('rerank_score')}")
    print(f"Combined Score: {doc.metadata.get('combined_score')}")
    print("---")
```

---

## � Evaluation Framework

Atlas AI ships with a complete evaluation harness to measure RAG quality objectively.

### Evaluation Dataset Format

```json
[
  {
    "question": "What was the effective tax rate in 2023?",
    "answer": "21.0%",
    "relevant_ids": ["chunk-uuid-1", "chunk-uuid-2"],
    "paraphrases": [
      "What percentage was paid in taxes in 2023?",
      "How much tax did the company owe in fiscal year 2023?"
    ]
  }
]
```

### Metrics Computed

| Metric                 | What It Measures                                    |
| ---------------------- | --------------------------------------------------- |
| **Precision@K**        | Fraction of retrieved docs that are relevant        |
| **Recall@K**           | Fraction of relevant docs that were retrieved       |
| **F1 Score**           | Harmonic mean of Precision and Recall               |
| **MRR**                | How early the first relevant result appears         |
| **Jaccard Stability**  | Consistency of results across repeated queries      |
| **Rephrase Stability** | Robustness to question paraphrasing                 |
| **Token F1**           | Keyword overlap between LLM answer and ground truth |

### Running an Evaluation

```python
from pathlib import Path
from app.rag.evaluation.eval_pipline import EvalPipeline

evaluator = EvalPipeline(
    path=Path("app/rag/evaluation/evaluation_dataset.json"),
    tenant_id="1234"
)

results = evaluator.evaluate(runs=3)
```

---

## 🎨 Design Patterns

Atlas AI is built with clean architecture principles:

| Pattern                | Where Used                                  | Purpose                                           |
| ---------------------- | ------------------------------------------- | ------------------------------------------------- |
| **Factory Pattern**    | `upload_factory.py`                         | Route different file types to appropriate loaders |
| **Repository Pattern** | `repositories/`                             | Decouple database access from business logic      |
| **Singleton Pattern**  | `embedded_model.py`, `llm_singlton.py`      | Load heavy models once, reuse everywhere          |
| **Pipeline Pattern**   | `ingest_data_pipline.py`, `eval_pipline.py` | Chain processing steps in defined order           |
| **Strategy Pattern**   | `upload_factory_pattern/`                   | Swappable file handling strategies                |

---

## ⚙️ Configuration

| Variable                          | Description                       | Default                 |
| --------------------------------- | --------------------------------- | ----------------------- |
| `DATABASE_URL`                    | PostgreSQL connection string      | Required                |
| `QDRANT_URL`                      | Qdrant server URL                 | `http://localhost:6333` |
| `QDRANT_COLLECTION`               | Base collection name              | `atlas_documents`       |
| `SECRET_KEY`                      | JWT signing key                   | Required                |
| `ALGORITHM`                       | JWT algorithm                     | `HS256`                 |
| `ACCESS_TOKEN_EXPIRE_MINUTES`     | Token TTL                         | `30`                    |
| `HF_TOKEN`                        | HuggingFace API token             | Required                |
| `HF_HUB_DISABLE_SYMLINKS_WARNING` | Suppress Windows symlink warnings | `1`                     |

---

## 🗄️ Database & Migrations

Atlas AI uses **Alembic** for database schema version control.

```bash
# Create a new migration
alembic revision --autogenerate -m "add new table"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# View migration history
alembic history
```

### Core Database Models

```
Users          Tenants         TrackedFiles
─────────      ────────────    ─────────────────
id (PK)        id (PK)         id (PK)
username       name            tenant_id (FK)
password_hash  created_at      file_name
tenant_id (FK)                 file_hash
                                processed_at
```

---

## 🐳 Docker Services

```yaml
# docker-compose.yml overview
services:
  api: # FastAPI application (port 8000)
  db: # PostgreSQL 15 with health checks (port 5432)
  qdrant: # Qdrant vector database (port 6333)
```

Persistent volumes ensure your data survives container restarts:

- `db_data` → PostgreSQL data
- `qdrant_data` → Qdrant vector storage

---

## 🚀 Roadmap

### ✅ Phase 1-5: Completed (v1.0)

**What's Been Built:**

- ✅ **Multi-Tenant RAG Pipeline** — Complete document ingestion, semantic search, and answer generation
- ✅ **Enterprise Authentication** — JWT tokens, user approval workflows, token-based invitations
- ✅ **Advanced Retrieval** — Vector search with cross-encoder, BM25, and hybrid reranking
- ✅ **Comprehensive Evaluation** — Precision, Recall, F1, MRR, stability metrics, MLflow integration
- ✅ **Cost Analytics** — Token counting, per-run cost tracking, aggregated pricing by tenant
- ✅ **Multi-Tenancy** — Namespace-based vector isolation, tenant-scoped database queries, complete data segregation

**Summary:** All core RAG functionality is production-ready with evaluation metrics and cost tracking.

---

### 🔄 Next Phase: Agent Framework (v2.0)

**Timeline:** Q2 2026

**Planned Features:**

🤖 **Agent Systems**
- ReAct (Reasoning + Acting) architecture
- Thought-Action-Observation loops
- Tool use framework (web search, code execution, calculators)
- Agent memory management (short-term & long-term)

🧠 **Advanced Reasoning**
- Multi-hop retrieval
- Query decomposition & planning
- Confidence scoring
- Iterative refinement

🔧 **Tool Integration**
- Web search connector
- Python code execution
- External API framework
- Custom tool plugins

📊 **Agent Evaluation**
- Success rate metrics
- Tool-use scoring
- Reasoning trace logging
- Capability benchmarking

💬 **Conversation Management**
- Multi-turn dialogue support
- Session persistence
- Context tracking
- Analytics & insights

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**Built with ❤️ by the Atlas AI Team**

_Authenticate → Ingest → Retrieve → Answer → Evaluate → Track Costs → Stay tuned for Agents (v2.0)_

</div>
