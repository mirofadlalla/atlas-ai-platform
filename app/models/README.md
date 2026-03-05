# Atlas AI Models - Database Schema & ORM Documentation

**Module**: `app/models`  
**Purpose**: SQLAlchemy ORM models defining database schema  
**Last Updated**: March 2026

---

## 📋 Overview

The Models module defines the complete database schema using SQLAlchemy ORM. Every model includes:

✅ **Multi-tenant Isolation** - `tenant_id` field on all significant tables  
✅ **UUID Primary Keys** - Globally unique identifiers  
✅ **Timestamps** - `created_at` and `updated_at` on audit tables  
✅ **Relationships** - Foreign key constraints with relationship loading  
✅ **Indexes** - Strategic indexing for query performance  

---

## 🏗️ Database Schema

### Core Tables

#### 1. **Tenants** (Multi-tenant accounts)

```python
class Tenants(Base):
    __tablename__ = 'tenants'
    
    id = UUIDField()              # Primary key (UUID)
    name = String(255)            # Tenant name
    plan = String(50)             # Subscription plan (free, pro, enterprise)
    created_at = DateTime         # Account creation timestamp
    
    users = relationship("Users") # One-to-many: 1 tenant -> many users
```

**Typical Records**:
- Tenant 1: "Acme Corp" (plan: enterprise)
- Tenant 2: "Startup Inc" (plan: pro)

#### 2. **Users** (Authentication & authorization)

```python
class Users(Base):
    __tablename__ = 'users'
    
    id = UUIDField()                       # Primary key
    name = String(255)                    # Full name
    email = String(255)                   # Unique email
    tenant_id = ForeignKey('tenants.id')  # Which tenant owns this user
    
    hashed_password = String()            # Bcrypt hashed password
    role = String(50)                     # 'admin', 'user', 'viewer'
    
    approval_status = String(50)          # 'approved', 'pending', 'rejected'
    approved_by = ForeignKey('users.id')  # Which admin approved this user
    approved_at = DateTime                # When was approval given
    
    created_at = DateTime                 # Account creation time
    
    # Relationships
    tenant = relationship("Tenants")      # Reference to parent tenant
```

**Multi-tenant Isolation**: Every user must belong to exactly one tenant

#### 3. **Runs** (Agent execution history)

```python
class Runs(Base):
    __tablename__ = 'runs'
    
    id = UUIDField()              # Primary key
    tenant_id = ForeignKey()      # Data isolation
    user_id = ForeignKey()        # Who executed it
    
    question = Text()             # User's original question
    final_answer = Text()         # Agent's synthesized answer
    
    # Tracking
    status = String()             # 'completed', 'failed', 'timeout'
    total_tokens = Integer()      # LLM tokens consumed
    total_cost_usd = Decimal()    # Cost of execution
    
    # Timing
    started_at = DateTime()       # Execution start
    completed_at = DateTime()     # Execution end
    duration_ms = Float()         # Total execution time
    
    # Full audit
    execution_trace = JSON()      # Step-by-step reasoning log
    metadata = JSON()             # Additional context
    
    INDEX (tenant_id, user_id)    # Fast lookup per tenant/user
```

**Purpose**: Complete audit trail of agent operations

#### 4. **CostLog** (Billing & cost tracking)

```python
class CostLog(Base):
    __tablename__ = 'costlog'
    
    id = UUIDField()
    tenant_id = ForeignKey()      # Tenant responsible for cost
    
    resource_type = String()      # 'llm', 'embedding', 'vector_search'
    operation = String()          # Specific operation (e.g., 'gpt4-completion')
    
    cost_usd = Decimal(10, 4)     # Cost in dollars
    tokens_used = Integer()       # Tokens consumed (if applicable)
    
    run_id = ForeignKey('runs.id') # Which agent run caused this cost
    query_id = ForeignKey()        # Which query (if applicable)
    
    created_at = DateTime()        # When cost was incurred
    
    INDEX (tenant_id, created_at)  # For billing queries
```

**Purpose**: Track all costs for billing and analytics

#### 5. **Runs** (Deprecated - kept for backward compatibility)

Used by agent for storing run results. See `runs.py`.

#### 6. **Documents** (Ingested documents)

```python
class Documents(Base):
    __tablename__ = 'documents'
    
    id = UUIDField()
    tenant_id = ForeignKey()     # Multi-tenant isolation
    
    filename = String()          # Original filename
    file_hash = String()         # MD5 hash for deduplication
    document_type = String()     # 'pdf', 'txt', 'docx'
    
    total_chunks = Integer()     # Number of chunks created
    storage_path = String()      # File storage location
    
    processed_at = DateTime()    # When ingestion completed
    created_at = DateTime()
```

#### 7. **Chunks** (Document segments)

```python
class Chunks(Base):
    __tablename__ = 'chunks'
    
    id = UUIDField()
    document_id = ForeignKey('documents.id')
    tenant_id = ForeignKey()     # Isolation + query efficiency
    
    content = Text()             # Chunk text
    embedding = Vector(384)      # Dense embedding (pgvector)
    
    metadata = JSON()            # {source, page, section, etc}
    chunk_index = Integer()      # Position in document
    
    created_at = DateTime()
    
    INDEX (tenant_id, document_id)
```

#### 8. **Invitations** (User onboarding workflow)

```python
class Invitations(Base):
    __tablename__ = 'invitations'
    
    id = UUIDField()
    tenant_id = ForeignKey()
    
    invited_email = String()     # Email to invite
    invited_by = ForeignKey('users.id')  # Which user sent invite
    
    status = String()            # 'pending', 'accepted', 'rejected'
    accepted_by = ForeignKey('users.id')  # User who accepted
    accepted_at = DateTime()
    
    expires_at = DateTime()      # Invitation expiration
    created_at = DateTime()
    
    INDEX (tenant_id, invited_email)
```

---

## 📊 Multi-Tenant Isolation Strategy

Every important table includes `tenant_id` field:

```python
# Pattern used throughout
tenant_id = Column(
    String,
    ForeignKey('tenants.id'),
    nullable=False,
    index=True
)
```

**Safety Mechanisms**:

1. **Automatic Filtering** - Repository layer adds `tenant_id` filter to all queries
2. **Index Optimization** - `tenant_id` always indexed for fast lookup
3. **Foreign Keys** - Enforce referential integrity
4. **Validation** - Request middleware checks user's tenant matches query

**Example Query** (safe):
```python
def get_user_documents(user_id: str, tenant_id: str, db: Session):
    # Gets ONLY documents for this tenant
    return db.query(Documents).filter(
        Documents.tenant_id == tenant_id,
        Documents.created_by == user_id
    ).all()
```

---

## 🔑 UUID Primary Keys

All models use UUID (not integer IDs):

```python
from app.models.uuid import uuid_pk

class Users(Base):
    id = uuid_pk()  # Generates UUID automatically
```

**Benefits**:
- ✅ Globally unique (no collisions across distributed systems)
- ✅ Cannot be guessed (security)
- ✅ Hardware-independent
- ✅ Good for microservices

**Format**: Standard UUID4 (36 characters)  
**Example**: `a1b2c3d4-e5f6-47a8-9b10-c11d12e13f14`

---

## ⏰ Timestamps & Auditing

**Pattern**:
```python
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Standards**:
- All times stored in UTC
- Default to `utcnow()` for consistency
- Used for sorting and filtering

---

## 📁 File Structure

```
app/models/
├── README.md         ← You are here
├── __init__.py
├── base.py          # Base declarative class
├── uuid.py          # UUID column helper
├── user.py          # Users table
├── tenant.py        # Tenants table
├── runs.py          # Agent runs (execution history)
├── costLog.py       # Cost tracking for billing
├── documents.py     # Ingested documents
├── invitation.py    # User invitations
└── TRACKER_DB_FILE.py  # File processing status
```

---

## 🔗 Relationships

```
Tenants
  ├─→ Users (1:N)
  ├─→ Documents (1:N)
  ├─→ Runs (1:N)
  ├─→ CostLog (1:N)
  └─→ Chunks (1:N)

Users
  ├─→ Tenants (N:1)
  ├─→ Runs (1:N)
  └─→ Invitations (1:N)

Documents
  ├─→ Tenants (N:1)
  └─→ Chunks (1:N)

Runs
  ├─→ Tenants (N:1)
  ├─→ Users (N:1)
  └─→ CostLog (1:N)
```

---

## 🐛 Troubleshooting

### Migration Fails

**Check**:
```bash
alembic current     # See current revision
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Foreign Key Constraint Error

**Cause**: Trying to insert record with non-existent foreign key

**Solution**: Ensure parent record exists first

### Null Constraint Violation

**Cause**: Writing NULL to non-nullable field

**Solution**: Check field defaults and ensure values provided

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Key Feature**: Multi-tenant isolation with UUID primary keys
