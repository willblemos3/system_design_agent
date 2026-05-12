# GenAI Platform — Spec-Driven Blueprint

## Goal

Build a **clean, modular, provider-agnostic GenAI platform** that is easy to understand, use, test, maintain, extend, and replace components — notebook-friendly and production-friendly.

The goal is **not** to build isolated agent demos.

The goal is to build a **platform** where models, embeddings, vector stores, tools, runtimes, and protocols can evolve independently without breaking business logic.

---

# Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CONSUMER LAYER                              │
│                                                                      │
│     Notebook          ADK Agent       LangChain        MCP Client   │
└────────┬──────────────────┬───────────────┬─────────────────┬───────┘
         │                  │               │                 │
┌────────▼──────────────────▼───────────────▼─────────────────▼───────┐
│                          RUNTIME LAYER                               │
│                                                                      │
│        ADKRuntime          LangChainRuntime         MCPAdapter       │
│                                                                      │
│   run() │ stream() │ invoke_tool() │ handoff()                       │
│                                                                      │
│   Auto-saves each turn to MemoryProvider (user query + agent reply). │
│   Each adapter reads tool.schema() and wraps it into the            │
│   framework-specific registration format.                            │
└──────────────────────┬──────────────────────────┬────────────────────┘
                       │                          │
          ┌────────────▼──────────┐   ┌───────────▼───────────────────┐
          │      TOOL LAYER       │   │       MEMORY LAYER            │
          │                       │   │                               │
          │  CandidateSearchTool  │   │  VectorMemoryProvider         │
          │  SearchMemoryTool     │   │                               │
          │                       │   │  save(MemoryRecord)           │
          │  execute() → Result   │   │  search(query, user_id, ...)  │
          │  schema()  → Schema   │   │  get_session(session_id, ...) │
          └────────────┬──────────┘   │                               │
                       │              │  Backed by VectorStore        │
          ┌────────────▼──────────┐   │  + EmbeddingProvider          │
          │   APPLICATION LAYER   │   └───────────────────────────────┘
          │                       │
          │  CandidateRetriever   │
          │  query → embed        │
          │        → search       │
          │        → results      │
          └────────────┬──────────┘
                       │
┌──────────────────────▼───────────────────────────────────────────────┐
│                        FOUNDATION LAYER                              │
│                                                                      │
│  ┌──────────────────┐  ┌───────────────────┐  ┌───────────────────┐ │
│  │   Embeddings     │  │   Vector Store    │  │   LLM Provider   │ │
│  │                  │  │                   │  │                   │ │
│  │  embed()         │  │  create_index()   │  │  generate()       │ │
│  │  embed_batch()   │  │  insert()         │  │  structured_      │ │
│  │                  │  │  search()         │  │    generate()     │ │
│  │  Providers:      │  │                   │  │  stream()         │ │
│  │  · Gemini   ✅   │  │  Providers:       │  │                   │ │
│  │  · OpenAI        │  │  · FAISS     ✅   │  │  Providers:       │ │
│  │  · Local         │  │  · Milvus    ✅   │  │  · Gemini    ✅   │ │
│  └──────────────────┘  │  · Vertex AI      │  │  · OpenAI         │ │
│                        └───────────────────┘  │  · Claude         │ │
│                                               └───────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

**Portability rule:** swapping any provider touches only the wiring line.
Swapping a runtime touches only the runtime adapter. Business logic never changes.

---

# Engineering Principles

**Abstract only what is actually varying.**

We only create contracts for components that already have multiple providers, are expected to change, or create infrastructure coupling.

| Layer | Abstracted | Reason |
|---|---|---|
| Embeddings | ✅ | Multiple providers in use |
| Vector Store | ✅ | Multiple providers validated |
| LLM | ✅ | Multiple providers planned |
| Tools | ✅ | Must run across runtimes |
| Runtime | ✅ | ADK and LangChain differ fundamentally |
| Memory | ✅ | Implemented — per-message, user+session scope |
| A2A / PubSub | ⏳ | Patterns still unknown — explore first |

---

# Development Model

Every component follows:

```
Specification → Contract → Harness → Implementation → Provider Certification
```

**Harnesses are not unit tests.** Harnesses validate architectural integrity.

The criterion is:

> Swap a provider. If business logic changes, the abstraction failed.

---

# Foundation Layer

## 1. Embedding Provider

**File:** `src/foundation/embeddings/embedding_provider.py`

### Contract

```python
class EmbeddingProvider:
    def embed(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
```

### Providers

- `GeminiEmbeddingProvider` ✅ (current)
- `OpenAIEmbeddingProvider`
- `LocalEmbeddingProvider`

---

## 2. Vector Store

**Files:** `src/foundation/vector_store/`

### Contract

```python
class VectorStore:
    def create_index(self, index_name: str, schema: dict): ...
    def insert(self, index_name: str, records: list[VectorRecord]): ...
    def search(self, index_name: str, query_vector: list[float], top_k: int) -> list[SearchResult]: ...
```

### Harness Passed

```
Milvus → FAISS   ✅  Business logic unchanged.
```

### Providers

- `FAISSVectorStore` ✅
- `MilvusVectorStore` ✅
- `VertexVectorStore` (planned)

---

## 3. LLM Provider

**File:** `src/foundation/llm/llm_provider.py`

### Contract

```python
class LLMProvider:
    def generate(self, prompt: str, **kwargs) -> str: ...
    def structured_generate(self, prompt: str, schema: type[BaseModel], **kwargs) -> BaseModel: ...
    def stream(self, prompt: str, **kwargs) -> Iterator[str]: ...
```

### Providers

- `GeminiProvider` (next)
- `OpenAIProvider`
- `ClaudeProvider`

---

# Application Layer

## Candidate Retriever

**File:** `src/applications/retrieval/candidate_retriever.py`

```
query → EmbeddingProvider.embed() → VectorStore.search() → list[SearchResult]
```

No framework coupling. No tool coupling. Pure business logic.

---

# Tool Layer

Tools are the **portability boundary** between business logic and runtimes.

Every tool exposes two contracts:

```python
class Tool:
    def execute(self, **kwargs) -> ToolResult: ...
    def schema(self) -> ToolSchema: ...
```

`execute()` runs the capability.
`schema()` describes it — name, description, parameters as JSON Schema.

Runtime adapters call `schema()` to register the tool in their framework-specific format. They call `execute()` to invoke it. No framework logic ever enters the tool.

### ToolSchema contract

```python
@dataclass
class ToolParameter:
    name: str
    type: str          # "string" | "integer" | "number" | "boolean" | "array" | "object"
    description: str
    required: bool = True

@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: list[ToolParameter]

@dataclass
class ToolResult:
    content: Any
    error: str | None = None
```

### Why schema() closes the portability gap

Without `schema()`:

```
ADKRuntime        — reads tool description from ADK-specific declaration
LangChainRuntime  — reads tool description from @tool decorator or BaseTool
MCPAdapter        — reads tool description from MCP JSON Schema

→ Each adapter makes assumptions about how to read the tool.
→ Adding a new runtime requires touching the tool.
```

With `schema()`:

```
Every runtime calls tool.schema()
Every runtime translates ToolSchema → its own format
The tool knows nothing about frameworks.

→ Adding a new runtime requires only a new adapter.
→ The tool is never touched.
```

### Tools

**Files:** `src/tools/`

| Tool | Description |
|---|---|
| `CandidateSearchTool` | Semantic search over candidate index |
| `SearchMemoryTool` | Retrieves relevant past turns from long-term memory |

```
CandidateSearchTool
    ↓
CandidateRetriever
    ↓
EmbeddingProvider  +  VectorStore
```

The same tools run in notebooks, ADK, LangChain, and MCP without modification.

---

# Runtime Layer

Introduced after the Tool layer is validated.

### Contract

```python
class AgentRuntime:
    def run(self, input: str, tools: list[Tool]) -> str: ...
    def stream(self, input: str, tools: list[Tool]) -> Iterator[str]: ...
    def invoke_tool(self, tool: Tool, kwargs: dict) -> ToolResult: ...
    def handoff(self, target_agent: str, context: dict): ...
```

### Adapter responsibility

Each adapter:
1. Calls `tool.schema()` to build the framework-specific tool declaration
2. Calls `tool.execute(**kwargs)` when the framework triggers a tool call
3. Translates framework output back to standard types

### Providers

- `ADKRuntime` (next)
- `LangChainRuntime`

> **Note:** `handoff()` semantics differ significantly between ADK and LangChain.
> Follow the same strategy as Memory: implement both concretely before finalising the contract.

---

# Protocol Layer

Introduced after tools and agents are validated end-to-end.

## MCP

MCP is a **capability exposure layer**, not a business logic layer.

```
WITHOUT MCP                          WITH MCP

Notebook / Agent                     Notebook / Agent / External Runtime
       ↓                                            ↓
CandidateSearchTool              MCP Server → CandidateSearchTool
       ↓                                            ↓
CandidateRetriever               CandidateRetriever
```

`MCPAdapter` calls `tool.schema()` to build the MCP tool JSON Schema. Same pattern as every other runtime adapter.

### Rules

- Do not import MCP into retrievers or tools
- Do not expose vector stores directly via MCP
- Do not let MCP payloads leak into business logic

---

# Memory Layer

**Files:** `src/foundation/memory/`

Long-term memory is built on the same `VectorStore` + `EmbeddingProvider` contracts already in use — no new infrastructure.

### Contract

```python
class MemoryProvider:
    def save(self, record: MemoryRecord) -> None: ...
    def search(self, query: str, user_id: str, top_k: int, session_id: str | None) -> list[MemoryRecord]: ...
    def get_session(self, session_id: str, user_id: str) -> list[MemoryRecord]: ...
```

### MemoryRecord — the domain object

```python
@dataclass
class MemoryRecord:
    id: str
    user_id: str
    session_id: str
    role: str        # "user" | "agent"
    text: str
    timestamp: str   # ISO 8601
```

`MemoryRecord` carries no embedding. The embedding is computed at save time by `EmbeddingProvider` and stored inside `VectorStore` as part of `VectorRecord`. The domain object never knows about infrastructure — the same separation used everywhere else in the platform.

### How VectorMemoryProvider.save() works

```
MemoryRecord.text
    ↓
EmbeddingProvider.embed(text)  →  vector
    ↓
VectorStore.insert(VectorRecord(id, vector, metadata={all MemoryRecord fields}))
```

The vector lives in the index. The domain record stays clean.

### Scope and filtering

Memory is scoped by `user_id` + `session_id`. Search can filter by either or both.

FAISS has no native metadata filtering — `VectorMemoryProvider` over-fetches (top_k × 20) and filters in Python. For production scale, replace `FAISSVectorStore` with a store that supports predicate pushdown (Milvus, pgvector). Only the wiring changes.

### Auto-save

`ADKRuntime` saves both turns automatically after each cycle:

```
user query  →  agent answer  →  save(user record) + save(agent record)
```

No `SaveMemoryTool`. No extra reasoning budget. The agent never knows saving is happening.

### Providers

- `VectorMemoryProvider` ✅ (FAISS or any VectorStore)

### POC vs Production

The contracts are production-grade. The providers are POC compromises.

| What | Current (POC) | Production replacement |
|---|---|---|
| Vector storage | `FAISSVectorStore` — in-memory, lost on restart | pgvector / Qdrant / Weaviate — persistent + native filtering |
| Metadata filtering | Over-fetch ×20, filter in Python | Predicate pushdown (`WHERE user_id = ?`) in the DB layer |
| Session management | `_runtimes` dict in process memory | Redis / database — survives restarts, scales horizontally |
| Tool user scope | `search_memory_tool._user_id` mutated at runtime | `user_id` injected per-request, tool instantiated per-request |
| Authorization | None — any caller can pass any `user_id` | Auth layer validates `user_id` matches the authenticated token |
| ADK sessions | `InMemorySessionService` — lost on restart | Persistent session service |

None of these replacements touch `MemoryProvider`, `MemoryRecord`, `VectorMemoryProvider`, `SearchMemoryTool`, or `ADKRuntime`. Only the wiring changes — which is exactly what the platform was designed for.

---

# Repository Structure

```
genai-platform/
│
├── README.md
│
├── notebooks/
│   ├── experiments/
│   ├── harness/
│   └── workshops/
│       └── platform_demo.ipynb           ← end-to-end demo (sections 0–9)
│
├── src/
│   ├── foundation/
│   │   ├── embeddings/
│   │   │   └── embedding_provider.py     ← EmbeddingProvider contract + providers
│   │   ├── vector_store/
│   │   │   ├── vector_store.py           ← VectorStore contract + data types
│   │   │   ├── faiss_store.py
│   │   │   ├── milvus_store.py
│   │   │   └── schemas.py                ← CANDIDATE_SCHEMA, MEMORY_SCHEMA
│   │   ├── memory/
│   │   │   ├── memory_provider.py        ← MemoryProvider contract + MemoryRecord
│   │   │   └── vector_memory_provider.py ← VectorMemoryProvider (FAISS or any VectorStore)
│   │   └── llm/
│   │       └── llm_provider.py           ← LLMProvider contract + providers
│   │
│   ├── applications/
│   │   └── retrieval/
│   │       └── candidate_retriever.py
│   │
│   ├── tools/
│   │   ├── tool.py                       ← Tool base class, ToolSchema, ToolResult
│   │   ├── candidate_search_tool.py
│   │   └── search_memory_tool.py         ← semantic search over conversation history
│   │
│   ├── runtime/
│   │   ├── agent_runtime.py              ← AgentRuntime contract
│   │   └── adk_runtime.py                ← ADKRuntime (auto-saves turns to MemoryProvider)
│   │
│   ├── protocols/
│   │   └── mcp/
│   │       └── mcp_adapter.py            ← MCPAdapter (uses tool.schema())
│   │
│   └── shared/
│       ├── config.py                     ← provider config (API keys, endpoints)
│       ├── dataset.py                    ← dataset loaders
│       └── exceptions.py                 ← platform-level exceptions
│
└── tests/
    ├── unit/
    ├── integration/
    └── harness/                          ← provider switching tests
```

---

# Execution Plan

## Phase 1 — Foundation ✅

| Component | Status | Harness |
|---|---|---|
| EmbeddingProvider | ✅ | GeminiEmbeddingProvider |
| VectorStore | ✅ | FAISS ↔ Milvus ✅ |
| LLMProvider | ✅ | GeminiLLMProvider |

---

## Phase 2 — Tools and Runtime ✅

| Component | Status |
|---|---|
| Tool base class (execute + schema) | ✅ |
| CandidateSearchTool | ✅ |
| SearchMemoryTool | ✅ |
| ADKRuntime (run + stream + auto-save) | ✅ |

---

## Phase 3 — Memory ✅

| Component | Status |
|---|---|
| MemoryProvider contract + MemoryRecord | ✅ |
| VectorMemoryProvider (FAISS-backed) | ✅ |
| Auto-save per turn in ADKRuntime | ✅ |
| SearchMemoryTool for agent retrieval | ✅ |

---

## Phase 4 — MCP

| Component | Status |
|---|---|
| MCPAdapter | planned |
| MCP server | planned |
| CandidateSearchTool exposed via MCP | planned |

Success criteria: same tool runs in notebook, ADK, and MCP with zero business changes.

---

# Final Validation Rule

Every abstraction must pass:

> Only wiring changes. Never business logic.

If business logic changes: the abstraction failed.
