import os
import sys
from pathlib import Path

# إغلاق تحذيرات ومشاكل الـ Symlinks في ويندوز
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_SYMLINKS"] = "1"

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.repositories.qdrant import QdrantRepository
from app.rag.steps.semantic_chunking_function import SemanticChunkingFunction

COLLECTION_NAME = "atlas_documents1"

def main(text : str , my_metadata : dict):
    repo = QdrantRepository()
    repo.create_collection(COLLECTION_NAME) 

    print("[⏳] Chunking text...")
    chunks_with_metadata = SemanticChunkingFunction.process_document(text, my_metadata)

    data_to_insert = []
    for doc in chunks_with_metadata:
        
        # Generate a stable chunk ID based on the content and metadata
        chunk_id = SemanticChunkingFunction.generate_chunk_id(
            text=doc.page_content,
            tenant_id=my_metadata["tenant_id"],
            source=my_metadata["source"]
        )
        
        data_to_insert.append({
            "id": chunk_id,
            "text": doc.page_content,
            "metadata": doc.metadata
        })
        
    repo.add_hybrid_documents(COLLECTION_NAME, data_to_insert)

# if __name__ == "__main__":
#     # Simple Test
#     text = """
#     Machine learning is a subset of artificial intelligence.
#     It allows systems to learn from data.
#     Deep learning is a specialized type of machine learning.
#     Pizza is one of the most popular foods in the world.
#     Neural networks are inspired by the human brain.
#     """

#     my_metadata = {
#         "tenant_id": 123,
#         "source": "machine_learning_intro.txt",
#         "author": "Omar"
#     }
#     main(text,my_metadata)




# # 4. طباعة النتيجة عشان تتأكد
# print(chunks_with_metadata)