import os
import sys
from pathlib import Path

# إغلاق تحذيرات ومشاكل الـ Symlinks في ويندوز
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_SYMLINKS"] = "1"

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.rag.steps.ingest import main
from app.rag.steps.loader import DocumentLoader

from app.rag.steps.file_tracker import FileTracker 

from sqlalchemy.orm import Session

class RAGPipeline:
    
    @staticmethod
    def process_file(file_path: str, custom_metadata: dict, db: Session):
        # Extract tenant_id and file_name for tracking purposes
        tenant_id = str(custom_metadata["tenant_id"])
        file_name = Path(file_path).name
        
        # 1. calculate file hash to detect changes and avoid reprocessing unchanged files (especially important for large files) - لو الملف اتعدل أو جديد، هنكمل البايبلاين، لو لأ، هنرجع رسالة إنه مفيش حاجة اتغيرت ومش هنكمل البايبلاين عشان نوفر وقت وموارد
        print(f"Checking file hash for: {file_name}")
        file_hash = FileTracker.calculate_file_hash(file_path)
        
        # 2. Check if the file has been processed before with the same hash (indicating no changes) - لو الملف اتعدل أو جديد، هنكمل البايبلاين، لو لأ، هنرجع رسالة إنه مفيش حاجة اتغيرت ومش هنكمل البايبلاين عشان نوفر وقت وموارد
        if FileTracker.is_file_processed(tenant_id, file_hash, db):
            msg = f"Skip: File '{file_name}' for tenant {tenant_id} is already processed. No changes detected."
            print(msg)
            return {"status": "skipped", "message": msg}

        # ==========================================
        # if we reached here, it means the file is new or has changed, so we proceed with the RAG pipeline
        # ==========================================
        print(f"New content detected. Starting RAG pipeline for: {file_name}")
        
        # 3. Mark file as processing (idempotent - supports retries without re-doing chunking)
        FileTracker.mark_processing(tenant_id, file_name, file_hash, db)
        
        try:
            # 4. Load the file and get a list of Document objects
            documents = DocumentLoader.load_file(file_path, custom_metadata)

            # 5. Extract text and ingest into Qdrant
            full_text = "\n\n".join([doc.page_content for doc in documents])
            result = main(full_text, custom_metadata)
            
            # 6. Mark the file as completed
            FileTracker.mark_completed(tenant_id, file_hash, db)
            
            return {"status": "success", "message": "File processed and ingested.", "details": result}
        
        except Exception as e:
            # Mark file as failed (allows retry without re-doing chunking)
            FileTracker.mark_failed(tenant_id, file_hash, db)
            error_msg = f"Error processing file: {str(e)}"
            print(f"[❌] {error_msg}")
            return {"status": "failed", "message": error_msg, "error": str(e)}
    


# antml:function_calls>
