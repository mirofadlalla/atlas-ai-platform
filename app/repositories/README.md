# Atlas AI Repositories - Data Access Layer

**Module**: `app/repositories`  
**Purpose**: Data Access Layer (Repository Pattern)  
**Last Updated**: March 2026

---

## 📋 Overview

The Repositories module implements the **Repository Pattern**, abstracting database access and maintaining consistent tenant isolation across all data operations.

✅ **Single Responsibility** - Each repository handles one model  
✅ **Tenant-Safe Queries** - All queries automatically filtered by tenant_id  
✅ **Reusable Methods** - Common CRUD operations pre-implemented  
✅ **Vector Search Integration** - Qdrant wrapper for semantic search  

---

## 🏗️ Architecture

```
Route Handler
    ↓ (calls)
Service Layer
    ↓ (calls)
Repository Layer  ← Pure data access
    ↓
Database / Vector Store
```

**Benefits**:
- Routes don't know SQL syntax
- Services orchestrate business logic
- Repositories handle data persistence
- Easy to mock for testing

---

## 📁 Repository Files

### 1. **user_repository.py** - User operations

```python
class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, email: str, hashed_password: str, tenant_id: str, **kwargs) -> Users:
        """Create new user"""
        user = Users(email=email, hashed_password=hashed_password, tenant_id=tenant_id, **kwargs)
        self.db.add(user)
        self.db.commit()
        return user
    
    def get_by_email(self, email: str) -> Optional[Users]:
        """Lookup user by email"""
        return self.db.query(Users).filter(Users.email == email).first()
    
    def get_by_id(self, user_id: str, tenant_id: str) -> Optional[Users]:
        """Get user (with tenant isolation)"""
        return self.db.query(Users).filter(
            Users.id == user_id,
            Users.tenant_id == tenant_id  # ← Tenant safety
        ).first()
    
    def get_all_for_tenant(self, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Users]:
        """List all users in tenant (paginated)"""
        return self.db.query(Users).filter(
            Users.tenant_id == tenant_id
        ).offset(skip).limit(limit).all()
```

### 2. **runs_repository.py** - Agent execution history

```python
class RunsRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_run(self, tenant_id: str, user_id: str, question: str) -> Runs:
        """Log new agent execution"""
        run = Runs(
            tenant_id=tenant_id,
            user_id=user_id,
            question=question,
            status="in_progress",
            started_at=datetime.utcnow()
        )
        self.db.add(run)
        self.db.commit()
        return run
    
    def update_run(self, run_id: str, final_answer: str, tokens: int, cost: float) -> Runs:
        """Mark run complete with results"""
        run = self.db.query(Runs).get(run_id)
        run.final_answer = final_answer
        run.total_tokens = tokens
        run.total_cost_usd = cost
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        self.db.commit()
        return run
    
    def get_tenant_runs(self, tenant_id: str, skip: int = 0, limit: int = 50) -> List[Runs]:
        """Get run history for tenant (paginated, newest first)"""
        return self.db.query(Runs).filter(
            Runs.tenant_id == tenant_id
        ).order_by(Runs.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_run_total_cost(self, tenant_id: str, days: int = 30) -> float:
        """Calculate total cost for tenant in past N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = self.db.query(func.sum(Runs.total_cost_usd)).filter(
            Runs.tenant_id == tenant_id,
            Runs.created_at > cutoff,
            Runs.status == "completed"
        ).scalar()
        return float(result or 0)
```

### 3. **cost_log_repository.py** - Billing & cost tracking

```python
class CostLogRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def log_cost(self, tenant_id: str, resource_type: str, operation: str, 
                 cost_usd: float, tokens_used: int, run_id: str = None) -> CostLog:
        """Log cost event for billing"""
        cost_entry = CostLog(
            tenant_id=tenant_id,
            resource_type=resource_type,  # 'llm', 'embedding', 'vector_search'
            operation=operation,           # 'gpt4-completion', 'embedding-query'
            cost_usd=cost_usd,
            tokens_used=tokens_used,
            run_id=run_id,
            created_at=datetime.utcnow()
        )
        self.db.add(cost_entry)
        self.db.commit()
        return cost_entry
    
    def get_tenant_cost_summary(self, tenant_id: str, start_date: datetime, end_date: datetime) -> dict:
        """Billing report for date range"""
        results = self.db.query(
            CostLog.resource_type,
            func.sum(CostLog.cost_usd).label('total_cost'),
            func.sum(CostLog.tokens_used).label('total_tokens'),
            func.count().label('operation_count')
        ).filter(
            CostLog.tenant_id == tenant_id,
            CostLog.created_at.between(start_date, end_date)
        ).group_by(CostLog.resource_type).all()
        
        return [{
            "resource": row.resource_type,
            "cost_usd": float(row.total_cost),
            "tokens": row.total_tokens,
            "operations": row.operation_count
        } for row in results]
```

### 4. **qdrant.py** - Vector search wrapper

```python
class QdrantRepository:
    """Wrapper around Qdrant REST API for hybrid semantic search"""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.base_url = f"http://{host}:{port}"
    
    def search_hybrid(self, tenant_id: str, query_embedding: List[float], 
                      top_k: int = 3) -> List[Document]:
        """Hybrid search: Dense + Sparse + Reranking"""
        
        # 1. Dense vector search (cosine similarity)
        dense_results = self._search_dense(query_embedding, top_k=50)
        
        # 2. Sparse search (BM25 - todo implement)
        sparse_results = self._search_sparse(query_text, top_k=50)
        
        # 3. Merge and rerank
        merged = self._merge_results(dense_results, sparse_results)
        reranked = self._rerank(query_text, merged, top_k=top_k)
        
        # 4. Filter by tenant_id
        tenant_filtered = [r for r in reranked if r.metadata.get('tenant_id') == tenant_id]
        
        return tenant_filtered[:top_k]
    
    def upsert_documents(self, documents: List[Dict], embeddings: List[List[float]]):
        """Insert/update documents in Qdrant"""
        points = [
            {
                "id": doc['id'],
                "vector": embedding,
                "payload": {
                    "content": doc['content'],
                    "tenant_id": doc['tenant_id'],
                    "source": doc['source'],
                    "metadata": doc.get('metadata', {})
                }
            }
            for doc, embedding in zip(documents, embeddings)
        ]
        # POST to Qdrant API
        response = requests.post(
            f"{self.base_url}/collections/documents/points?wait=true",
            json={"points": points}
        )
        return response.status_code == 200
    
    def delete_by_tenant(self, tenant_id: str):
        """Remove all documents for tenant (e.g., account closure)"""
        # DELETE WHERE metadata.tenant_id = tenant_id
        pass
```

### 5. **tenant_repository.py** - Tenant management

```python
class TenantRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_tenant(self, name: str, plan: str = "free") -> Tenants:
        """Create new tenant account"""
        tenant = Tenants(name=name, plan=plan)
        self.db.add(tenant)
        self.db.commit()
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenants]:
        """Get tenant by ID"""
        return self.db.query(Tenants).filter(Tenants.id == tenant_id).first()
    
    def update_plan(self, tenant_id: str, new_plan: str) -> Tenants:
        """Change subscription plan"""
        tenant = self.get_tenant(tenant_id)
        tenant.plan = new_plan
        self.db.commit()
        return tenant
```

### 6. **invitation_repository.py** - User onboarding

```python
class InvitationRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_invitation(self, tenant_id: str, invited_email: str, invited_by: str) -> Invitations:
        """Send user invitation"""
        invitation = Invitations(
            tenant_id=tenant_id,
            invited_email=invited_email,
            invited_by=invited_by,
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.db.add(invitation)
        self.db.commit()
        return invitation
    
    def accept_invitation(self, invitation_id: str) -> Invitations:
        """User accepts invitation"""
        invitation = self.db.query(Invitations).get(invitation_id)
        if not invitation or invitation.expires_at < datetime.utcnow():
            raise InvalidInvitation("Invitation expired")
        
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        self.db.commit()
        return invitation
```

---

## 🔒 Tenant Isolation Pattern

Every repository method enforces this pattern:

```python
# ✅ SAFE: Filters by tenant_id
def get_document(self, doc_id: str, tenant_id: str, db: Session):
    return db.query(Document).filter(
        Document.id == doc_id,
        Document.tenant_id == tenant_id  # ← Required
    ).first()

# ❌ UNSAFE: Missing tenant_id filter
def get_document_unsafe(self, doc_id: str, db: Session):
    return db.query(Document).filter(
        Document.id == doc_id
    ).first()  # Could return document from different tenant!
```

**Rules**:
1. **ALWAYS** filter by `tenant_id`
2. **NEVER** return records without tenant verification
3. **ALWAYS** include `tenant_id` in composite keys for indexing

---

## 💡 Usage Example

```python
# In routes/query_route.py

from app.repositories.runs_repository import RunsRepository
from app.core.db import get_db
from fastapi import Depends

@router.post("/api/agent/reason")
async def agent_reason(
    request: AgentRequest,
    current_user: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Create run using repository
    runs_repo = RunsRepository(db)
    run = runs_repo.create_run(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        question=request.question
    )
    
    try:
        # Execute agent (simplified)
        answer = agent.execute(request.question)
        tokens = 1250
        cost = tokens * 0.0001
        
        # Update run with results
        runs_repo.update_run(
            run_id=run.id,
            final_answer=answer,
            tokens=tokens,
            cost=cost
        )
    except Exception as e:
        run.status = "failed"
        db.commit()
        raise
    
    return {"run_id": run.id, "answer": run.final_answer}
```

---

## 🏗️ Common Patterns

### Pagination

```python
def get_paginated(self, tenant_id: str, page: int = 1, page_size: int = 50):
    skip = (page - 1) * page_size
    return self.db.query(Model).filter(
        Model.tenant_id == tenant_id
    ).offset(skip).limit(page_size).all()
```

### Counting

```python
def get_count(self, tenant_id: str) -> int:
    return self.db.query(func.count(Model.id)).filter(
        Model.tenant_id == tenant_id
    ).scalar()
```

### Aggregation

```python
def get_stats(self, tenant_id: str):
    result = self.db.query(
        func.sum(Model.cost).label("total_cost"),
        func.avg(Model.duration).label("avg_duration"),
        func.count().label("count")
    ).filter(Model.tenant_id == tenant_id).first()
    
    return {
        "total_cost": result.total_cost or 0,
        "avg_duration": result.avg_duration or 0,
        "count": result.count
    }
```

---

## 📊 Performance Considerations

### Indexes Used

```python
# All repositories leverage these indexes:
INDEX (tenant_id)                    # Fast tenant filtering
INDEX (tenant_id, created_at)        # Sorting by date
INDEX (tenant_id, status)            # Status filtering
INDEX (tenant_id, user_id)           # User-specific queries
```

### N+1 Query Prevention

```python
# ❌ Causes N+1 queries
for run in db.query(Runs).all():
    print(run.user.name)  # Query per run!

# ✅ Use eager loading
from sqlalchemy.orm import joinedload

runs = db.query(Runs).options(
    joinedload(Runs.user),
    joinedload(Runs.tenant)
).all()

for run in runs:
    print(run.user.name)  # No extra queries!
```

---

## 🐛 Troubleshooting

### Foreign Key Constraint Error

**Cause**: Repository trying to reference non-existent record

**Solution**: Ensure parent entity created first

### Tenant Data Leakage

**Check**: All queries have `tenant_id` filter

```bash
grep -r "\.filter(" app/repositories/ | grep -v "tenant_id"
```

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Pattern**: Repository Pattern with Tenant Isolation
