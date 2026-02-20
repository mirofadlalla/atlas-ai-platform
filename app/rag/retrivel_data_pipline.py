import os
import sys
from pathlib import Path

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_SYMLINKS"] = "1"

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from app.rag.steps.retriever import get_retriever


class RetrievalPipeline:
    '''
    A simple retrieval pipeline that initializes a retriever 
    for a given tenant_id and allows you to retrieve 
    relevant documents based on a query.
    '''
    def __init__(self, tenant_id: int):
        self.retriever = get_retriever(tenant_id)

    def retrieve(self, query: str):
        return self.retriever.invoke(query)

retrieval_pipeline = RetrievalPipeline(tenant_id=123)
retrieved_docs = retrieval_pipeline.retrieve("What triggers these upward or downward adjustments for non-marketable equity securities?")
print(retrieved_docs)