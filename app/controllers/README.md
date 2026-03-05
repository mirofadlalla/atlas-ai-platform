# Atlas AI Controllers - Request Preprocessing

**Module**: `app/controllers`  
**Purpose**: Request validation and preprocessing before service execution  
**Last Updated**: March 2026

---

## 📋 Overview

Controllers act as a **thin adapter layer** between routes and services:

✅ **Request Normalization** - Transform raw input to domain objects  
✅ **Input Validation** - Schema enforcement (Pydantic)  
✅ **Error Translation** - Convert exceptions to HTTP responses  
✅ **Dependency Injection** - Inject database and configuration  

```
FastAPI Route
    ↓
Controller (validate, normalize)
    ↓
Service (business logic)
    ↓
Repository (data access)
```

---

## 🎯 Controller Pattern

### Standard Implementation

```python
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

class MyRequest(BaseModel):
    # Request schema - validated by Pydantic
    email: EmailStr
    name: str
    
class MyController:
    @staticmethod
    def handle_request(request: MyRequest, db: Session) -> dict:
        """Static method pattern for dependency injection"""
        
        # 1. Normalize input
        email = request.email.lower().strip()
        
        # 2. Call service
        from app.services.my_service import MyService
        service = MyService(db)
        result = service.execute(email=email, name=request.name)
        
        # 3. Return domain object
        return result.to_dict()
```

### Route Integration

```python
from fastapi import APIRouter, Depends
from app.controllers.my_controller import MyController
from app.core.db import get_db

router = APIRouter()

@router.post("/endpoint")
async def endpoint(
    request: MyRequest,
    db: Session = Depends(get_db)
):
    """Route delegates to controller"""
    return MyController.handle_request(request, db)
```

---

## 📁 Controllers

### 1. AuthController (`auth_controller.py`)

**Purpose**: Handle authentication workflows

```python
from app.schema.auth_admin import UserCreate, UserLogin

class AuthController:
    
    @staticmethod
    def register(user_data: UserCreate, db: Session) -> dict:
        """
        Register new user.
        
        Request:
        {
            "email": "john@example.com",
            "password": "secure123",
            "company_name": "Acme Corp"
        }
        
        Flow:
        1. Validate email not already registered
        2. Hash password with bcrypt
        3. Create tenant & user records
        4. Return JWT token
        """
        service = AuthService(db)
        return service.register_user(user_data)
    
    @staticmethod
    def login(user_data: UserLogin, db: Session) -> dict:
        """
        Authenticate user with email/password.
        
        Request:
        {
            "email": "john@example.com",
            "password": "secure123"
        }
        
        Flow:
        1. Find user by email
        2. Verify password hash
        3. Generate JWT token (8-hour expiration)
        4. Return token + user profile
        """
        service = AuthService(db)
        return service.login_user(user_data.email, user_data.password)
    
    @staticmethod
    def refresh_token(invalid_token: str, db: Session) -> dict:
        """Generate new JWT token if current expired"""
        service = AuthService(db)
        return service.generate_new_token(invalid_token)
```

### 2. IngestRagController (`ingest_rag_controller.py`)

**Purpose**: Handle document ingestion workflows

```python
from typing import Optional
from fastapi import UploadFile

class IngestRagController:
    
    @staticmethod
    def upload_documents(
        files: list[UploadFile],
        user_id: str,
        tenant_id: str,
        metadata: Optional[dict] = None,
        db: Session = None
    ) -> dict:
        """
        Queue document ingestion.
        
        Flow:
        1. Validate file types (PDF, DOCX, TXT)
        2. Validate file sizes (< 100MB)
        3. Save to temporary storage
        4. Queue Celery task for ingestion
        5. Return task IDs for polling
        
        Returns:
        {
            "file_ids": ["task-1", "task-2"],
            "status": "queued",
            "message": "2 files queued for processing"
        }
        """
        service = IngestRagService(db)
        
        # Normalization
        validated_files = [
            {
                "filename": file.filename,
                "size_bytes": len(await file.read()),
                "content_type": file.content_type
            }
            for file in files
        ]
        
        # Validation
        for f in validated_files:
            if f["size_bytes"] > 100 * 1024 * 1024:  # 100MB
                raise ValueError(f"File {f['filename']} too large")
            if not f["content_type"] in [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ]:
                raise ValueError(f"File type {f['content_type']} not supported")
        
        # Service call
        return service.queue_ingestion(
            files=files,
            user_id=user_id,
            tenant_id=tenant_id,
            metadata=metadata
        )
    
    @staticmethod
    def get_ingestion_status(file_id: str, tenant_id: str, db: Session) -> dict:
        """
        Poll ingestion status.
        
        Returns:
        {
            "file_id": "task-1",
            "status": "completed" | "processing" | "failed",
            "progress": 75,
            "chunks_created": 42
        }
        """
        service = IngestRagService(db)
        return service.get_status(file_id, tenant_id)
```

---

## 🔄 Request Flow Example

### Scenario: User Registration

```
POST /api/auth/register
{
  "email": "john@acme.com",
  "password": "secure123",
  "company_name": "Acme Corp"
}
    ↓
(FastAPI Pydantic validation)
    ↓
auth_route.register() [route handler]
    ↓
AuthController.register(request: UserCreate, db: Session) [controller]
    ├─ Normalize: email = email.lower().strip()
    ├─ Validate: email not already registered
    └─→ AuthService.register_user(user_data) [service]
        ├─ Create Tenant record
        ├─ Create User record
        ├─ Hash password (bcrypt)
        └─ Generate JWT token
    ↓
Return 201 Created
{
  "tenant_id": "uuid-123",
  "user_id": "uuid-456",
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## ✅ Validation Patterns

### Pydantic Schema Validation

Controllers receive **automatically validated** Pydantic models:

```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr                    # Valid email format enforced
    password: str = Field(min_length=8) # Min 8 chars
    company_name: str = Field(max_length=256)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@acme.com",
                "password": "secure123",
                "company_name": "Acme Corp"
            }
        }
```

**FastAPI automatically rejects invalid input:**

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email", "password": "short"}'

Response 422 Unprocessable Entity:
{
  "detail": [
    {
      "field": "email",
      "message": "Invalid email format"
    },
    {
      "field": "password",
      "message": "Ensure this value has at least 8 characters"
    }
  ]
}
```

### Business Logic Validation

```python
class AuthController:
    @staticmethod
    def register(user_data: UserCreate, db: Session) -> dict:
        # Check duplicate
        existing = db.query(User).filter(
            User.email == user_data.email
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )
        
        # Proceed...
        service = AuthService(db)
        return service.register_user(user_data)
```

---

## 🚨 Error Handling

### Controller Exception Translation

```python
from fastapi import HTTPException

class IngestRagController:
    @staticmethod
    def upload_documents(files: list, db: Session) -> dict:
        try:
            service = IngestRagService(db)
            return service.queue_ingestion(files)
        
        except ValueError as e:  # Business logic error
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        
        except FileNotFoundError as e:  # Storage error
            raise HTTPException(
                status_code=500,
                detail="File storage unavailable"
            )
        
        except Exception as e:  # Unexpected
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
```

---

## 🧠 Best Practices

### DO ✅

- **Inject dependencies** - Pass `db: Session` as parameter
- **Use Pydantic models** - Let FastAPI validate input
- **Use static methods** - Easier to test, no state
- **Return dict/model** - Let route serialize to JSON
- **Keep it thin** - Delegate logic to service layer
- **Document flows** - Add docstrings with Request/Response examples

### DON'T ❌

- **Duplicate validation** - Pydantic handles it
- **Call routes from controllers** - Circular dependency
- **Mix concerns** - Don't write business logic here
- **Access repositories directly** - Go through service layer
- **Return raw ORM objects** - Convert to dict/Pydantic first

---

## 📊 Layered Architecture

```
Layer 1: Routes (FastAPI)
├─ Path: /api/auth/register
├─ Method: POST
└─ Input: HTTP JSON
    ↓
Layer 2: Controllers (Request Preprocessing)
├─ Validate Pydantic schema
├─ Normalize input
└─ Catch exceptions
    ↓
Layer 3: Services (Business Logic)
├─ Complex domain operations
├─ Orchestrate repositories
└─ Apply business rules
    ↓
Layer 4: Repositories (Data Access)
├─ Query builders
├─ Transaction management
└─ Tenant filtering
    ↓
Layer 5: Database (PostgreSQL)
└─ Persist data
```

---

## 📁 File Structure

```
app/controllers/
├── README.md                    ← You are here
├── auth_controller.py           # Authentication controller
├── ingest_rag_controller.py     # Document ingestion controller
└── __pycache__/
```

---

## 🔗 Related Modules

- [Routes](../routes/README.md) - HTTP endpoint handlers
- [Services](../services/README.md) - Business logic orchestration
- [Repositories](../repositories/README.md) - Data access patterns
- [Models](../models/README.md) - ORM schemas

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Pattern**: Static method design with dependency injection