# Atlas AI Celery - Background Task Queue

**Module**: `app/celery`  
**Purpose**: Asynchronous task execution via Celery + RabbitMQ  
**Last Updated**: March 2026

---

## 📋 Overview

Celery handles long-running operations **asynchronously** without blocking HTTP responses:

✅ **Document Ingestion** - Process large files in background  
✅ **Evaluation Pipelines** - Run benchmarks without tying up workers  
✅ **Query Logging** - Write results to database after request completes  
✅ **Distributed** - Multiple workers process tasks in parallel  

---

## 🏗️ Architecture

```
FastAPI Route (client request)
    ↓
Route calls service.some_task.delay(args)  [enqueue to queue]
    ↓
RabbitMQ Broker (amqp://guest:guest@localhost:5672//)
    ├─ ingest_data_queue     [document processing]
    ├─ eval_data_queue       [evaluation tasks]
    ├─ logging_queue         [database logging]
    └─ queue_dead            [failed tasks]
    ↓
Celery Worker Pool
    ├─ Worker 1 (processes ingest tasks)
    ├─ Worker 2 (processes eval tasks)
    └─ Worker 3 (processes logging tasks)
    ↓
Task Result Backend (RabbitMQ RPC)
    ↓
Route polls result or client receives callback
```

---

## ⚙️ Configuration (`celery_config.py`)

```python
celery_app = Celery(
    "atlas_ai",
    broker="amqp://guest:guest@localhost:5672//",  # RabbitMQ connection
    backend="rpc://",                               # Result storage
)
```

### Task Queues

| Queue | Routing Key | Purpose | Max Duration |
|-------|-------------|---------|--------------|
| `ingest_data_queue` | `ingest` | Upload/ingest documents | 10 min |
| `eval_data_queue` | `eval` | Run evaluations | 10 min |
| `logging_queue` | `logging` | Write logs to DB | 10 min |
| `queue_dead` | `dead` | Failed task retries | N/A |

### Key Settings

```python
# Serialization
task_serializer = "json"              # Simple JSON encoding
result_serializer = "json"

# Worker Pool
worker_pool = "threads"               # Thread-based (Windows compatible)
worker_max_tasks_per_child = 10       # Restart after 10 tasks (memory leak prevention)
worker_prefetch_multiplier = 1        # One task at a time (prevent queue spam)

# Time Limits
task_soft_time_limit = 550 seconds    # 9:10 - graceful shutdown
task_time_limit = 600 seconds         # 10:00 - hard kill

# Reliability
task_acks_late = True                 # Ack only after completion (no loss)
task_reject_on_worker_lost = True     # Re-queue if worker dies
task_default_retry_delay = 30 seconds # Wait before retry
task_max_retries = 3                  # Max 3 attempts

# Tracking
task_track_started = True             # Monitor progress
timezone = "UTC"                      # Central time reference
```

---

## 🎯 Defined Tasks

### Task Routing

```python
celery_app.conf.task_routes = {
    "app.services.rag_services.ingest_rag_service.ingest_file_task": {
        "queue": "ingest_data_queue",
        "routing_key": "ingest",
    },
    "app.services.rag_services.eval_pipline.evaluate_task": {
        "queue": "eval_data_queue",
        "routing_key": "eval",
    },
    "app.services.rag_services.query_logging_service.log_query_run_and_cost": {
        "queue": "logging_queue",
        "routing_key": "logging",
    },
}
```

### Task Examples

**1. Ingest Document Task**

```python
# File: app/services/rag_services/ingest_rag_service.py
from app.celery.celery_config import celery_app

@celery_app.task(name="app.services.rag_services.ingest_rag_service.ingest_file_task")
def ingest_file_task(
    file_path: str,
    document_id: str,
    tenant_id: str,
    metadata: dict = None
) -> dict:
    """Ingest document: chunk → embed → store in Qdrant + DB"""
    
    try:
        # 1. Parse document
        chunks = parse_document(file_path)
        
        # 2. Embed chunks (heavy operation)
        embeddings = embed_batch(chunks)
        
        # 3. Store in Qdrant
        qdrant_repository.upsert_documents(
            document_id=document_id,
            tenant_id=tenant_id,
            chunks=chunks,
            embeddings=embeddings
        )
        
        # 4. Log to database
        log_ingest(document_id, len(chunks), success=True)
        
        return {
            "status": "completed",
            "chunks_created": len(chunks),
            "document_id": document_id
        }
    except Exception as e:
        log_ingest(document_id, 0, success=False, error=str(e))
        raise  # Celery will retry
```

**Usage from HTTP endpoint:**

```python
# File: app/routes/ingest_rag_route.py
from app.services.rag_services.ingest_rag_service import ingest_file_task

@router.post("/upload")
async def upload_document(file: UploadFile, current_user: TokenData = Depends(verify_token)):
    """Accept file upload, queue ingest task, return immediately"""
    
    # Save temporary file
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    # Queue task (returns immediately)
    task = ingest_file_task.delay(
        file_path=temp_path,
        document_id=str(uuid4()),
        tenant_id=current_user.tenant_id,
        metadata={"uploaded_by": current_user.email}
    )
    
    # Return task ID for polling
    return {
        "file_id": task.id,
        "filename": file.filename,
        "status": "queued"
    }
```

**2. Query Logging Task**

```python
# File: app/services/rag_services/query_logging_service.py
from app.celery.celery_config import celery_app

@celery_app.task(name="app.services.rag_services.query_logging_service.log_query_run_and_cost")
def log_query_run_and_cost(
    tenant_id: str,
    user_id: str,
    query: str,
    answer: str,
    tokens_used: int,
    cost_usd: float,
    duration_ms: float,
    cache_hit: bool = False
) -> dict:
    """Async log query execution to database"""
    
    db = get_db_session()
    try:
        # 1. Create Run record
        run = Runs(
            tenant_id=tenant_id,
            user_id=user_id,
            question=query,
            final_answer=answer,
            status="completed",
            total_tokens=tokens_used,
            total_cost_usd=cost_usd,
            duration_ms=duration_ms,
            metadata={"cache_hit": cache_hit}
        )
        db.add(run)
        db.commit()
        
        # 2. Log cost
        if cost_usd > 0:
            cost_log = CostLog(
                tenant_id=tenant_id,
                resource_type="llm",
                operation="query",
                cost_usd=cost_usd,
                tokens_used=tokens_used,
                run_id=str(run.id)
            )
            db.add(cost_log)
            db.commit()
        
        return {"status": "logged"}
    finally:
        db.close()
```

**Usage from query endpoint:**

```python
# File: app/routes/query_route.py
from app.services.rag_services.query_logging_service import log_query_run_and_cost

@router.post("/search")
async def search(
    request: QueryRequest,
    current_user: TokenData = Depends(verify_token)
):
    """Execute query and queue async logging"""
    
    # Execute query (synchronous RAG)
    result = rag_service.search(request.query)
    
    # Queue logging (non-blocking)
    log_query_run_and_cost.delay(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        query=request.query,
        answer=result.answer,
        tokens_used=result.tokens,
        cost_usd=result.cost_usd,
        duration_ms=result.duration_ms,
        cache_hit=result.cache_hit
    )
    
    # Return immediately
    return {
        "answer": result.answer,
        "duration_ms": result.duration_ms,
        "cost_usd": result.cost_usd
    }
```

---

## 🚀 Running Workers

### Development (Single Worker)

```bash
# Terminal 1: Start RabbitMQ
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management

# Terminal 2: Run Celery worker
cd atlas-ai
python -m celery -A app.celery.celery_config worker \
  --loglevel=info \
  --concurrency=4 \
  --pool=threads
```

### Production (Multiple Workers)

```bash
# Worker 1: Ingestion tasks
python -m celery -A app.celery.celery_config worker \
  --queues=ingest_data_queue \
  --hostname=ingest_worker@%h \
  --concurrency=2

# Worker 2: Evaluation tasks
python -m celery -A app.celery.celery_config worker \
  --queues=eval_data_queue \
  --hostname=eval_worker@%h \
  --concurrency=4

# Worker 3: Logging tasks
python -m celery -A app.celery.celery_config worker \
  --queues=logging_queue \
  --hostname=logging_worker@%h \
  --concurrency=8
```

### Docker Compose

```yaml
# docker-compose.yml
celery_worker_ingest:
  image: atlas-ai:latest
  command: celery -A app.celery.celery_config worker --queues=ingest_data_queue
  depends_on:
    - rabbitmq
    - postgres

celery_worker_eval:
  image: atlas-ai:latest
  command: celery -A app.celery.celery_config worker --queues=eval_data_queue
  depends_on:
    - rabbitmq
    - postgres
```

---

## 📊 Monitoring Tasks

### Celery Flower (UI Dashboard)

```bash
pip install flower

# Start Flower on http://localhost:5555
python -m celery -A app.celery.celery_config flower
```

Features:
- ✅ Real-time task execution
- ✅ Queue depth monitoring
- ✅ Worker status
- ✅ Task statistics (pending, arrived, started)
- ✅ Task details (args, result, traceback)

### Command Line Inspection

```bash
# List active tasks
celery -A app.celery.celery_config inspect active

# Check tasks in queue
celery -A app.celery.celery_config inspect reserved

# Get worker stats
celery -A app.celery.celery_config inspect stats

# Revoke task (cancel ongoing)
celery -A app.celery.celery_config revoke <task_id>
```

### Prometheus Metrics

Celery metrics must be exported manually:

```python
# File: app/core/monitors.py
from prometheus_client import Counter, Histogram

celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task_name", "status"]  # status: succeeded, failed, retried
)

celery_task_duration = Histogram(
    "celery_task_duration_seconds",
    "Task execution duration",
    ["task_name"]
)

# Middleware to track tasks
@celery_app.task(bind=True)
def my_task(self):
    try:
        # Task logic
        pass
        celery_tasks_total.labels(
            task_name=self.name,
            status="succeeded"
        ).inc()
    except Exception as e:
        celery_tasks_total.labels(
            task_name=self.name,
            status="failed"
        ).inc()
        raise
```

---

## ⚠️ Error Handling & Retries

### Automatic Retries

```python
@celery_app.task(
    name="my_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30
)
def my_task(self, arg1):
    try:
        # Task logic
        return result
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### Dead Letter Queue

```python
# Failed tasks route to queue_dead
Queue("queue_dead", default_exchange, routing_key="dead")

# Monitor dead letter queue
celery -A app.celery.celery_config inspect active
```

---

## 🔒 Security

**Message Signing** (optional, add if needed):

```python
celery_app.conf.update(
    security_key="/path/to/key.pem",
    security_certificate="/path/to/cert.pem",
    security_cert_store="/path/to/trust.pem"
)
```

**Authentication** (RabbitMQ credentials):

```bash
export CELERY_BROKER_URL=amqp://username:password@rabbitmq:5672//
```

---

## 📁 File Structure

```
app/celery/
├── README.md                ← You are here
├── celery_config.py         # Configuration and queues
└── __pycache__/
```

---

## 🧠 Best Practices

1. **Keep tasks small** - Should complete in seconds/minutes, not hours
2. **Idempotent tasks** - Safe to retry without side effects
3. **Use task routing** - Route to specific queues by task type
4. **Monitor queues** - Watch for backlog growth
5. **Version tasks** - Change task names when logic changes
6. **Error logging** - Capture exceptions with traceback
7. **Result backends** - Use Redis for faster result retrieval

---

## 🐛 Troubleshooting

| Issue | Check |
|-------|-------|
| Tasks stuck in queue | Worker running? RabbitMQ connection OK? |
| Tasks timing out | Increase `task_time_limit` if task legitimately slow |
| Memory leaks | Check `worker_max_tasks_per_child` is set |
| Tasks not retrying | Verify `task_acks_late = True` |
| No results returned | Check `backend` configuration (RPC or Redis) |

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Broker**: RabbitMQ 3.12+  
**Worker Pool**: Threads (Windows-compatible)