import os
import threading
from typing import List
from langchain_core.embeddings import Embeddings 

# 2. inherit from Embeddings because it is the interface that langchain expects for embedding models
class EmbeddedModel(Embeddings): 
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    print("Initializing embedding model for the first time")
                    cls._instance = super().__new__(cls)
                    cls._instance.model = None  # Placeholder for the actual model instance
                    # cls._instance._load_model()  # Load the model during initialization
        return cls._instance

    def _load_model(self):
        # Lazy import of heavy dependencies - only loaded when model is instantiated
        if self.model is None:
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
        self._load_model()
        embeddings = self.model.encode(texts,normalize_embeddings=True,batch_size=16 )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        self._load_model()
        embedding = self.model.encode(text,normalize_embeddings=True,batch_size=16)
        return embedding.tolist()


# # use for testing
# import os
# import threading
# import logging
# from typing import List
# from langchain_core.embeddings import Embeddings
# from huggingface_hub import InferenceClient

# logger = logging.getLogger(__name__)

# # Global singleton instance
# _embedding_instance = None
# _embedding_lock = threading.Lock()


# def _to_list(vec) -> List[float]:
#     """Convert numpy array or list to list of floats."""
#     if hasattr(vec, "tolist"):
#         return vec.tolist()
#     return list(vec)


# class EmbeddedModel(Embeddings):
#     def __new__(cls):
#         global _embedding_instance
#         if _embedding_instance is None:
#             with _embedding_lock:
#                 if _embedding_instance is None:
#                     logger.info("Initializing embedding model via HF Inference API")
#                     instance = super().__new__(cls)
#                     instance._load_model()
#                     _embedding_instance = instance
#         return _embedding_instance

#     def _load_model(self):
#         from app.core.config import settings
#         timeout = getattr(settings, "embedding_request_timeout", 60.0)
#         self.client = InferenceClient(
#             provider="auto",
#             api_key=os.environ.get("HF_TOKEN_M"),
#             timeout=timeout,
#         )
#         self.model_id = "BAAI/bge-m3"
#         self.batch_size = 32  # Process texts in batches (API accepts list)
#         logger.info(f"EmbeddedModel loaded successfully (batch_size={self.batch_size}, timeout={timeout}s)")

#     def embed_documents(self, texts: List[str]) -> List[List[float]]:
#         """
#         Embed multiple documents. Uses one-by-one API calls with progress logging
#         so ingestion does not appear to hang and to avoid batch API issues.
#         """
#         if not texts:
#             return []
#         total = len(texts)
#         embeddings: List[List[float]] = []
#         logger.info(f"[⏳] Embedding {total} texts via HF API...")

#         for i, text in enumerate(texts):
#             try:
#                 if (i + 1) % 5 == 0 or i == 0 or i == total - 1:
#                     logger.info(f"[⏳] Embedding progress: {i + 1}/{total}")
#                 response = self.client.feature_extraction(text, model=self.model_id)
#                 embeddings.append(_to_list(response))
#             except Exception as e:
#                 logger.error(f"Failed to embed text {i + 1}/{total}: {e}")
#                 embeddings.append([0.0] * 1024)

#         logger.info(f"[✅] Embedding complete: {len(embeddings)} vectors")
#         return embeddings

#     def embed_query(self, text: str) -> List[float]:
#         """Embed a single query text."""
#         try:
#             logger.debug(f"Embedding query: {text[:50]}...")
#             response = self.client.feature_extraction(text, model=self.model_id)
#             logger.debug("✅ Query embedding complete")
#             return _to_list(response)
#         except Exception as e:
#             logger.error(f"Failed to embed query: {e}")
#             return [0.0] * 1024