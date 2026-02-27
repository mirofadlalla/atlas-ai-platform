from prometheus_client import Counter, Histogram

class RAGMetrics:
    # 1. Counter for Token Usage
    TOKEN_USAGE_COUNTER = Counter(
        "rag_token_usage_total", 
        "Total tokens consumed by LLM", 
        ["model_name", "token_type", "tenant_id"]
    )

    # 2. Histogram for RAG Latency
    RAG_LATENCY_HISTOGRAM = Histogram(
        "rag_process_latency_seconds", 
        "Latency of RAG steps", 
        ["step", "tenant_id"] # to monitor latency for each step: retrieval, generation, etc. and per tenant
    )

    # 3. Counter for Cache Efficiency
    CACHE_HIT_COUNTER = Counter(
        "rag_cache_hits_total", 
        "Number of semantic cache hits", 
        ["status", "tenant_id"]
    )
    
    # 4. Counter for Requests (for tracking total RAG queries and their status)
    REQUEST_COUNT = Counter(
        "rag_requests_total",
        "Total number of RAG queries",
        ["tenant_id", "status"] # status: success / error
    )