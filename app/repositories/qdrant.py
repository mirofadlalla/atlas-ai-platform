import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, SparseVectorParams, PointStruct
from fastembed import SparseTextEmbedding 
from app.design_pattern.embedded_model import EmbeddedModel as embedding

class QdrantRepository:
    def __init__(self, url: str = os.getenv("QDRANT_URL", "http://localhost:6333")):
        # Initialize Qdrant client
        self.client = QdrantClient(url=url)
        
        # Initialize AI models (Dense & Sparse) for hybrid embeddings
        self.dense_model = embedding()  
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    def create_collection(self, collection_name: str, vector_size: int = 1024):
        # Create collection if it does not exist
        if not self.client.collection_exists(collection_name):
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": VectorParams(size=vector_size, distance=Distance.COSINE)
                },  
                sparse_vectors_config={
                    "sparse": SparseVectorParams()
                }
            )
            print(f"[✅] Collection '{collection_name}' created for Hybrid Search.")

    def add_hybrid_documents(self, collection_name: str, documents: list[dict]):
        """
        Add hybrid documents (Dense + Sparse embeddings) to Qdrant.
        
        documents: List of dictionaries
        Example: [{"text": "Machine learning is...", "metadata": {"tenant_id": 123}}]
        """
        points = []
        
        # Extract texts from documents
        texts = [doc["text"] for doc in documents]
        
        print("[⏳] Generating Dense & Sparse embeddings...")
        
        # Generate embeddings (Dense + Sparse)
        dense_vectors = self.dense_model.embed_documents(texts)
        sparse_vectors = list(self.sparse_model.embed(texts)) 
        
        # Build Qdrant points
        for i in range(len(documents)):
            point_id = str(uuid.uuid4())  # Unique ID for each document
            
            # Payload must match retriever configuration
            payload = {
                "content": documents[i]["text"],       # content_payload_key="content"
                "payload": documents[i]["metadata"]    # metadata_payload_key="payload"
            }
            
            # Vectors split into dense + sparse
            vector = {
                "dense": dense_vectors[i],
                "sparse": {
                    "indices": sparse_vectors[i].indices.tolist(), # Convert to list
                    "values": sparse_vectors[i].values.tolist()    # Convert to list
                }
            }
            
            points.append(
                PointStruct(id=point_id, payload=payload, vector=vector)
            )

        # Upsert points into Qdrant
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"[✅] {len(points)} Hybrid documents added to '{collection_name}'.")

    def delete_collection(self, collection_name: str):
        # Delete collection if exists
        if self.client.collection_exists(collection_name):
            self.client.delete_collection(collection_name)
            print(f"[✅] Collection '{collection_name}' deleted from Qdrant.")
        else:
            print(f"[ℹ️] Collection '{collection_name}' does not exist in Qdrant.")

    def list_collections(self):
        # List all collections in Qdrant
        collections = self.client.get_collections()
        return [col.name for col in collections.collections]

    def search(self, collection_name: str, query_vector: list, top_k: int = 5):
        # Perform search in Qdrant collection
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k
        )
        return results