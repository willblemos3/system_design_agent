# Candidate Retrieval Architecture

## Goal

Build a provider-agnostic retrieval stack that supports local experimentation today and seamless migration to Google-native infrastructure (e.g. Vertex AI) later, without changing business logic.

Current focus is the **vector retrieval layer**.  
Next layers to follow the same pattern:

- Agent abstraction
- Embedding abstraction
- LLM abstraction

---

# High-Level Architecture

```text
User / Agent
     │
     ▼
CandidateRetriever
     │
     ▼
Embedding Service
     │
     ▼
VectorStore (Contract)
     │
 ┌───┼───────────────┐
 ▼   ▼               ▼
Milvus FAISS      Vertex AI
```

---

# Core Architectural Decisions

## 1. Business Logic Must Not Know the Provider

Retrieval logic should never know whether vectors are stored in:

- Milvus
- FAISS
- Vertex AI Vector Search

Provider-specific logic lives exclusively inside adapters.

### Example

```python
retriever.search(query)
```

This interface remains identical regardless of backend.

---

## 2. Contract-First Design

A generic `VectorStore` interface defines the boundary between business logic and infrastructure.

### Current contract

```python
create_index()
insert()
search()
```

Any new provider must implement this contract.

### Benefits

- backend portability
- easier testing
- easier local experimentation
- zero business logic changes during migration

---

## 3. Canonical Data Contract

All providers operate on the same internal object:

```python
VectorRecord(
    id="candidate_123",
    vector=[...],
    metadata={...}
)
```

This structure maps naturally to:

### Milvus

```text
row → vector + metadata
```

### FAISS

```text
faiss index + metadata store
```

### Vertex AI

```text
IndexDatapoint
```

### Why this matters

This avoids provider-shaped payloads leaking into notebooks or application code.

---

## 4. Schema-Driven Index Creation

Index structure is defined declaratively via schemas.

### Example

- `CANDIDATE_SCHEMA`
- `JOB_SCHEMA`

Providers translate the schema into their own implementation.

### Benefits

- consistent field definitions
- easier provider migration
- reusable indexing logic

---

## 5. Embedding Is Treated as Infrastructure

Embedding generation is isolated from retrieval logic.

Current implementation:

- Gemini Embeddings
- 3072 dimensions
- cosine similarity

Current flow:

```text
text
  ↓
embedding
  ↓
vector search
```

This layer will also become provider-agnostic.

---

# Current Flow

## Indexing

```text
DataFrame
   ↓
build_records()
   ↓
VectorRecord[]
   ↓
store.insert()
```

---

## Retrieval

```text
Query
  ↓
Gemini Embedding
  ↓
VectorStore.search()
  ↓
SearchResult[]
  ↓
CandidateRetriever
  ↓
Formatted Results
```

---

# Current Provider

## Milvus

Used for:

- local development
- free experimentation
- notebook iteration
- schema validation

Reason:

Fast local setup with minimal operational overhead.

---

# Planned Validation

## 1. Add FAISS Adapter

Purpose:

Validate that the architecture is truly provider-agnostic.

Expected validation:

Only this line should change:

```python
store = MilvusVectorStore()
```

to:

```python
store = FAISSVectorStore()
```

Everything else should remain untouched.

Success criteria:

- same schemas
- same retriever
- same notebook code
- same search interface

---

## 2. Embedding Adapter Refactor

Next abstraction:

```text
EmbeddingService
```

Target providers:

- Gemini
- OpenAI
- local embedding models

Goal:

Retrieval layer should not know which embedding provider is being used.

---

## 3. Agent Adapter Refactor

Next abstraction:

```text
AgentRuntime
```

Target providers:

- Google ADK
- LangGraph
- custom orchestration

Goal:

Tools, retrieval, and business logic remain independent of agent framework.

---

# Long-Term Migration Goal

When moving from local development to Google infrastructure, migration should require changing only infrastructure wiring.

Example:

```python
store = MilvusVectorStore()
```

to:

```python
store = VertexVectorStore()
```

No changes should be required in:

- schemas
- retrievers
- embeddings
- tools
- agents
- notebooks

This is the primary architectural constraint moving forward.