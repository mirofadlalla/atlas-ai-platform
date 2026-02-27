# Atlas AI System Diagrams & Architecture

Comprehensive visual documentation of the Atlas AI system's core workflows, data flows, and component interactions.

---

## Table of Contents

1. [Agent Reasoning Loop](#agent-reasoning-loop)
2. [Document Ingestion Pipeline](#document-ingestion-pipeline)
3. [Query Retrieval Pipeline](#query-retrieval-pipeline)
4. [Authentication & Authorization Flow](#authentication--authorization-flow)
5. [Multi-Tenant Data Isolation](#multi-tenant-data-isolation)
6. [Cost Tracking & Logging](#cost-tracking--logging)
7. [System Architecture Overview](#system-architecture-overview)

---

## Agent Reasoning Loop

### 4-Node Agent State Graph

```
                                    User Question
                                         │
                                         ▼
                          ┌──────────────────────────┐
                          │     THOUGHT NODE 🧠      │
                          │  Question Analysis &     │
                          │  Action Decision         │
                          └────────────┬─────────────┘
                                       │
                        ┌──────────────┼──────────────┐
                        │              │              │
                        ▼              ▼              ▼
                   SQL Node      RETRIEVAL      FINISH
                   (Data)        (Knowledge)    (Answer)
                   │              │              │
                   └──────────────┬──────────────┘
                                  │
                                  ▼
                        ┌──────────────────────────┐
                        │  Response to User (SSE)  │
                        └──────────────────────────┘
```

### Detailed Agent Sequence: SQL Question

**User Query:** "How many users registered in Q4?"

```
Step 1: User sends question to /agent/ask-agent
  │
  ├─► THOUGHT NODE ────────────────────────────────
  │   ├─► Analyze: "how many" + "users" = SQL_NEEDED
  │   ├─► Check: Has SQL been executed? No
  │   ├─► Check: Question requires DATA? Yes
  │   └─► Decision: action = "sql"
  │
  ├─► ROUTER ──────────────────────────────────────
  │   ├─► Validate: step_count < 10? Yes
  │   ├─► Validate: No data gathered? Yes
  │   ├─► Safety: Question needs data, no data yet
  │   └─► Route to: sql_node
  │
  ├─► SQL NODE ────────────────────────────────────
  │   ├─► SQL Generation:
  │   │   └─► Prompt: "Generate SQL for 'How many users registered in Q4?'"
  │   ├─► SQL Validator:
  │   │   ├─► Inject: WHERE tenant_id = <current_tenant>
  │   │   └─► Check: Allowed keywords, no injection risk
  │   ├─► SQL Execution:
  │   │   └─► Execute: SELECT COUNT(*) FROM users WHERE ...
  │   ├─► Result:
  │   │   └─► 5 users registered in Q4
  │   └─► Observation:
  │       └─► "SQL executed: Found 1 record: [{'count': 5}]"
  │
  ├─► ROUTER (2nd iteration) ──────────────────────
  │   ├─► Check: step_count < 10? Yes
  │   ├─► Check: Data available? Yes (SQL result)
  │   ├─► Check: Question answered? Yes
  │   └─► Route to: finish_node
  │
  ├─► FINISH NODE ─────────────────────────────────
  │   ├─► Compile Data:
  │   │   ├─► SQL Results: 5 users
  │   │   ├─► Observation History: [...thoughts and steps...]
  │   │   └─► Gathered Context: All available data
  │   ├─► Generate Answer:
  │   │   └─► LLM Prompt: "Based on the data gathered, answer the question"
  │   ├─► Answer Output:
  │   │   └─► "5 users registered in Q4 2024"
  │   └─► Return: final_answer + metadata
  │
  └─► STREAM TO USER ──────────────────────────────
      └─► {"type": "answer", "content": "5 users registered in Q4..."}
```

### Detailed Agent Sequence: Knowledge Question

**User Query:** "What is Access Control Model?"

```
Step 1: User sends question to /agent/ask-agent
  │
  ├─► THOUGHT NODE ────────────────────────────────
  │   ├─► Analyze: "what is" + "definition" = RETRIEVAL_NEEDED
  │   ├─► Check: KnowledgeBase search needed? Yes
  │   └─► Decision: action = "retrieval"
  │
  ├─► ROUTER ──────────────────────────────────────
  │   ├─► Validate: step_count < 10? Yes
  │   ├─► Validate: No data gathered? Yes
  │   └─► Route to: retrieval_node
  │
  ├─► RETRIEVAL NODE ──────────────────────────────
  │   ├─► Embed Question:
  │   │   └─► Convert to vector using HF embeddings
  │   ├─► Qdrant Search:
  │   │   ├─► Search in tenant namespace
  │   │   ├─► Top-K: 5 documents
  │   │   └─► Filter: similarity > 0.7
  │   ├─► Rerank Results:
  │   │   ├─► Cross-Encoder scoring
  │   │   ├─► BM25 relevance
  │   │   └─► Hybrid score = 70% semantic + 30% lexical
  │   ├─► Top Results:
  │   │   ├─► Doc 1: "ACM is authorization model..."
  │   │   ├─► Doc 2: "Access control mechanisms include..."
  │   │   └─► Doc 3: "Models like RBAC, ABAC..."
  │   └─► Observation:
  │       └─► "Retrieved 3 relevant documents about Access Control Models"
  │
  ├─► ROUTER (2nd iteration) ──────────────────────
  │   ├─► Check: Data available? Yes (retrieved docs)
  │   └─► Route to: finish_node
  │
  ├─► FINISH NODE ─────────────────────────────────
  │   ├─► Compile Data:
  │   │   ├─► Retrieved Documents: 3 documents
  │   │   └─► Observation History: [thoughts]
  │   ├─► Generate Answer:
  │   │   └─► LLM Prompt: "Use retrieved docs to answer question"
  │   ├─► Answer Output:
  │   │   └─► "Access Control Model is... [comprehensive answer from docs]"
  │   └─► Return: final_answer + sources
  │
  └─► STREAM TO USER ──────────────────────────────
      └─► {"type": "answer", "content": "Access Control Model is..."}
```

---

## Document Ingestion Pipeline

### Complete Ingestion Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        FILE INPUT                               │
│  (PDF, TXT, JSON, Directory path, multiple files)               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
   ┌─────────────────┐            ┌──────────────────────┐
   │  HASH CHECK     │            │  SINGLE FILE or      │
   │  MD5 calculate  │            │  DIRECTORY?          │
   └────────┬────────┘            └──────────┬───────────┘
            │                                │
    ┌───────┴────────┐           ┌──────────┴─────────────┐
    │                │           │                        │
    ▼                ▼           ▼                        ▼
 FOUND         NOT FOUND     DIRECTORY             SINGLE FILE
 IN DB         (New File)    (Recursive)              │
 │             │             │                        │
 │ SKIP        │             │ Process each            │ LOAD
 │ RETURN      │             │  file in dir            │ FILE
 │ PREVIOUS    │             │                        │
 │ CHUNKS      │             └────────────────────────┘
 │             │                        │
 │             └────────────┬───────────┘
 │                          │
 │                          ▼
 │            ┌──────────────────────────┐
 │            │  LOAD DOCUMENT           │
 │            │  Extract text from PDF/  │
 │            │  TXT/JSON/etc            │
 │            └────────────┬─────────────┘
 │                         │
 └─────────────┬───────────┘
               │
               ▼
    ┌──────────────────────────┐
    │  STAGE 1: TOKEN SPLIT    │
    │  ├─ Chunk size: 2000 tok │
    │  ├─ Overlap: 50 tokens   │
    │  └─ Fast & predictable   │
    └────────────┬─────────────┘
                 │
                 ▼
    ┌──────────────────────────┐
    │  STAGE 2: SEMANTIC CHUNK │
    │  ├─ Embed chunks (HF)    │
    │  ├─ Calculate similarity │
    │  ├─ Find breakpoints at  │
    │  │  90th percentile drop │
    │  └─ Topically coherent   │
    └────────────┬─────────────┘
                 │
                 ▼
    ┌──────────────────────────┐
    │  GENERATE CHUNK IDS      │
    │  MD5(tenant_id +         │
    │       source +           │
    │       chunk_text)        │
    └────────────┬─────────────┘
                 │
                 ▼
    ┌──────────────────────────┐
    │  EMBED CHUNKS            │
    │  HuggingFace Embeddings  │
    │  Model: (768-dim)        │
    └────────────┬─────────────┘
                 │
                 ▼
    ┌──────────────────────────┐
    │  STORE IN QDRANT         │
    │  ├─ Per-tenant namespace │
    │  ├─ Vector storage       │
    │  └─ Metadata indexing    │
    └────────────┬─────────────┘
                 │
                 ▼
    ┌──────────────────────────┐
    │  LOG FILE PROCESSED      │
    │  ├─ Hash stored in PG    │
    │  ├─ Chunk count          │
    │  └─ Timestamp            │
    └──────────────────────────┘
```

### Chunking Strategy Comparison

```
DOCUMENT: "The quick brown fox jumps over the lazy dog. It is a well-known pangram..."

STAGE 1: TOKEN-BASED SPLIT (2000 tokens, 50 overlap)
┌─────────────────────────────────────────────────────────┐
│ Chunk 1: [0-2000 tokens]                                │
│ "The quick brown fox jumps over the lazy dog. It is..." │
├─────────────────────────────────────────────────────────┤
│ Chunk 2: [1950-3950 tokens] (50 token overlap)          │
│ "...well-known pangram. The document continues with..." │
└─────────────────────────────────────────────────────────┘

STAGE 2: SEMANTIC REFINEMENT (Natural breakpoints)
┌─────────────────────────────────────────────────────────┐
│ Semantic Chunk 1:                                       │
│ "The quick brown fox jumps over the lazy dog."          │
│ [Coherent: single topic - animal description]          │
├─────────────────────────────────────────────────────────┤
│ Semantic Chunk 2:                                       │
│ "It is a well-known pangram that uses every letter..." │
│ [Coherent: single topic - pangram definition]          │
└─────────────────────────────────────────────────────────┘

RESULT: Topically-coherent chunks at natural semantic boundaries
- Chunk 1 focuses on one idea
- Chunk 2 focuses on another idea
- No topic overlap between chunks
```

---

## Query Retrieval Pipeline

### RAG Pipeline: From Question to Answer

```
┌──────────────────────────────────────────────────────────────────┐
│                    USER QUESTION                                  │
│               "What was Q3 revenue in 2023?"                      │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
      ┌────────────────────────────────┐
      │  1. QUESTION EMBEDDING         │
      │  HuggingFace Encoder           │
      │  Vector: 768-dimensional       │
      └────────────┬───────────────────┘
                   │
                   ▼
      ┌────────────────────────────────┐
      │  2. VECTOR SEARCH (Qdrant)     │
      │  ├─ Tenant namespace scoped    │
      │  ├─ Top-50 candidates          │
      │  └─ Initial ranking            │
      └────────────┬───────────────────┘
                   │
        ┌──────────┴──────────┐
        │   Keep reranking?   │
        ├──────────┬──────────┤
        │ NO       │ YES      │
        │          │          │
        ▼          ▼          ▼
      Pass    ┌─────────────────────┐
      to LLM  │ 3. RERANKING        │
              ├─────────────────────┤
              │ Strategy Options:   │
              │ • Cross-Encoder ━━  │
              │   Semantic scoring  │
              │ • BM25 ━━━━━━━━━━  │
              │   Lexical matching  │
              │                     │
              │ HYBRID (Recommended)│
              │ 70% semantic +      │
              │ 30% lexical         │
              └──────────┬──────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │ Top-5 Reranked Docs   │
              └──────────┬────────────┘
                         │
         ┌───────────────┴────────────────┐
         │                                │
         ▼                                ▼
    ┌─────────────────────┐  ┌──────────────────────────┐
    │ LLM GENERATION      │  │ ALTERNATIVE FLOW:        │
    │ (Grounded Prompting)│  │ Return Ranked List       │
    │                     │  │ (Reranking only)         │
    │ Prompt Template:    │  │                          │
    │ "Using only the     │  │ For: Document retrieval  │
    │ provided context,   │  │ without LLM synthesis    │
    │ answer the question"│  │                          │
    └──────────┬──────────┘  └──────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────┐
    │ 4. TOKEN COUNTING                │
    │ ├─ Input tokens: Q + context     │
    │ ├─ Output tokens: Answer         │
    │ └─ Track for cost                │
    └────────────┬─────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │ 5. STREAMING RESPONSE (SSE)      │
    │ Send tokens in real-time to user │
    │ as they're generated             │
    └────────────┬─────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │ 6. LOGGING & ANALYTICS           │
    │ ├─ Store query in 'runs' table   │
    │ ├─ Store costs in 'cost_log'     │
    │ ├─ Track retrieved document IDs  │
    │ ├─ Calculate latency             │
    │ └─ Detect cache hit              │
    └──────────────────────────────────┘
```

### Reranking Strategy Comparison

```
SCENARIO: Query about "effective tax rate"
Retrieved 5 documents:

┌─────────────────────────────────────────────────────────────────┐
│ DOC  │ CONTENT                    │ VEC │ BM25 │ CE  │ HYBRID   │
├──────┼────────────────────────────┼─────┼──────┼─────┼──────────┤
│ 1    │ "Tax rate of 21% in 2023"  │ 0.9 │ 0.8  │ 0.95│ 0.90 ▲   │
│ 2    │ "Interest rate 2%..."      │ 0.7 │ 0.6  │ 0.5 │ 0.65     │
│ 3    │ "Tax compliance..."        │ 0.8 │ 0.7  │ 0.7 │ 0.74     │
│ 4    │ "Mortgage rate 4.2%..."    │ 0.6 │ 0.7  │ 0.4 │ 0.62     │
│ 5    │ "Sales tax rate 8%..."     │ 0.6 │ 0.9  │ 0.5 │ 0.68     │
└─────────────────────────────────────────────────────────────────┘

VECTOR SIMILARITY (Initial): Doc1=0.9, Doc3=0.8, Doc2=0.7, ...
BM25 LEXICAL:           Doc5=0.9, Doc1=0.8, Doc3=0.7, ...
CROSS-ENCODER:          Doc1=0.95, Doc3=0.7, Doc2=0.5, ...
HYBRID (70% CE + 30%):  Doc1=0.90, Doc3=0.74, Doc5=0.68, ...

FINAL RANKING: 1 → 3 → 5 → 2 → 4
✓ Most relevant at top (Doc1: "Tax rate 21%")
```

---

## Authentication & Authorization Flow

### User Registration with Approval Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│                    USER SELF-SIGNUP                              │
│              POST /auth/register                                 │
│         { email, password, tenant_id }                           │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────────┐
         │  VALIDATE EMAIL & PASSWORD      │
         │  ├─ Email format check          │
         │  ├─ Password strength (8+ char) │
         │  └─ Unique email in tenant      │
         └────────────┬────────────────────┘
                      │
             ┌────────┴─────────┐
             │                  │
         VALID            INVALID
             │                  │
             ▼                  ▼
    ┌─────────────────┐  RETURN ERROR
    │ HASH PASSWORD   │
    │ bcrypt(pw)      │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────┐
    │ CREATE USER RECORD      │
    │ status = 'pending'      │
    │ (if approval required)  │
    │    OR                   │
    │ status = 'approved'     │
    │ (if self-signup enabled)│
    └────────┬────────────────┘
             │
             ▼
    ┌─────────────────────────┐
    │ GENERATE JWT TOKEN      │
    │ Claims:                 │
    │ ├─ sub: user_id         │
    │ ├─ tenant_id: XXX       │
    │ ├─ role: user/admin     │
    │ └─ exp: +30min          │
    └────────┬────────────────┘
             │
             ▼
    ┌─────────────────────────┐
    │ ADMIN APPROVAL STEP     │
    │ (if configured)         │
    │                         │
    │ Admin views pending     │
    │ users in dashboard      │
    │                         │
    │ Admin approves OR       │
    │ Admin rejects           │
    │                         │
    │ User status updated     │
    └────────┬────────────────┘
             │
             ▼
    ┌─────────────────────────┐
    │ RETURN RESPONSE         │
    │ {                       │
    │   "access_token": JWT,  │
    │   "token_type": bearer, │
    │   "user": {...},        │
    │   "tenant": {...}       │
    │ }                       │
    └─────────────────────────┘
```

### JWT Token Validation on Every Request

```
CLIENT REQUEST:
GET /query/runs
Headers: {
  "Authorization": "Bearer eyJhbGc..."
}

                    ▼
        ┌───────────────────────────┐
        │ EXTRACT TOKEN FROM HEADER │
        └───────────┬───────────────┘
                    │
                    ▼
        ┌───────────────────────────┐
        │ DECODE JWT SIGNATURE      │
        │ ├─ Use SECRET_KEY         │
        │ ├─ Verify HS256 algorithm │
        │ └─ Check not tampered     │
        └───────────┬───────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
      VALID              INVALID
         │                     │
         ▼                     ▼
    ┌─────────────┐       REJECT 401
    │ CHECK EXP   │
    │ exp > now?  │
    └────┬────────┘
         │
    ┌────┴──────┐
    │            │
  VALID      EXPIRED
    │            │
    ▼            ▼
EXTRACT     REJECT 401
 CLAIMS   (Token expired)
    │
    ├─ user_id
    ├─ tenant_id
    ├─ role
    │
    ▼
┌──────────────────────────────────┐
│ LOAD USER & VALIDATE PERMISSION  │
│ ├─ Fetch user record             │
│ ├─ Check: status = 'approved'    │
│ ├─ Check: role permissions       │
│ └─ Bind tenant_id to request     │
└──────────┬───────────────────────┘
           │
   ┌───────┴──────┐
   │              │
 ALLOW       DENY
   │              │
   ▼              ▼
PROCEED     REJECT 403
REQUEST    (Forbidden)
   │
   └─► All subsequent DB queries
       automatically filtered by
       tenant_id
```

---

## Multi-Tenant Data Isolation

### Complete Data Isolation Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM ARCHITECTURE                           │
│                     (3 Isolation Levels)                         │
└─────────────────────────────────────────────────────────────────┘

LEVEL 1: VECTOR DATABASE (Qdrant)
┌────────────────────────────────────────────────────────────┐
│                      QDRANT                                 │
│                                                             │
│  ┌─────────────────┐  ┌──────────────────┐               │
│  │ Tenant A NS     │  │ Tenant B NS      │ ...             │
│  │ Collections:    │  │ Collections:     │                │
│  │ ├─ atlas_1234   │  │ ├─ atlas_5678    │                │
│  │ │  40k vectors  │  │ │  25k vectors   │                │
│  │ │  Tenant-only   │  │ │  Tenant-only   │                │
│  │ │  data          │  │ │  data          │                │
│  │ └─ chunk metadata│  │ └─ chunk metadata│                │
│  └─────────────────┘  └──────────────────┘                │
│                                                             │
│  NAMESPACE ISOLATION:                                       │
│  - Each tenant has separate collection namespace            │
│  - Queries scoped to tenant namespace only                  │
│  - Zero cross-tenant vector leakage                         │
└────────────────────────────────────────────────────────────┘

LEVEL 2: RELATIONAL DATABASE (PostgreSQL)
┌────────────────────────────────────────────────────────────┐
│                    PostgreSQL DB                            │
│                                                             │
│  USERS Table:                   DOCUMENTS Table:           │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ id           │              │ id           │            │
│  │ tenant_id ◄──┼──────────────┼─ tenant_id   │            │
│  │ email        │              │ file_path    │            │
│  │ password_hash│              │ chunk_count  │            │
│  └──────────────┘              └──────────────┘            │
│                                                             │
│  COST_LOG Table:                RUNS Table:               │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ id           │              │ id           │            │
│  │ tenant_id ◄──┼──────────────┼─ tenant_id   │            │
│  │ tokens       │              │ query        │            │
│  │ cost_usd     │              │ answer       │            │
│  └──────────────┘              └──────────────┘            │
│                                                             │
│  ISOLATION MECHANISM:                                       │
│  - Every table has tenant_id foreign key                   │
│  - All queries filtered: WHERE tenant_id = <current>       │
│  - Repository layer enforces tenant filtering              │
│  - No cross-tenant queries possible                        │
│  - Database integrity constraints prevent violations       │
└────────────────────────────────────────────────────────────┘

LEVEL 3: API LAYER (FastAPI)
┌────────────────────────────────────────────────────────────┐
│                    FastAPI Endpoints                        │
│                                                             │
│  Request Flow:                                              │
│                                                             │
│  1. JWT Token Validation:                                   │
│     ├─ Extract tenant_id from token                        │
│     └─ Bind to request context                             │
│                                                             │
│  2. Endpoint Handler:                                       │
│     ├─ Receive request                                     │
│     ├─ Use tenant_id from context (NOT from body)          │
│     └─ Pass to service layer                               │
│                                                             │
│  3. Service Layer:                                          │
│     ├─ Prepare SQL with: WHERE tenant_id = <context>       │
│     ├─ Prepare Qdrant filter: namespace = <context>       │
│     └─ Execute queries                                     │
│                                                             │
│  4. Repository Layer:                                       │
│     ├─ Only queries rows with matching tenant_id           │
│     └─ Prevents any data leakage                           │
│                                                             │
│  EXAMPLE - SQL Query Auto-Filtering:                        │
│  ┌─────────────────────────────────────────────┐           │
│  │ Original SQL from LLM:                       │           │
│  │ SELECT COUNT(*) FROM users WHERE status='on'│           │
│  │                                              │           │
│  │ Validator adds tenant filter:                │           │
│  │ SELECT COUNT(*) FROM users                  │           │
│  │ WHERE status='on'                           │           │
│  │ AND tenant_id = 'abc-123'                   │           │
│  └─────────────────────────────────────────────┘           │
└────────────────────────────────────────────────────────────┘

RESULT: ZERO CROSS-TENANT DATA ACCESS
┌────────────────────────────────────────────────────────────┐
│ Tenant A user cannot retrieve Tenant B data via:           │
│ ├─ Vector search (separate namespace)                      │
│ ├─ SQL queries (WHERE clause blocks)                       │
│ ├─ API endpoint (JWT tenant_id blocks)                     │
│ └─ Direct DB access (constraints prevent)                  │
│                                                             │
│ Data isolation is enforced at 3 independent layers         │
└────────────────────────────────────────────────────────────┘
```

---

## Cost Tracking & Logging

### Complete Cost Tracking Flow

```
USER INTERACTION:
  ├─ Ask Question (Streaming or Batch)
  └─ Query RAG system

                    ▼
        ┌───────────────────────────────┐
        │ AGENT/RAG EXECUTION           │
        │ ├─ Generate embedding         │
        │ ├─ Vector search (Qdrant)     │
        │ ├─ LLM generation             │
        │ └─ Optional: SQL query        │
        └───────────┬───────────────────┘
                    │
                    ▼
        ┌───────────────────────────────┐
        │ TOKEN COUNTING                │
        │ ├─ Call llm_runner            │
        │ ├─ Extract counts from API:   │
        │ │  ├─ input_tokens: N         │
        │ │  └─ output_tokens: M        │
        │ └─ Total tokens: N + M        │
        └───────────┬───────────────────┘
                    │
                    ▼
        ┌───────────────────────────────┐
        │ COST CALCULATION              │
        │ ├─ Model: Qwen2.5-1.5B        │
        │ ├─ Input rate: $0.00001/token │
        │ ├─ Output rate: $0.00001/token│
        │ │                              │
        │ │ Cost = (N * 0.00001) +       │
        │ │        (M * 0.00001)         │
        │ │                              │
        │ └─ Result: $0.00XY USD        │
        └───────────┬───────────────────┘
                    │
                    ▼
        ┌────────────────────────────────┐
        │ TWO PARALLEL PATHS:            │
        ├────────────────────────────────┤
        │                                │
        │ PATH 1: IMMEDIATE              │
        │ ├─ Store in 'runs' table       │
        │ │  ├─ query: "How many..."     │
        │ │  ├─ answer: "42 users"       │
        │ │  ├─ latency: 2.5s            │
        │ │  ├─ cache_hit: false         │
        │ │  └─ tenant_id: abc-123       │
        │ │                              │
        │ └─ Store in 'cost_log' table   │
        │    ├─ input_tokens: 145        │
        │    ├─ output_tokens: 32        │
        │    ├─ cost_usd: 0.00177        │
        │    ├─ model_name: Qwen2.5      │
        │    └─ tenant_id: abc-123       │
        │                                │
        │ PATH 2: BACKGROUND (Celery)   │
        │ ├─ Trigger async logging task  │
        │ ├─ Queue with Celery           │
        │ ├─ Worker processes async      │
        │ └─ Stores detailed metrics     │
        └────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────┐
        │ ANALYTICS AVAILABLE            │
        │ ├─ Cost per tenant             │
        │ ├─ Cost trends over time       │
        │ ├─ Cost by model               │
        │ ├─ Cost by question type       │
        │ ├─ Total tokens used           │
        │ ├─ Average latency             │
        │ └─ Cache hit rate              │
        └───────────────────────────────┘

QUERY EXAMPLES:
┌────────────────────────────────────────────┐
│ Get Cost Analytics:                        │
│ GET /query/cost-analytics                  │
│                                            │
│ Returns:                                   │
│ [                                          │
│   {                                        │
│     "model_name": "Qwen2.5-1.5B",          │
│     "total_cost": 45.32,                   │
│     "input_tokens": 14234,                 │
│     "output_tokens": 5123                  │
│   },                                       │
│   {...}                                    │
│ ]                                          │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ Get Recent Runs (Last 50):                 │
│ GET /query/runs                            │
│                                            │
│ Returns:                                   │
│ [                                          │
│   {                                        │
│     "run_id": "uuid-123",                  │
│     "query": "How many users...",          │
│     "answer": "42 users...",               │
│     "latency": 2.5,                        │
│     "cache_hit": false,                    │
│     "created_at": "2024-02-15T10:30:00"    │
│   },                                       │
│   {...}                                    │
│ ]                                          │
└────────────────────────────────────────────┘
```

---

## System Architecture Overview

### Complete System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                    │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  Web Browser (Next.js/React)  │  Mobile App  │  API Clients  │
│  └───────────────────┬───────────────────────────────────────┘   │
└──────────────────────┼──────────────────────────────────────────┘
                       │ HTTP/WebSocket
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FASTAPI APPLICATION                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Port 8000                                               │   │
│  │                                                          │   │
│  │  ROUTES:                                                 │   │
│  │  ├─ /auth/*                 (Authentication)            │   │
│  │  ├─ /ingest-rag/*           (Document ingestion)        │   │
│  │  ├─ /ask                    (RAG query)                 │   │
│  │  ├─ /retrieve               (Document retrieval)        │   │
│  │  ├─ /eval-rag/*             (Evaluation)                │   │
│  │  ├─ /agent/ask-agent        (Agentic AI)               │   │
│  │  ├─ /query/cost-analytics   (Cost data)                │   │
│  │  └─ /query/runs             (Query history)            │   │
│  │                                                          │   │
│  │  MIDDLEWARE:                                             │   │
│  │  ├─ JWT Validation (get_current_user)                   │   │
│  │  ├─ Tenant Isolation (Auto tenant_id binding)           │   │
│  │  └─ Rate Limiting                                       │   │
│  └──────┬───────────────────────────────────────────────────┘   │
└─────────┼──────────────────────────────────────────────────────┘
          │
          ├─────────────┬──────────────┬──────────────┐
          │             │              │              │
          ▼             ▼              ▼              ▼
    ┌─────────┐  ┌─────────┐  ┌──────────────┐  ┌────────────┐
    │Qdrant   │  │Postgres │  │HF Inference  │  │Celery      │
    │Vector DB│  │Database │  │LLM API       │  │Worker      │
    │         │  │         │  │              │  │            │
    │Port6333 │  │Port5432 │  │              │  │            │
    │         │  │         │  │ Qwen2.5 LLM  │  │Background  │
    │Per-     │  │Users    │  │              │  │Tasks       │
    │tenant   │  │Tenants  │  │              │  │            │
    │NS       │  │Docs     │  │              │  │Logging     │
    │         │  │Cost_Log │  │              │  │Cost Tracking
    │         │  │Runs     │  │              │  │            │
    │         │  │         │  │              │  │            │
    └─────────┘  └─────────┘  └──────────────┘  └────────────┘
```

### Data Flow: Query to Answer

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER SUBMITS QUESTION                                    │
│    POST /agent/ask-agent { "question": "..." }              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 2. API VALIDATES & AUTHENTICATES                            │
│    ├─ JWT token verification                               │
│    ├─ Extract tenant_id from claims                        │
│    └─ Bind to request context                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 3. AGENT ORCHESTRATOR (LangGraph)                           │
│    ├─ Initialize AgentState with question                  │
│    ├─ Route through 4-node graph                           │
│    │  ├─ Thought Node: Analyze & decide action             │
│    │  ├─ SQL/Retrieval Node: Get data                      │
│    │  ├─ Finish Node: Generate answer                      │
│    │  └─ Router: Control flow between nodes                │
│    └─ Maintain observation_history (audit trail)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
    ┌─────────┐               ┌──────────────┐
    │SQL PATH │               │RETRIEVAL PATH│
    │         │               │              │
    │Generate │               │Embed Question│
    │↓        │               │↓             │
    │SQL      │               │Search Qdrant │
    │Query    │               │↓             │
    │↓        │               │Rerank Docs   │
    │Execute  │               │↓             │
    │Query    │               │Return Top-5  │
    │↓        │               │              │
    │Format   │               │              │
    │Results  │               │              │
    │↓        │               │              │
    │Return   │               │              │
    │To Agent │               │              │
    └────┬────┘               └──────┬───────┘
         │                           │
         └───────────────┬───────────┘
                         │
        ┌────────────────▼────────────────┐
        │ FINISH NODE: ANSWER SYNTHESIS   │
        │ ├─ Compile all observations     │
        │ ├─ Prompt LLM with gathered data│
        │ ├─ Generate comprehensive answer│
        │ └─ Count tokens for cost        │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │ LOGGING & COST TRACKING         │
        │ ├─ Save to 'runs' table         │
        │ ├─ Save to 'cost_log' table     │
        │ ├─ Trigger Celery background    │
        │ │  task for detailed logging    │
        │ └─ Update analytics             │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼────────────────┐
        │ STREAM TO USER (SSE)            │
        │ ├─ Send thought process         │
        │ ├─ Send tool execution status   │
        │ ├─ Send final answer            │
        │ └─ Send metadata (cost, tokens) │
        └────────────────────────────────┘
```

---

## Performance & Scalability

### Request Latency Breakdown

```
TYPICAL RESPONSE TIME: 2.5 seconds

├─ JWT Validation: 5ms
├─ Agent Initialization: 10ms
├─ Thought Node (LLM): 300ms
│   └─ HF Inference API call
├─ Data Gathering (parallel or sequential)
│   ├─ SQL Node (if needed): 400ms
│   │  ├─ SQL Generation (LLM): 200ms
│   │  ├─ Query Execution: 150ms
│   │  └─ Formatting: 50ms
│   └─ Retrieval Node (if needed): 350ms
│      ├─ Embedding: 100ms
│      ├─ Vector Search: 150ms
│      └─ Reranking: 100ms
├─ Finish Node (LLM): 600ms
│   └─ Answer generation and streaming
├─ Cost Calculation: 5ms
├─ Logging: 10ms
└─ Network overhead: 200ms

OPTIMIZATION OPPORTUNITIES:
├─ Parallel SQL + Retrieval execution (save ~350ms)
├─ Embedding caching (save ~50ms on repeated Q)
├─ Prompt optimization (reduce LLM tokens)
├─ Batch mode (save streaming overhead ~100ms)
└─ Model quantization (if self-hosted)
```

### Scalability Considerations

```
SINGLE INSTANCE CAPACITY:
├─ Concurrent users: ~50-100
├─ QPS (Queries Per Second): ~20
├─ Memory: 4GB (Python + models)
└─ CPU: 2+ cores recommended

HORIZONTAL SCALING:
├─ Multiple API instances (load balanced)
├─ Celery workers (separate from API)
├─ Qdrant cluster (sharded by tenant)
├─ PostgreSQL read replicas
└─ Redis cache layer (optional)

BOTTLENECK ANALYSIS:
├─ LLM inference (HF API is external)
├─ Vector search (Qdrant indexing)
├─ SQL query execution
├─ Token counting (minimal)
└─ Network latency (varies by region)
```

---

## Conclusion

This document provides comprehensive visual documentation of the Atlas AI system's architecture and workflows. Use these diagrams to:

- **Onboard new developers** to the system architecture
- **Debug issues** by understanding data flow
- **Optimize performance** by identifying bottlenecks
- **Plan features** based on system constraints
- **Document decisions** with visual references

Last Updated: **February 27, 2026**
