<div align="center">

<h1>🌍 Atlas AI Platform</h1>

<p>
  <strong>A production-ready, multi-tenant RAG (Retrieval-Augmented Generation) platform</strong><br/>
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
  <em>Upload documents → Semantic Search → LLM-Powered Answers → Evaluate Everything</em>
</p>

</div>

---

## 📖 Table of Contents

- [What is Atlas AI?](#-what-is-atlas-ai)
- [Architecture Overview](#-architecture-overview)
- [Key Features](#-key-features)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [API Reference](#-api-reference)
- [RAG Pipeline Deep Dive](#-rag-pipeline-deep-dive)
- [Evaluation Framework](#-evaluation-framework)
- [Design Patterns](#-design-patterns)
- [Configuration](#-configuration)
- [Database & Migrations](#-database--migrations)

---

## 🚀 What is Atlas AI?

**Atlas AI** is a full-stack, multi-tenant Retrieval-Augmented Generation (RAG) platform that enables organizations to:

- 📂 **Ingest structured and unstructured documents** (PDFs, text files, entire directories)
- 🔍 **Retrieve semantically relevant chunks** using vector similarity search
- 🧠 **Generate grounded, accurate answers** using LLMs (Qwen 2.5 via Featherless AI)
- 📊 **Evaluate retrieval and generation quality** with built-in metrics (Precision, Recall, F1, MRR, Jaccard Stability)
- 🔐 **Isolate data per tenant** — each organization's data is completely separated

Whether you're building an internal knowledge base, document Q&A system, or AI-powered search engine, Atlas AI gives you the full pipeline out of the box.

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

## ✨ Key Features

### 🔐 Multi-Tenant Authentication

- JWT-based authentication with secure password hashing (`bcrypt`)
- Tenant isolation: every document, embedding, and query is scoped to its tenant
- Register and login endpoints with token-based session management

### 📥 Smart Document Ingestion

- **File hash tracking** — identical files are detected and skipped, saving compute
- **Factory Pattern** upload handling — supports PDFs, text files, and recursive directories
- **Two-stage chunking strategy:**
  1. **Token-based splitting** — breaks large documents into manageable windows (2000 tokens, 50 overlap)
  2. **Semantic chunking** — uses embedding similarity to split at natural semantic boundaries (90th percentile breakpoint), ensuring each chunk is topically coherent

### 🔍 Semantic Retrieval

- Dense vector search via **Qdrant** with per-tenant collection namespaces
- Embeddings powered by a singleton `EmbeddedModel` (lazy-loaded for efficiency)
- LangChain `Retriever` interface for flexible downstream integration

### 🧠 LLM Answer Generation

- Powered by **Qwen 2.5-1.5B-Instruct** via **Featherless AI** (HuggingFace Inference API)
- Context-grounded prompting — answers extracted from retrieved documents only
- Hallucination-resistant prompting with explicit "I don't know" fallback

### 📊 Comprehensive Evaluation Suite

- **Precision / Recall / F1** — measures whether the right documents were retrieved
- **MRR (Mean Reciprocal Rank)** — how early relevant results appear
- **Jaccard Stability** — measures how consistently the retriever returns the same docs across multiple runs
- **Rephrase Stability** — tests if retrieval is robust to paraphrased questions
- **Token F1** — keyword overlap between LLM answer and reference ground truth
- **MLflow integration** — all experiment metrics are tracked and versioned

### ⚙️ Background Processing

- **Celery** worker support for async document ingestion tasks
- Decoupled processing: API responds immediately, Celery handles heavy lifting

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
├── alembic/                        # Database migration scripts
│   └── versions/                   # Auto-generated migration files
│
├── app/
│   ├── core/                       # Database session, config
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── user.py                 # User model
│   │   ├── tenant.py               # Tenant model
│   │   ├── documents.py            # Document tracking model
│   │   └── TRACKER_DB_FILE.py      # File hash tracker model
│   │
│   ├── routes/                     # FastAPI route definitions
│   │   ├── auth_route.py           # POST /auth/register, /auth/login
│   │   ├── ingest_rag_route.py     # POST /ingest-rag/upload_file
│   │   └── eval_pipline.py         # Evaluation endpoints
│   │
│   ├── controllers/                # Request handling logic
│   ├── services/                   # Business logic layer
│   │   ├── auth_admin_service.py   # Auth & user management
│   │   ├── ingest_rag_service.py   # Document ingestion orchestration
│   │   ├── llm_runner.py           # LLM call abstraction
│   │   ├── eval_pipline.py         # Evaluation orchestration
│   │   └── path_processing_service.py  # File/directory routing
│   │
│   ├── repositories/               # Database access layer (Repository Pattern)
│   ├── schema/                     # Pydantic request/response models
│   │
│   ├── design_pattern/             # Design pattern implementations
│   │   ├── embedded_model.py       # Singleton embedding model
│   │   ├── llm_singlton.py         # Singleton LLM client
│   │   ├── upload_factory.py       # Factory entry point for uploads
│   │   └── upload_factory_pattern/ # Strategy-based file type handlers
│   │
│   ├── rag/                        # Core RAG Logic
│   │   ├── ingest_data_pipline.py  # Full ingestion pipeline orchestrator
│   │   ├── retrivel_data_pipline.py # Retrieval pipeline
│   │   │
│   │   ├── steps/                  # Individual pipeline steps
│   │   │   ├── loader.py           # Document loaders (PDF, TXT, etc.)
│   │   │   ├── ingest.py           # Qdrant ingestion step
│   │   │   ├── retriever.py        # Vector retriever setup
│   │   │   ├── embeddings.py       # Embedding computation
│   │   │   ├── semantic_chunking_function.py  # Two-stage chunker
│   │   │   └── file_tracker.py     # Hash-based file deduplication
│   │   │
│   │   └── evaluation/             # RAG evaluation framework
│   │       ├── eval_pipline.py     # Evaluation orchestrator
│   │       ├── generate_eval_dataset.py    # Synthetic Q&A dataset generator
│   │       ├── relevance_evaluation.py     # Precision/Recall/F1/MRR
│   │       ├── retrieval_stability.py      # Jaccard & rephrase stability
│   │       └── evaluation_dataset.json     # Sample eval dataset
│   │
│   └── celery/                     # Async task workers
│
├── mlruns/                         # MLflow experiment tracking data
├── digrams/                        # Architecture diagrams
└── SRS/                            # Software Requirements Specification
```

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

## 📡 API Reference

Interactive docs available at: `http://localhost:8000/docs`

### 🔐 Authentication

| Method | Endpoint         | Description                 |
| ------ | ---------------- | --------------------------- |
| `POST` | `/auth/register` | Register a new user         |
| `POST` | `/auth/login`    | Login and receive JWT token |

**Register Example:**

```json
POST /auth/register
{
  "username": "jane.doe@company.com",
  "password": "SecurePass123",
  "tenant_id": 1
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR...",
  "token_type": "bearer"
}
```

---

### 📥 Document Ingestion

| Method | Endpoint                  | Description                                      |
| ------ | ------------------------- | ------------------------------------------------ |
| `POST` | `/ingest-rag/upload_file` | Ingest a file or directory into the RAG pipeline |

**Request Body:**

```json
POST /ingest-rag/upload_file
{
  "file_path": "/data/documents/annual_report.pdf",
  "tenant_id": 1,
  "source": "annual_report.pdf",
  "author": "Finance Team",
  "recursive": false,
  "file_extensions": [".pdf", ".txt"]
}
```

**Response:**

```json
{
  "message": "File processed and ingested successfully",
  "result": {
    "status": "success",
    "chunks_stored": 42
  }
}
```

> 💡 Set `recursive: true` and provide a directory path to batch-ingest entire folders of documents.

---

### 📊 Evaluation

| Method | Endpoint        | Description                     |
| ------ | --------------- | ------------------------------- |
| `POST` | `/eval-rag/...` | Trigger RAG pipeline evaluation |

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
    │
    └─► Return Top-K Relevant Document Chunks
```

---

## 📊 Evaluation Framework

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

_Upload → Search → Answer → Evaluate → Repeat_

</div>
