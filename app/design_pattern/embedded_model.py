import os
import threading
import logging
from typing import List
from langchain_core.embeddings import Embeddings
import requests

logger = logging.getLogger(__name__)


def _to_list(vec) -> List[float]:
    if hasattr(vec, "tolist"):
        return vec.tolist()
    return list(vec)


class EmbeddedModel(Embeddings):
    """
    Singleton embedding model that uses a remote `/embed` endpoint when
    `REMOTE_EMBED_URL` is set, otherwise falls back to a local
    `sentence_transformers` model.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def _ensure_initialized(self):
        if self._initialized:
            return
        self.remote_url = "https://marilyn-unilluminative-florinda.ngrok-free.dev"
        self.batch_size = int(os.environ.get("EMBED_BATCH_SIZE", "32"))
        self.timeout = float(os.environ.get("EMBED_TIMEOUT", "30"))
        self.model = None
        self._initialized = True

    def _load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            import torch

            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.model = SentenceTransformer("BAAI/bge-m3", device=device)
                logger.info("Loaded local embedding model on %s", device)
            except Exception:
                logger.exception("Failed loading BGE-M3, falling back to all-MiniLM-L6-v2")
                self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    def _call_remote_embed(self, texts: List[str]) -> List[List[float]]:
        url = self.remote_url.rstrip("/") + "/embed"
        resp = requests.post(url, json={"texts": texts}, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("embeddings", [])

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self._ensure_initialized()
        if not texts:
            return []

        if self.remote_url:
            try:
                embeddings: List[List[float]] = []
                for i in range(0, len(texts), self.batch_size):
                    batch = texts[i : i + self.batch_size]
                    batch_emb = self._call_remote_embed(batch)
                    embeddings.extend(batch_emb)
                return embeddings
            except Exception:
                logger.exception("Remote embedding failed, falling back to local model")
                self.remote_url = None

        # local fallback
        self._load_model()
        emb = self.model.encode(texts, normalize_embeddings=True, batch_size=self.batch_size)
        return _to_list(emb)

    def embed_query(self, text: str) -> List[float]:
        self._ensure_initialized()
        if self.remote_url:
            try:
                emb = self._call_remote_embed([text])
                if emb:
                    return emb[0]
            except Exception:
                logger.exception("Remote query embedding failed, falling back to local model")
                self.remote_url = None

        self._load_model()
        embedding = self.model.encode(text, normalize_embeddings=True)
        return _to_list(embedding)
