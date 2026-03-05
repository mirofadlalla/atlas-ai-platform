# Atlas AI Design Patterns

**Module**: `app/design_pattern`  
**Purpose**: Reusable design patterns for common software engineering problems  
**Last Updated**: March 2026

---

## 📋 Overview

This module implements three core design patterns to solve recurring problems:

✅ **Singleton Pattern** - Ensure only one instance of expensive objects (embedding models)  
✅ **Factory Pattern** - Create objects without specifying exact classes  
✅ **Strategy Pattern** - Encapsulate file processing logic variations  

---

## 🎯 Pattern 1: Singleton - EmbeddedModel

**Problem**: Embedding model is expensive to load (~500MB). Should be loaded once and reused globally.

### Implementation (`embedded_model.py`)

```python
import threading
from typing import List
from langchain_core.embeddings import Embeddings

class EmbeddedModel(Embeddings):
    """Thread-safe singleton embedding model"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Ensure only one instance exists across all code"""
        if cls._instance is None:
            with cls._lock:  # Thread-safe double-check
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def _ensure_initialized(self):
        """Lazy initialization - model loads on first access"""
        if self._initialized:
            return
        
        # Configuration from environment
        self.remote_url = os.environ.get("REMOTE_EMBED_URL")
        self.batch_size = int(os.environ.get("EMBED_BATCH_SIZE", "32"))
        self.timeout = float(os.environ.get("EMBED_TIMEOUT", "30"))
        
        self.model = None  # Will load in _load_model()
        self._initialized = True
    
    def _load_model(self):
        """Load from remote API or local sentence_transformers"""
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = SentenceTransformer(
                "all-MiniLM-L6-v2",
                device=device
            )
    
    def embed_query(self, text: str) -> List[float]:
        """Embed single query"""
        self._ensure_initialized()
        
        if self.remote_url:
            # Use remote API
            response = requests.post(
                f"{self.remote_url}/embed",
                json={"text": text},
                timeout=self.timeout
            )
            return response.json()["embedding"]
        else:
            # Use local model
            self._load_model()
            embedding = self.model.encode(text)
            return embedding.tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed batch of documents"""
        self._ensure_initialized()
        
        if self.remote_url:
            # Use remote API with batching
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i+self.batch_size]
                response = requests.post(
                    f"{self.remote_url}/embed",
                    json={"texts": batch},
                    timeout=self.timeout
                )
                all_embeddings.extend(response.json()["embeddings"])
            return all_embeddings
        else:
            # Use local model
            self._load_model()
            embeddings = self.model.encode(texts, batch_size=self.batch_size)
            return [e.tolist() for e in embeddings]
```

### Usage

```python
# Anywhere in code
from app.design_pattern.embedded_model import EmbeddedModel

# First call: loads model (slow, ~2 seconds)
embedder = EmbeddedModel()
embedding1 = embedder.embed_query("hello")  # First call: loads model

# Second call: returns same instance (instant)
embedder2 = EmbeddedModel()
embedding2 = embedder2.embed_query("world")  # Same instance, instant

# Same object
assert embedder is embedder2  # True
```

### Benefits

✅ **Memory Efficient** - Model loaded once, not per request  
✅ **Thread-Safe** - Double-lock pattern prevents race conditions  
✅ **Lazy Loading** - Model loads on first access, not at startup  
✅ **Hybrid Support** - Can switch between local/remote embed APIs  

---

## 🎯 Pattern 2: Factory - UserFactory + UploadFactory

**Problem**: Different user types or upload methods should be created differently.

### UserFactory (Template)

```python
# File: app/design_pattern/user_factory.py (currently disabled)

from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class AdminUser:
    """Admin with full permissions"""
    def __init__(self, user_id: str, email: str, tenant_id: str):
        self.id = user_id
        self.email = email
        self.tenant_id = tenant_id
        self.role = UserRole.ADMIN
        self.permissions = ["read", "write", "delete", "admin"]

class RegularUser:
    """Regular user with limited permissions"""
    def __init__(self, user_id: str, email: str, tenant_id: str):
        self.id = user_id
        self.email = email
        self.tenant_id = tenant_id
        self.role = UserRole.USER
        self.permissions = ["read", "write"]

class ViewerUser:
    """Read-only viewer"""
    def __init__(self, user_id: str, email: str, tenant_id: str):
        self.id = user_id
        self.email = email
        self.tenant_id = tenant_id
        self.role = UserRole.VIEWER
        self.permissions = ["read"]

class UserFactory:
    """Create appropriate user instance based on role"""
    
    @staticmethod
    def create_user(role: UserRole, user_id: str, email: str, tenant_id: str):
        """Factory method - hides creation logic from caller"""
        
        if role == UserRole.ADMIN:
            return AdminUser(user_id, email, tenant_id)
        
        elif role == UserRole.USER:
            return RegularUser(user_id, email, tenant_id)
        
        elif role == UserRole.VIEWER:
            return ViewerUser(user_id, email, tenant_id)
        
        else:
            raise ValueError(f"Unknown role: {role}")

# Usage
user = UserFactory.create_user(
    role=UserRole.ADMIN,
    user_id="uuid-123",
    email="john@example.com",
    tenant_id="tenant-456"
)
assert user.role == UserRole.ADMIN
assert "admin" in user.permissions
```

### UploadFactory (Active Implementation)

**Purpose**: Handle different upload sources (single file, directory, etc.)

```python
# File: app/design_pattern/upload_factory.py

from pathlib import Path
from app.controllers.ingest_rag_controller import IngestRagController
from sqlalchemy.orm import Session

def process_upload(
    file_path: str,
    tenant_id: str,
    source: str,
    author: str,
    db: Session
) -> dict:
    """
    Factory function that routes to appropriate processor.
    Handles both single files and directories.
    """
    path = Path(file_path)
    
    if not path.exists():
        return {"error": f"Path does not exist: {file_path}"}
    
    results = []
    
    if path.is_file():
        # Single file: use FileProcessor
        print(f"📄 Processing single file: {path.name}")
        result = IngestRagController.ingest_file(
            file_path=str(path),
            tenant_id=tenant_id,
            source=source,
            author=author,
            db=db
        )
        results.append({
            "file": path.name,
            "task_id": result.get("task_id"),
            "status": result.get("status")
        })
    
    elif path.is_dir():
        # Directory: use FolderProcessor (recursively process all files)
        print(f"📁 Processing directory: {path.name}")
        for file in path.iterdir():
            if file.is_file():
                print(f"  - {file.name}")
                result = IngestRagController.ingest_file(
                    file_path=str(file),
                    tenant_id=tenant_id,
                    source=source,
                    author=author,
                    db=db
                )
                results.append({
                    "file": file.name,
                    "task_id": result.get("task_id"),
                    "status": result.get("status")
                })
    
    return {
        "message": f"Processed {len(results)} files",
        "results": results,
        "total_files": len(results)
    }

# Usage
result = process_upload(
    file_path="/path/to/documents",
    tenant_id="tenant-123",
    source="User Upload",
    author="john@example.com",
    db=db_session
)
# Returns:
# {
#   "message": "Processed 5 files",
#   "results": [
#     {"file": "doc1.pdf", "task_id": "...", "status": "queued"},
#     {"file": "doc2.pdf", "task_id": "...", "status": "queued"}
#   ],
#   "total_files": 5
# }
```

---

## 🎯 Pattern 3: Strategy - File Processing

**Problem**: Different file types need different processing strategies (PDF vs DOCX vs TXT).

### Strategy Pattern Implementation

```python
# File: app/design_pattern/upload_factory_pattern/Interface.py

from abc import ABC, abstractmethod

class FileProcessor(ABC):
    """Abstract interface for file processors"""
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """Check if processor handles this file type"""
        pass
    
    @abstractmethod
    def process(self, file_path: str) -> str:
        """Process file and return extracted text"""
        pass
```

### Concrete Strategies

```python
# File: app/design_pattern/upload_factory_pattern/file_processor.py

from typing import Optional
from pathlib import Path
import PyPDF2
import docx

class PDFProcessor(FileProcessor):
    """Strategy for PDF files"""
    
    def can_process(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".pdf"
    
    def process(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text())
        return "\n".join(text)

class DocxProcessor(FileProcessor):
    """Strategy for DOCX files"""
    
    def can_process(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".docx"
    
    def process(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

class TextProcessor(FileProcessor):
    """Strategy for TXT files"""
    
    def can_process(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".txt"
    
    def process(self, file_path: str) -> str:
        """Read plain text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
```

### Folder Processor

```python
# File: app/design_pattern/upload_factory_pattern/folder_processor.py

from pathlib import Path
from .processor_factory import ProcessorFactory

class FolderProcessor:
    """Process all files in folder using appropriate strategy"""
    
    def __init__(self):
        self.factory = ProcessorFactory()
    
    def process_folder(self, folder_path: str) -> dict:
        """Recursively process all files in folder"""
        
        results = {
            "total_files": 0,
            "processed": 0,
            "failed": 0,
            "files": []
        }
        
        for file_path in Path(folder_path).rglob("*"):
            if file_path.is_file():
                results["total_files"] += 1
                
                try:
                    # Strategy selection via factory
                    processor = self.factory.get_processor(str(file_path))
                    
                    if processor is None:
                        results["files"].append({
                            "file": file_path.name,
                            "status": "skipped",
                            "reason": "No processor for this type"
                        })
                        continue
                    
                    # Execute strategy
                    text = processor.process(str(file_path))
                    
                    results["processed"] += 1
                    results["files"].append({
                        "file": file_path.name,
                        "status": "processed",
                        "text_length": len(text),
                        "preview": text[:100] + "..."
                    })
                
                except Exception as e:
                    results["failed"] += 1
                    results["files"].append({
                        "file": file_path.name,
                        "status": "failed",
                        "error": str(e)
                    })
        
        return results
```

### Processor Factory

```python
# File: app/design_pattern/upload_factory_pattern/processor_factory.py

from typing import Optional
from .file_processor import PDFProcessor, DocxProcessor, TextProcessor
from .Interface import FileProcessor

class ProcessorFactory:
    """Select appropriate strategy for each file"""
    
    def __init__(self):
        self.strategies = [
            PDFProcessor(),
            DocxProcessor(),
            TextProcessor()
        ]
    
    def get_processor(self, file_path: str) -> Optional[FileProcessor]:
        """Factory method - returns appropriate strategy or None"""
        
        for strategy in self.strategies:
            if strategy.can_process(file_path):
                return strategy
        
        return None

# Usage
factory = ProcessorFactory()

# Automatically selects PDFProcessor for .pdf files
pdf_processor = factory.get_processor("document.pdf")
text = pdf_processor.process("document.pdf")

# Automatically selects DocxProcessor for .docx files
docx_processor = factory.get_processor("report.docx")
text = docx_processor.process("report.docx")
```

---

## 📊 Pattern Comparison

| Pattern | Problem | Solution | Use Case |
|---------|---------|----------|----------|
| **Singleton** | Expensive object created repeatedly | Only 1 instance globally | Embedding model, DB connection pool, LLM client |
| **Factory** | Client code tightly coupled to concrete classes | Create via factory method | User roles, different upload types |
| **Strategy** | Multiple algorithms for same problem | Encapsulate algorithms as classes | Different file processors, different chunking strategies |

---

## 🏆 Benefits & Trade-offs

### Singleton ✅
**Benefits**: Memory efficient, thread-safe, global access  
**Trade-offs**: Global state (harder to test), must ensure thread-safety

### Factory ✅
**Benefits**: Decouples creation logic, easy to add new types, single source of truth  
**Trade-offs**: Extra indirection, more classes

### Strategy ✅
**Benefits**: Easy to swap algorithms, follows Open/Closed principle, flexible  
**Trade-offs**: Can lead to many small classes, overkill for 2 options

---

## 📁 File Structure

```
app/design_pattern/
├── README.md                          ← You are here
├── embedded_model.py                  # Singleton pattern (LLM embeddings)
├── llm_singlton.py                    # Singleton template (disabled)
├── user_factory.py                    # Factory pattern template (disabled)
├── upload_factory.py                  # Upload router (factory function)
└── upload_factory_pattern/            # Strategy pattern for file processing
    ├── Interface.py                   # Abstract FileProcessor interface
    ├── file_processor.py              # Concrete strategies (PDF, DOCX, TXT)
    ├── folder_processor.py            # Directory processor
    ├── processor_factory.py           # Strategy selection factory
    └── __pycache__/
```

---

## 🔗 Related Patterns

- **Decorator Pattern**: Could wrap processors with logging/metrics
- **Observer Pattern**: Notify listeners when processing completes
- **Template Method**: Common processing steps in base class
- **Adapter Pattern**: Convert different APIs to common interface

---

## 🧠 Design Principles Applied

✅ **Single Responsibility** - Each class does one thing  
✅ **Open/Closed** - Easy to add new processors without modifying factory  
✅ **Liskov Substitution** - Any processor can replace another  
✅ **Dependency Inversion** - Depend on abstractions (Interface), not concrete classes  
✅ **Don't Repeat Yourself** - Common logic in factory/interface  

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Patterns**: Singleton, Factory, Strategy  
**Industries**: ML/AI, Document Processing, Multi-tenant SaaS