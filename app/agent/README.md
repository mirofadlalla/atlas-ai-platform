# Atlas AI Agent - Complete Documentation

**Module**: `app/agent`  
**Purpose**: Autonomous multi-step reasoning using LangGraph  
**Last Updated**: March 2026

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Agent Architecture](#agent-architecture)
3. [State Machine & Node Breakdown](#state-machine--node-breakdown)
4. [LangGraph Workflow](#langgraph-workflow)
5. [Supported Actions](#supported-actions)
6. [Streaming & Real-time Updates](#streaming--real-time-updates)
7. [Cost & Token Tracking](#cost--token-tracking)
8. [File Structure](#file-structure)
9. [API Integration](#api-integration)
10. [Monitoring & Telemetry](#monitoring--telemetry)
11. [Configuration](#configuration)
12. [Examples & Usage](#examples--usage)

---

## 🧠 Overview

The Agent system is an autonomous reasoning engine built on **LangGraph**, a framework for building stateful, multi-step AI workflows. It transforms complex questions into structured reasoning processes, leveraging both knowledge bases (RAG) and relational databases (SQL) to provide comprehensive answers.

### Key Capabilities

✅ **Multi-Step Reasoning**
- Decomposes complex questions into manageable sub-questions
- Sequential or parallel execution planning
- State-machine based workflow coordination

✅ **Intelligent Tool Selection**
- Automatically decides between SQL queries and semantic search
- Routes to RAG for knowledge base queries
- Executes SQL for quantitative database questions
- Combines results for compound questions

✅ **Real-time Streaming**
- Server-Sent Events (SSE) for live response updates
- Stream tokens as LLM generates response
- Display thought process to users in real-time

✅ **Comprehensive Tracking**
- Cost accounting (LLM tokens, embedding API calls)
- Execution latency metrics (step-by-step timing)
- Thought process logging for transparency
- Complete audit trail for compliance

✅ **Tenant Isolation**
- All queries filtered by tenant_id
- Rate limiting per tenant
- Cost tracking per tenant
- Separate execution contexts

✅ **Error Handling & Retry Logic**
- Graceful fallbacks when tools fail
- Timeout protection on long-running tasks
- Custom exception handling per node

---

## 🏗️ Agent Architecture

### System Diagram

```
                        User Question (SSE connection)
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │    DECOMPOSE NODE            │
                    │  • Analyze question          │
                    │  • Split into sub-questions  │
                    │  • Create execution plan     │
                    └────────────┬─────────────────┘
                                 │
                  ┌──────────────────────────────┐
                  │   AGENT LOOP (per sub-Q)    │
                  │                              │
                  ├─────────────────────────────┤
                  │   THOUGHT NODE (Decision)   │
                  │  • Analyze current Q        │
                  │  • Choose: SQL|Retrieval    │
                  │  • Track costs/tokens       │
                  └────────┬──────┬─────────────┘
                           │      │
                           ▼      ▼
                    ┌─────────┐  ┌──────────────┐
                    │SQL NODE │  │RETRIEVAL NODE│
                    │Execute: │  │Execute:      │
                    │-Secure  │  │-Vector search│
                    │-Parameterized │-Reranking │
                    │-Tenant-level  │-Cached    │
                    └────┬────┘  └────┬─────────┘
                         │            │
                         └──────┬─────┘
                                │
                    ┌───────────▼─────────────┐
                    │  FINISH NODE            │
                    │  • Aggregate results    │
                    │  • Generate answer      │
                    │  • Stream via SSE       │
                    │  • Log metrics          │
                    └───────────┬─────────────┘
                                │
                                ▼
                        Response to User

                    ┌─────────────────────────┐
                    │    DATABASE LOGGING     │
                    │  • Store run record     │
                    │  • Store costs          │
                    │  • Store full trace     │
                    │  • Update metrics       │
                    └─────────────────────────┘
```

---

## 🎯 State Machine & Node Breakdown

### AgentState (TypedDict Schema)

```python
# File: app/agent/core/state.py

class AgentState(TypedDict):
    # Input/Output
    question: str                          # Original user question
    tenant_id: int                         # Multi-tenant isolation
    user_id: int                          # Audit trail
    
    # Processing
    sub_questions: List[str]              # Decomposed questions
    current_question_index: int           # Current sub-Q being processed
    
    # Tool Results
    sql_result: Optional[str]             # SQL query output
    retrieval_results: List[Document]    # RAG chunks retrieved
    
    # Reasoning
    thoughts: List[str]                   # Internal reasoning steps
    actions: List[ActionDecision]         # Tool selection decisions
    
    # Tracking
    loop_count: int                       # Number of agent loops
    total_tokens: int                     # LLM tokens used
    total_cost: float                     # USD cost
    start_time: float                     # Execution start (unix timestamp)
    
    # Final Output
    final_answer: str                     # Synthesized answer
    sources: List[Dict]                   # Citation metadata
```

### Node 1: Decompose Node

**File**: `nodes/decompose_node.py`

**Purpose**: Analyzes the user's question and splits it into manageable sub-questions

**Process**:
1. Receive user question
2. Call LLM with reasoning prompt:
   ```
   "Is this a compound question? Does it ask for multiple pieces of information?"
   ```
3. LLM decides: is_compound (true/false)
4. If compound → generate sub-questions list
5. If simple → wrap as single question

**Input**:
```python
{
    "question": "How many users registered in Q4 and what was their average spend?"
}
```

**Output**:
```python
{
    "sub_questions": [
        "How many users registered in Q4?",
        "What was the average spend for Q4 users?"
    ],
    "current_question_index": 0
}
```

**Cost**: 1 LLM call per original question

**Latency**: ~500ms (LLM inference)

### Node 2: Thought Node (Main Decision Hub)

**File**: `nodes/thought_node.py`

**Purpose**: Decision-making engine - analyzes current sub-question and decides next action

**Process**:
1. Examine current sub-question
2. Call LLM with routing prompt:
   ```
   "Does this question require:
   - SQL (quantitative, database data)?
   - Retrieval (knowledge base, documents)?
   - Finish (I have enough info)?"
   ```
3. LLM returns ActionDecision with thought + action
4. Track tokens and reasoning

**Decision Logic** (LLM-driven):

**Example Decisions**:

| Question | Thought | Action |
|----------|---------|--------|
| "What was Q4 revenue?" | "This is a financial metric, needs database" | `sql` |
| "Explain our RAG architecture" | "This needs knowledge base context" | `retrieval` |
| "How many users AND their profiles?" | "First use SQL for count, then retrieval for profiles" | `sql` (first) → `retrieval` |
| "Summarize the results" | "I have all info needed, can synthesize answer" | `finish` |

**Input**:
```python
{
    "question": "How many users registered in Q4?",
    "retrieval_results": [],  # Empty on first run
    "sql_result": None
}
```

**Output**:
```python
{
    "thought": "This is asking for a count from the database",
    "action": "sql"  # Options: "sql", "retrieval", "finish"
}
```

**Cost**: 1 LLM call per sub-question (multiple if complex)

**Latency**: ~300-500ms per decision

### Node 3: SQL Node (Database Query Executor)

**File**: `nodes/sql_node.py`

**Purpose**: Generates and executes secure SQL queries

**Process**:
1. Receive question from Thought Node
2. Call LLM with SQL generation prompt:
   ```
   "Generate a SQL query to answer: <question>
   - Use ONLY these tables: users, orders, products
   - Include WHERE clause for tenant_id = <current_tenant>
   - LIMIT results to 1000 rows
   - Return JSON"
   ```
3. Parse generated SQL (extract from markdown blocks)
4. **Validate** SQL (prevent injection):
   - Check for dangerous keywords (DROP, DELETE, INSERT)
   - Verify only SELECT operations
   - Append tenant_id filter automatically
5. Execute with parameter binding (NOT string concatenation)
6. Return results as JSON

**Security Measures**:
- ✅ No string concatenation (uses parameterized queries)
- ✅ Tenant isolation enforced
- ✅ Forbidden operations blocked
- ✅ Query result limiting (1000 rows)
- ✅ Timeout protection
- ✅ Audit logging of all SQL executions

**Input**:
```python
{
    "question": "How many users registered in Q4?",
    "tenant_id": 42,
    "action": "sql"
}
```

**Output**:
```python
{
    "sql_result": json.dumps({
        "query": "SELECT COUNT(*) FROM users WHERE DATE_PART('quarter', created_at) = 4 AND tenant_id = 42",
        "result": 1523,
        "row_count": 1
    })
}
```

**Cost**: 1 LLM call + database execution

**Latency**: 300-2000ms (depends on query complexity)

**Limitations**:
- READ only (SELECT statements)
- Max 1000 rows returned
- 30-second execution timeout
- Tenant isolation enforced

### Node 4: Retrieval Node (Knowledge Base Search)

**File**: `nodes/retrieval_node.py`

**Purpose**: Executes semantic search against knowledge base

**Process**:
1. Receive question from Thought Node
2. Call RAG pipeline (from `app/rag`):
   - Generate query embedding
   - Check 3-tier cache (RAM → Redis → DB)
   - Qdrant hybrid search (Dense + Sparse)
   - Cross-encoder reranking
   - Return top-K chunks (default: 3)
3. Format results as Document objects
4. Return with metadata

**Features**:
- ✅ Hybrid semantic search
- ✅ 3-tier caching (sub-millisecond to 2-second)
- ✅ Cross-encoder reranking
- ✅ Tenant isolation
- ✅ Source citation tracking

**Input**:
```python
{
    "question": "Explain our RAG architecture",
    "tenant_id": 42,
    "action": "retrieval"
}
```

**Output**:
```python
{
    "retrieval_results": [
        Document(
            page_content="RAG (Retrieval-Augmented Generation) is...",
            metadata={"source": "Architecture.pdf", "page": 5}
        ),
        Document(
            page_content="The hybrid search combines dense and sparse embeddings...",
            metadata={"source": "Design.pdf", "page": 12}
        ),
        Document(
            page_content="Reranking uses cross-encoders for fine-grained scoring...",
            metadata={"source": "Design.pdf", "page": 14}
        )
    ]
}
```

**Cost**: 1 embedding API call + LLM generation (cached if applicable)

**Latency**: 10-2000ms (depending on cache level)

### Node 5: Finish Node (Answer Synthesis)

**File**: `nodes/finish_node.py`

**Purpose**: Aggregates results and generates final answer

**Process**:
1. Gather all results (SQL + Retrieval)
2. Check if all sub-questions answered
3. If not all answered → loop back to Thought Node
4. If all answered → synthesize final answer:
   ```
   "Using the following information:
   [SQL results]
   [Retrieval results]
   
   Answer the original question: [question]"
   ```
5. Call LLM to generate comprehensive answer
6. Extract citations from sources
7. Return final_answer + sources
8. Stream result via SSE to user

**Input** (example):
```python
{
    "question": "How many Q4 users and explain their behavior?",
    "sql_result": "Q4 had 1523 new users",
    "retrieval_results": [
        Document(...content about user behavior patterns...)
    ],
    "current_question_index": 1,  # Second sub-question done
    "sub_questions": [
        "How many users registered in Q4?",
        "What factors affect Q4 user behavior?"
    ]
}
```

**Output**:
```python
{
    "final_answer": "In Q4, we had 1523 new user registrations...",
    "sources": [
        {"type": "SQL", "value": "Database query result"},
        {"type": "Document", "source": "UserBehavior.pdf", "page": 8}
    ]
}
```

**Cost**: 1 final LLM call + aggregation

**Latency**: ~300-800ms

---

## 🔄 LangGraph Workflow

### How LangGraph Coordinates Nodes

**Framework**: LangGraph (from LangChain ecosystem)

**Graph Definition** (in `app/agent/core/graph.py`):

```python
from langgraph.graph import StateGraph

# Create workflow graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("decompose", decompose_node)
workflow.add_node("thought", thought_node)
workflow.add_node("sql", sql_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("finish", finish_node)

# Add edges (workflow connections)
workflow.add_edge("decompose", "thought")  # Always go thought after decompose

# Conditional edges (routing based on decision)
workflow.add_conditional_edges(
    "thought",
    route_decision,  # Function that reads state["action"] and decides
    {
        "sql": "sql",
        "retrieval": "retrieval",
        "finish": "finish"
    }
)

# SQL and Retrieval both lead back to Thought (loop)
workflow.add_edge("sql", "thought")
workflow.add_edge("retrieval", "thought")

# Finish exits the loop
workflow.add_edge("finish", "__end__")

# Compile the graph
agent = workflow.compile()
```

### Execution Example

```
Initial: question = "How many Q4 users + explain behavior?"
         sub_questions = ["How many...", "Explain..."]
         current_question_index = 0

Step 1: decompose_node()
  → Output: sub_questions ready

Step 2: thought_node()
  → question = "How many users registered in Q4?"
  → Decision: action = "sql"

Step 3: sql_node()
  → Executes SQL: SELECT COUNT(*) FROM users WHERE ...
  → Returns: sql_result = "1523 users"
  → current_question_index = 1 (move to next sub-Q)

Step 4: thought_node() [Loop]
  → question = "Explain Q4 user behavior"
  → Decision: action = "retrieval"

Step 5: retrieval_node()
  → Searches knowledge base
  → Returns: retrieval_results = [doc1, doc2, doc3]

Step 6: thought_node() [Loop]
  → All sub-questions are answered
  → Decision: action = "finish"

Step 7: finish_node()
  → Synthesizes: sql_result + retrieval_results
  → Calls LLM for final answer
  → Streams answer via SSE
  → Logs to database

Output: final_answer with full citation trail
```

---

## 🛠️ Supported Actions

### 1. SQL Action

**When**: Question requires data from database
- Quantitative queries (count, sum, average)
- Time-series data
- Transactional information

**Security**:
- Parameterized queries only
- Tenant isolation guaranteed
- Maximum 1000 rows
- 30-second timeout

### 2. Retrieval Action

**When**: Question requires knowledge base context
- Explanation questions
- Document references
- Policy/procedure lookups
- Technical documentation

**Features**:
- Hybrid semantic search
- Cross-encoder reranking
- Multi-level caching
- Source citations

### 3. Finish Action

**When**: Agent has sufficient information
- All sub-questions answered
- Enough context gathered
- Ready to synthesize final response

**Output**:
- Final comprehensive answer
- Source citations
- Cost accounting

---

## 📡 Streaming & Real-time Updates

### Server-Sent Events (SSE)

**Endpoint**: `GET /api/agent/reason?stream=true`

**Process**:
1. Client establishes SSE connection
2. Agent processes question (internally)
3. Stream intermediate results:
   - Tokens as they're generated
   - Thought process updates
   - Tool execution results
   - Cost/token accumulation

**SSE Message Format**:

```javascript
// Token streaming
data: {"type": "token", "content": "In", "cost": 0.0001}
data: {"type": "token", "content": " Q4", "cost": 0.0001}

// Thought update
data: {"type": "thought", "content": "I need to query the database for Q4 metrics"}

// Tool result
data: {"type": "tool_result", "tool": "sql", "result": "1523 users registered"}

// Cost update
data: {"type": "cost_updated", "total_tokens": 1250, "total_cost_usd": 0.045}

// Final answer
data: {"type": "final_answer", "content": "In Q4, we had 1523 registrations..."}
data: [DONE]
```

**Client Implementation** (JavaScript):

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/agent/reason?stream=true',
  { headers: { Authorization: 'Bearer <token>' } }
);

eventSource.addEventListener('token', (e) => {
  const data = JSON.parse(e.data);
  console.log('Token:', data.content);
});

eventSource.addEventListener('thought', (e) => {
  const data = JSON.parse(e.data);
  console.log('Agent thinking:', data.content);
});

eventSource.addEventListener('final_answer', (e) => {
  const data = JSON.parse(e.data);
  console.log('Final Answer:', data.content);
  eventSource.close();
});
```

---

## 💰 Cost & Token Tracking

### Cost Accounting Model

Every agent execution tracks:

| Component | Cost Source | Example |
|-----------|-------------|---------|
| **Decompose** | LLM tokens | 250 tokens @ $0.0001/token = $0.025 |
| **Per Sub-Q (Thought)** | LLM tokens | 150 tokens @ $0.0001/token = $0.015 |
| **SQL Query** | LLM tokens + database | 300 tokens = $0.030 |
| **Retrieval** | Embedding API + LLM | ~$0.002 (if cached: $0) |
| **Finish** | LLM tokens | 400 tokens = $0.040 |
| **TOTAL** | Sum | ~$0.112 per query |

### Implementation

```python
# File: app/agent/core/state.py

class AgentCost:
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
        self.breakdown = {}
    
    def add_cost(self, step: str, tokens: int, cost: float):
        """Track cost per node"""
        self.total_tokens += tokens
        self.total_cost += cost
        self.breakdown[step] = {"tokens": tokens, "cost": cost}
        
        # Log to Prometheus
        agent_cost_total.labels(step=step).inc(cost)

# Usage in each node
cost_tracker = state.get("cost_tracker", AgentCost())
tokens_used = response.usage.total_tokens
cost = (tokens_used / 1000) * 0.0001
cost_tracker.add_cost("thought_node", tokens_used, cost)
state["cost_tracker"] = cost_tracker
```

### Metrics

```promql
# Prometheus: Average cost per query
rate(atlas_agent_cost_total[1h]) / rate(atlas_agent_executions_total[1h])

# Cost by step
sum by (step) (increase(atlas_agent_cost_total[1d]))
```

---

## 📁 File Structure

```
app/agent/
├── README.md                           ← You are here
├── schemas.py                          # Pydantic models (ActionDecision, etc.)
│
├── core/
│   ├── state.py                        # AgentState TypedDict
│   ├── graph.py                        # LangGraph workflow definition
│   ├── router.py                       # Conditional routing logic
│   └── config.py                       # Agent configuration
│
├── nodes/
│   ├── __init__.py
│   ├── decompose_node.py              # Question decomposition
│   ├── thought_node.py                # Decision making
│   ├── sql_node.py                    # SQL generation & execution
│   ├── retrieval_node.py              # RAG integration
│   └── finish_node.py                 # Answer synthesis
│
└── tools/
    ├── sql_executor.py                # Safe SQL execution wrapper
    ├── retriever_tool.py              # RAG pipeline wrapper
    └── validators.py                  # Input validation
```

---

## 🔌 API Integration

### Execute Agent with Streaming

```bash
POST /api/agent/reason
Authorization: Bearer <token>

Body: {
  "question": "How many Q4 users and what was their engagement?",
  "stream": true
}

Response: Server-Sent Events stream
```

### Get Agent Run History

```bash
GET /api/agent/runs?page=1&limit=20
Authorization: Bearer <token>

Response: {
  "runs": [
    {
      "run_id": "uuid-123",
      "question": "How many Q4 users...",
      "final_answer": "In Q4, we had...",
      "total_tokens": 1250,
      "total_cost_usd": 0.045,
      "execution_time_ms": 2345,
      "status": "completed",
      "created_at": "2026-03-05T10:30:45Z"
    }
  ],
  "total": 482
}
```

### Get Detailed Run Trace

```bash
GET /api/agent/runs/{run_id}
Authorization: Bearer <token>

Response: {
  "run_id": "uuid-123",
  "question": "...",
  "decomposed_questions": ["Q1", "Q2"],
  "execution_trace": [
    {
      "node": "decompose",
      "output": {...},
      "duration_ms": 450
    },
    {
      "node": "thought",
      "output": {"thought": "...", "action": "sql"},
      "duration_ms": 320
    },
    ...
  ],
  "final_answer": "...",
  "cost_breakdown": {...}
}
```

---

## 📊 Monitoring & Telemetry

### Prometheus Metrics

```
# Agent Executions
atlas_agent_executions_total{status="completed|failed|timeout"}
atlas_agent_execution_duration_seconds

# Tokens & Costs
atlas_agent_tokens_total{node="decompose|thought|sql|retrieval|finish"}
atlas_agent_cost_usd_total{node="..."}

# Node Metrics
atlas_agent_thought_count{tenant_id="42"}
atlas_agent_tool_invocations_total{tool="sql|retrieval"}
atlas_agent_tool_success_rate{tool="sql|retrieval"}

# Routing Decisions
atlas_agent_action_count{action="sql|retrieval|finish"}
```

### Grafana Dashboards

**Agent Performance Dashboard**:
- Execution time histogram (p50, p95, p99)
- Cost distribution by node
- Token consumption trends
- Success/failure rates
- Tool invocation frequency

### Structured Logging

```json
{
  "timestamp": "2026-03-05T10:30:45Z",
  "level": "INFO",
  "logger": "app.agent.core.graph",
  "message": "Agent execution completed",
  "run_id": "uuid-123",
  "tenant_id": 42,
  "question": "How many Q4 users?",
  "execution_time_ms": 2345,
  "tokens_used": 1250,
  "cost_usd": 0.045,
  "status": "completed",
  "nodes_executed": ["decompose", "thought", "sql", "finish"],
  "tools_used": ["sql"]
}
```

---

## ⚙️ Configuration

```bash
# .env file
# Agent Behavior
AGENT_MAX_ITERATIONS=10               # Max loops before timeout
AGENT_TIMEOUT_SECONDS=60              # Overall execution timeout
AGENT_DECOMPOSE_ENABLED=true          # Enable question decomposition

# SQL Execution
SQL_QUERY_TIMEOUT=30                  # Query execution timeout
SQL_MAX_ROWS=1000                     # Result limit
SQL_NAMESPACE="public"                # Allowed schema

# Retrieval
VECTOR_SEARCH_TOP_K=3                 # Chunks to retrieve
USE_RERANKER=true                     # Enable cross-encoder reranking

# Cost Tracking
LLM_TOKEN_COST_PER_K=0.0001           # $ per 1000 tokens (adjust per model)
EMBEDDING_COST_PER_K=0.00002          # $ per 1000 embedding tokens

# Streaming
SSE_STREAMING_ENABLED=true            # Enable Server-Sent Events
SSE_CHUNK_SIZE=1024                   # Bytes per stream chunk
```

---

## 💡 Examples & Usage

### Example 1: Simple Question (Single Node)

```
Question: "What was our Q4 revenue?"

Execution path:
1. Decompose: Not compound → single question
2. Thought: Needs SQL → action = "sql"
3. SQL: Query database → "$5.2M"
4. Finish: Synthesize answer

Final answer: "Our Q4 revenue was $5.2M"
Duration: ~1.5 seconds
Cost: ~$0.015
```

### Example 2: Complex Question (Multiple Tools)

```
Question: "How many users registered in Q4 and explain their behavior patterns?"

Execution path:
1. Decompose: Compound → 2 sub-questions
2. Thought (Q1): Needs SQL → "How many users..."
3. SQL: Returns 1523
4. Thought (Q2): Needs Retrieval → "Explain behavior..."
5. Retrieval: Returns 3 documents about user patterns
6. Finish: Synthesize both results

Final answer: "1523 users registered in Q4. These users typically..."
Duration: ~3.2 seconds
Cost: ~$0.045
```

### Example 3: With Streaming

```javascript
// Client-side
async function askAgent(question) {
  const response = await fetch('/api/agent/reason', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer <token>'
    },
    body: JSON.stringify({ question, stream: true })
  });
  
  const reader = response.body.pipeThrough(
    new TextDecoderStream()
  ).pipeThrough(
    new TransformStream({
      transform(chunk, controller) {
        controller.enqueue(chunk);
      }
    })
  ).getReader();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    console.log(value);
  }
}
```

---

## 🐛 Troubleshooting

### Agent Hangs (Timeout)

- Check logs for which node is stuck
- Increase `AGENT_TIMEOUT_SECONDS` if needed
- Verify database/vector search are responding

### Cost Higher Than Expected

- Check `cost_breakdown` in run trace
- Verify LLM model is correct (GPT-4 is more expensive)
- Review `AGENT_MAX_ITERATIONS` (more loops = more cost)

### Incorrect Routing Decisions

- Agent might be confused about tool choice
- Try simpler question phrasing
- Check LLM model (use GPT-4 for better reasoning)

---

**Version**: 2.0.0  
**Last Updated**: March 2026  
**Framework**: LangGraph + OpenAI  
**Key Feature**: Multi-step autonomous reasoning with streaming
