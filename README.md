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
│              run() │ stream() │ invoke_tool() │ handoff()            │
│                                                                      │
│   Each adapter reads tool.schema() and wraps it into the            │
│   framework-specific registration format. execute() is called       │
│   directly — no framework logic leaks into the tool.                │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│                           TOOL LAYER                                 │
│                                                                      │
│                      CandidateSearchTool                             │
│                                                                      │
│                   execute(**kwargs) → ToolResult                     │
│                   schema()          → ToolSchema                     │
│                                                                      │
│  schema() is the portability contract.                               │
│  It describes name, description, and parameters as JSON Schema.      │
│  Runtime adapters translate this — business logic never changes.     │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│                        APPLICATION LAYER                             │
│                                                                      │
│                       CandidateRetriever                             │
│                                                                      │
│              query → embed → vector_store.search() → results        │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│                        FOUNDATION LAYER                              │
│                                                                      │
│  ┌──────────────────┐  ┌───────────────────┐  ┌───────────────────┐ │
│  │   Embeddings     │  │   Vector Store    │  │   LLM Provider   │ │
│  │                  │  │                   │  │                   │ │
│  │  embed()         │  │  create_index()   │  │  generate()       │ │
│  │  embed_batch()   │  │  insert()         │  │  structured_      │ │
│  │                  │  │  search()         │  │    generate()     │ │
│  │  Providers:      │  │                   │  │  stream()         │ │
│  │  · Gemini        │  │  Providers:       │  │                   │ │
│  │  · OpenAI        │  │  · FAISS     ✅   │  │  Providers:       │ │
│  │  · Local         │  │  · Milvus    ✅   │  │  · Gemini         │ │
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
| Memory | ⏳ | Patterns still unknown — explore first |
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

### First Tool

**File:** `src/tools/candidate_search_tool.py`

```
CandidateSearchTool
    ↓
CandidateRetriever
    ↓
EmbeddingProvider
    ↓
VectorStore
```

The same tool runs in notebooks, ADK, LangChain, and MCP without modification.

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

# Memory

Intentionally delayed.

Patterns are still unknown. Use concrete implementations first:

- `InMemoryStore`
- `RedisStore`
- simple vector memory

Only after patterns are understood: create contracts.

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
│
├── src/
│   ├── foundation/
│   │   ├── embeddings/
│   │   │   └── embedding_provider.py     ← EmbeddingProvider contract + providers
│   │   ├── vector_store/
│   │   │   ├── vector_store.py           ← VectorStore contract + data types
│   │   │   ├── faiss_store.py
│   │   │   ├── milvus_store.py
│   │   │   └── schemas.py
│   │   └── llm/
│   │       └── llm_provider.py           ← LLMProvider contract + providers
│   │
│   ├── applications/
│   │   └── retrieval/
│   │       └── candidate_retriever.py
│   │
│   ├── tools/
│   │   ├── tool.py                       ← Tool base class, ToolSchema, ToolResult
│   │   └── candidate_search_tool.py
│   │
│   ├── runtime/
│   │   ├── agent_runtime.py              ← AgentRuntime contract
│   │   ├── adk_runtime.py
│   │   └── langchain_runtime.py
│   │
│   ├── protocols/
│   │   └── mcp/
│   │       └── mcp_adapter.py            ← MCPAdapter (uses tool.schema())
│   │
│   └── shared/
│       ├── config.py                     ← provider config (API keys, endpoints)
│       └── exceptions.py                 ← platform-level exceptions
│
└── tests/
    ├── unit/
    ├── integration/
    └── harness/                          ← provider switching tests
```

---

# Execution Plan

## Phase 1 — Foundation

Build and certify each provider contract.

| Component | Status | Harness |
|---|---|---|
| EmbeddingProvider | 🔄 refactor from embedding.py | Gemini ↔ OpenAI |
| VectorStore | ✅ done | Milvus ↔ FAISS ✅ |
| LLMProvider | next | Gemini ↔ OpenAI |

Success criteria: provider switching works with zero business logic changes.

---

## Phase 2 — Tools and Runtime

| Component | Status |
|---|---|
| Tool base class (execute + schema) | next |
| CandidateSearchTool | next |
| CandidateSearchAgent | next |
| ADKRuntime | next |

Success criteria: agent runs with tools in notebook and ADK. Same tool, no changes.

---

## Phase 3 — MCP

| Component | Status |
|---|---|
| MCPAdapter | planned |
| MCP server | planned |
| CandidateSearchTool exposed via MCP | planned |

Success criteria: same tool runs in notebook, ADK, and MCP with zero business changes.

---

## Phase 4 — Memory

Explore concrete patterns first. Contract comes after.

---

# Final Validation Rule

Every abstraction must pass:

> Only wiring changes. Never business logic.

If business logic changes: the abstraction failed.
