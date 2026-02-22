import os
import sys
from pathlib import Path

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_SYMLINKS"] = "1"

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_qdrant import QdrantVectorStore, FastEmbedSparse, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client import models # 👈 التعديل هنا: استدعاء موديلز الفلترة من Qdrant
from app.design_pattern.embedded_model import EmbeddedModel

qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333")
)

COLLECTION_NAME = "atlas_documents1"
sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")

def get_retriever(tenant_id: int):
    vectorstore = QdrantVectorStore(
        client=qdrant_client,
        collection_name=COLLECTION_NAME,
        
        embedding=EmbeddedModel(),
        vector_name="dense",
        
        sparse_embedding=sparse_embeddings,
        sparse_vector_name="sparse",
        
        retrieval_mode=RetrievalMode.HYBRID,
        
        content_payload_key="content", 
        metadata_payload_key="payload" 
    )

    return vectorstore.as_retriever(
        search_kwargs={
            "k": 5,
            "filter": models.Filter(
                must=[
                    models.FieldCondition(
                        key="payload.tenant_id", 
                        match=models.MatchValue(value=tenant_id)
                    )
                ]
            )
        }
    )

# if __name__ == "__main__":
#     retriever = get_retriever(123)
#     relevant_docs = retriever.invoke("What is machine learning?") 
    
#     print("\n--- Retrieved Documents ---")
#     for i, doc in enumerate(relevant_docs):
#         print(f"Doc {i+1}: {doc.page_content}")
#         print(f"Metadata: {doc.metadata}\n")

