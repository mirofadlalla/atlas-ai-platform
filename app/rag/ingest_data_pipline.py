import os
import sys
from pathlib import Path

# إغلاق تحذيرات ومشاكل الـ Symlinks في ويندوز
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_SYMLINKS"] = "1"

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.rag.steps.ingest import main
from app.rag.steps.loader import DocumentLoader



class RAGPipeline:
    
    @staticmethod
    def process_file(file_path: str, custom_metadata: dict):
        # 1. Load the file and get a list of Document objects
        documents = DocumentLoader.load_file(file_path, custom_metadata)

        # 2. For each document, extract text and metadata, then ingest into Qdrant
        full_text = "\n\n".join([doc.page_content for doc in documents])
        return main(full_text, custom_metadata)
    

retrived = RAGPipeline.process_file("E:\\pyDS\\Enterprise Multi-Tenant Agentic RAG Infrastructure\\app\\rag\\data\\google.pdf", 
                                    custom_metadata={"tenant_id": 123,
                                                      "source": "google.pdf",
                                                        "author": "Omar"
                                                        }
                                    )