"""
Reranker service for improved document ranking in RAG systems.

Reranking improves upon initial retrieval by using cross-encoder models
to score document relevance based on query-document pair similarity.
"""
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class Document:
    """Document representation for reranking."""
    def __init__(self, content: str, metadata: Dict = None, score: float = 0.0):
        self.content = content
        self.metadata = metadata or {}
        self.score = score
        self.rerank_score = 0.0


class Reranker:
    """
    Base reranker class for document re-ranking strategies.
    """
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 10
    ) -> List[Document]:
        """
        Rerank documents based on query relevance.
        
        Args:
            query: User query
            documents: List of documents to rerank
            top_k: Number of top documents to return
            
        Returns:
            Reranked documents sorted by relevance
        """
        raise NotImplementedError


class CrossEncoderReranker(Reranker):
    """
    Cross-encoder based reranker using HuggingFace models.
    
    Cross-encoders directly score query-document pairs, providing
    more accurate relevance judgments than bi-encoders alone.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"):
        """
        Initialize cross-encoder reranker.
        
        Args:
            model_name: HuggingFace model identifier for cross-encoder
        """
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
            self.model_name = model_name
            logger.info(f"Loaded cross-encoder model: {model_name}")
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.model = None
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 10
    ) -> List[Document]:
        """
        Rerank documents using cross-encoder scoring.
        
        Args:
            query: User query
            documents: List of documents to rerank
            top_k: Number of top documents to return
            
        Returns:
            Top-k reranked documents
        """
        if not self.model or not documents:
            return documents[:top_k]
        
        try:
            # Extract texts from documents
            texts = [doc.content for doc in documents]
            
            # Create query-document pairs
            query_doc_pairs = [[query, text] for text in texts]
            
            # Score pairs with cross-encoder
            scores = self.model.predict(query_doc_pairs)
            
            # Assign rerank scores to documents
            for doc, score in zip(documents, scores):
                doc.rerank_score = float(score)
            
            # Sort by rerank score (descending)
            reranked = sorted(documents, key=lambda x: x.rerank_score, reverse=True)
            
            logger.debug(
                f"Reranked {len(documents)} documents for query: {query[:50]}... "
                f"Top score: {reranked[0].rerank_score:.4f}"
            )
            
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Error in cross-encoder reranking: {e}")
            # Fallback: return original documents
            return documents[:top_k]


class BM25Reranker(Reranker):
    """
    BM25-based reranker for lexical relevance scoring.
    
    BM25 is a proven ranking function that considers term frequency
    and document length normalization.
    """
    
    def __init__(self):
        """Initialize BM25 reranker."""
        try:
            from rank_bm25 import BM25Okapi
            self.BM25Okapi = BM25Okapi
            logger.info("BM25 reranker initialized")
        except ImportError:
            logger.error("rank-bm25 not installed. Install with: pip install rank-bm25")
            self.BM25Okapi = None
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 10
    ) -> List[Document]:
        """
        Rerank documents using BM25 scoring.
        
        Args:
            query: User query
            documents: List of documents to rerank
            top_k: Number of top documents to return
            
        Returns:
            Top-k reranked documents
        """
        if not self.BM25Okapi or not documents:
            return documents[:top_k]
        
        try:
            # Tokenize documents
            tokenized_docs = [doc.content.lower().split() for doc in documents]
            
            # Initialize BM25
            bm25 = self.BM25Okapi(tokenized_docs)
            
            # Tokenize query
            query_tokens = query.lower().split()
            
            # Score documents
            scores = bm25.get_scores(query_tokens)
            
            # Assign BM25 scores
            for doc, score in zip(documents, scores):
                doc.rerank_score = float(score)
            
            # Sort by BM25 score (descending)
            reranked = sorted(documents, key=lambda x: x.rerank_score, reverse=True)
            
            logger.debug(f"BM25 reranked {len(documents)} documents")
            
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Error in BM25 reranking: {e}")
            return documents[:top_k]


class HybridReranker(Reranker):
    """
    Hybrid reranker combining multiple scoring strategies.
    
    Uses cross-encoder scores (semantic relevance) and BM25 scores (lexical matching)
    with configurable weighting for balanced ranking.
    """
    
    def __init__(
        self,
        cross_encoder_weight: float = 0.7,
        bm25_weight: float = 0.3,
        cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"
    ):
        """
        Initialize hybrid reranker.
        
        Args:
            cross_encoder_weight: Weight for cross-encoder scores (0.0-1.0)
            bm25_weight: Weight for BM25 scores (0.0-1.0)
            cross_encoder_model: HuggingFace model for cross-encoder
        """
        self.cross_encoder_weight = cross_encoder_weight
        self.bm25_weight = bm25_weight
        
        # Initialize rerankers
        self.cross_encoder = CrossEncoderReranker(cross_encoder_model)
        self.bm25 = BM25Reranker()
        
        logger.info(
            f"Hybrid reranker initialized - "
            f"CE weight: {cross_encoder_weight}, BM25 weight: {bm25_weight}"
        )
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 10
    ) -> List[Document]:
        """
        Rerank documents using hybrid scoring strategy.
        
        Args:
            query: User query
            documents: List of documents to rerank
            top_k: Number of top documents to return
            
        Returns:
            Top-k reranked documents
        """
        if not documents:
            return documents
        
        try:
            # Create document copies for each reranker
            docs_for_ce = [Document(d.content, d.metadata, d.score) for d in documents]
            docs_for_bm25 = [Document(d.content, d.metadata, d.score) for d in documents]
            
            # Get scores from both rerankers
            ce_ranked = self.cross_encoder.rerank(query, docs_for_ce, top_k=len(documents))
            bm25_ranked = self.bm25.rerank(query, docs_for_bm25, top_k=len(documents))
            
            # Normalize scores for both rerankers
            ce_scores = np.array([d.rerank_score for d in ce_ranked])
            bm25_scores = np.array([d.rerank_score for d in bm25_ranked])
            
            ce_scores_norm = (ce_scores - ce_scores.min()) / (ce_scores.max() - ce_scores.min() + 1e-10)
            bm25_scores_norm = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min() + 1e-10)
            
            # Create mapping of document content to indices
            doc_content_to_ce_score = {d.content: score for d, score in zip(ce_ranked, ce_scores_norm)}
            doc_content_to_bm25_score = {d.content: score for d, score in zip(bm25_ranked, bm25_scores_norm)}
            
            # Calculate hybrid scores
            for doc in documents:
                ce_score = doc_content_to_ce_score.get(doc.content, 0.0)
                bm25_score = doc_content_to_bm25_score.get(doc.content, 0.0)
                
                hybrid_score = (
                    self.cross_encoder_weight * ce_score +
                    self.bm25_weight * bm25_score
                )
                doc.rerank_score = hybrid_score
            
            # Sort by hybrid score
            reranked = sorted(documents, key=lambda x: x.rerank_score, reverse=True)
            
            logger.debug(f"Hybrid reranked {len(documents)} documents")
            
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Error in hybrid reranking: {e}")
            return documents[:top_k]


class RankingService:
    """
    Service for managing document reranking in RAG pipelines.
    
    Provides a unified interface for different reranking strategies.
    """
    
    def __init__(self, strategy: str = "hybrid"):
        """
        Initialize ranking service with specified strategy.
        
        Args:
            strategy: Reranking strategy ('cross-encoder', 'bm25', 'hybrid')
        """
        self.strategy = strategy
        
        if strategy == "cross-encoder":
            self.reranker = CrossEncoderReranker()
        elif strategy == "bm25":
            self.reranker = BM25Reranker()
        elif strategy == "hybrid":
            self.reranker = HybridReranker()
        else:
            logger.warning(f"Unknown strategy: {strategy}, defaulting to hybrid")
            self.reranker = HybridReranker()
    
    def rank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        """
        Rerank documents using the configured strategy.
        
        Args:
            query: User query
            documents: List of document dictionaries with 'content' and 'metadata'
            top_k: Number of top documents to return
            
        Returns:
            Reranked documents with updated scores
        """
        # Convert to Document objects
        doc_objects = [
            Document(
                content=doc.get('content', doc.get('page_content', '')),
                metadata=doc.get('metadata', {}),
                score=doc.get('score', 0.0)
            )
            for doc in documents
        ]
        
        # Rerank
        reranked_docs = self.reranker.rerank(query, doc_objects, top_k)
        
        # Convert back to dictionaries
        results = []
        for doc in reranked_docs:
            results.append({
                'content': doc.content,
                'metadata': doc.metadata,
                'original_score': doc.score,
                'rerank_score': doc.rerank_score,
                'combined_score': (doc.score + doc.rerank_score) / 2  # Average both scores
            })
        
        return results
