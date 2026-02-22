import os
import threading
from typing import List
from langchain_core.embeddings import Embeddings # 1. الاستدعاء المهم جداً

# 2. خلينا الكلاس يورث من Embeddings
class EmbeddedModel(Embeddings): 
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    print("Initializing embedding model for the first time")
                    cls._instance = super().__new__(cls)
                    cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        # Lazy import of heavy dependencies - only loaded when model is instantiated
        from sentence_transformers import SentenceTransformer
        import torch
        
        try:
            self.model = SentenceTransformer(
                "BAAI/bge-m3",
                device="cuda" if torch.cuda.is_available() else "cpu",
            )
        except Exception: # Fallback to a smaller model if the main one fails to load (especially on CPU-only environments) but this wll cause a significant drop in embedding quality from 1024 to 384 dimensions but the qdrant requre 1024
            print("Falling back to all-MiniLM-L6-v2 on CPU")
            self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts,normalize_embeddings=True,batch_size=16 )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(text,normalize_embeddings=True,batch_size=16)
        return embedding.tolist()