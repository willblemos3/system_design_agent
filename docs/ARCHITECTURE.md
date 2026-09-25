# Platform Architecture

The PM agent is built on a provider-agnostic GenAI platform. This document describes that platform: its layers, contracts and the rules that keep them independent. For setup and usage of the agent, see the [README](../README.md).

## Goal

Build a **clean, modular, provider-agnostic GenAI platform** that is easy to understand, use, test, maintain, extend, and replace components — notebook-friendly and production-friendly.

The goal is **not** to build isolated agent demos.

The goal is to build a **platform** where models, embeddings, vector stores, tools, runtimes, and protocols can evolve independently without breaking business logic.

---

## Architecture

```
┌─────────────────────────── CONSUMER LAYER ───────────────────────────┐
│     Notebook       OpenAI Agent      ADK Agent       MCP Client      │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────────┐
│                          RUNTIME LAYER                               │
│              OpenAIRuntime               ADKRuntime                  │
│         run() · stream() · auto-saves to MemoryProvider             │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               │                               │
┌──────────────▼──────────┐   ┌────────────────▼──────────────────────┐
│       TOOL LAYER        │   │           APPLICATION LAYER           │
│                         │   │                                       │
│  CandidateSearchTool    │   │  CandidateRetriever                   │
│  SearchMemoryTool       │   │  query → embed() → search() → list   │
│                         │   │                                       │
│  execute() · schema()   │   └───────────────────────────────────────┘
└─────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────────┐
│                        FOUNDATION LAYER                              │
│              contracts (ABCs) — no concrete imports here             │
│                                                                      │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────┐ │
│  │  Embedding    │ │  VectorStore  │ │  LLMProvider  │ │  Memory  │ │
│  │  Provider     │ │               │ │               │ │  Provider│ │
│  │               │ │ create_index()│ │  generate()   │ │          │ │
│  │  embed()      │ │  insert()     │ │  structured   │ │  save()  │ │
│  │  embed_batch()│ │  search()     │ │  stream()     │ │  search()│ │
│  │               │ │               │ │               │ │  session │ │
│  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └────┬─────┘ │
└──────────┼─────────────────┼─────────────────┼──────────────┼───────┘
           │                 │   implemented by │              │
┌──────────▼─────────────────▼─────────────────▼──────────────▼───────┐
│                         PROVIDER LAYER                               │
│                                                                      │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────┐ │
│  │  Embeddings   │ │  VectorStore  │ │     LLM       │ │  Memory  │ │
│  │               │ │               │ │               │ │          │ │
│  │  Gemini   ✅  │ │  FAISS    ✅  │ │  Gemini   ✅  │ │  Vector  │ │
│  │  OpenAI   ✅  │ │  Milvus   ✅  │ │  OpenAI   ✅  │ │  Memory  │ │
│  └───────────────┘ └───────────────┘ └───────────────┘ │   ✅     │ │
│         ▲                ▲                              │  uses ↑  │ │
│         └────────────────┴─────── VectorMemoryProvider ─┘          │ │
└──────────────────────────────────────────────────────────────────────┘
```

**Portability rule:** swapping any provider touches only the wiring line.
Swapping a runtime touches only the runtime adapter. Business logic never changes.

---

## Engineering Principles

**Abstract only what is actually varying.**

We only create contracts for components that already have multiple providers, are expected to change, or create infrastructure coupling.

| Layer | Abstracted | Reason |
|---|---|---|
| Embeddings | ✅ | Multiple providers in use |
| Vector Store | ✅ | Multiple providers validated |
| LLM | ✅ | Multiple providers in use |
| Tools | ✅ | Must run across runtimes |
| Runtime | ✅ | OpenAI and ADK differ fundamentally |
| Memory | ✅ | Implemented — per-message, user+session scope |
| A2A / PubSub | ⏳ | Patterns still unknown — explore first |

---

## Development Model

Every component follows:

```
Specification → Contract → Harness → Implementation → Provider Certification
```

**Harnesses are not unit tests.** Harnesses validate architectural integrity.

The criterion is:

> Swap a provider. If business logic changes, the abstraction failed.

---

## Provider Configuration

**Files:** `providers.yaml` (root), `src/shared/provider_config.py`, `src/shared/factory.py`

Provider selection is centralised in `providers.yaml`. No Python code changes are needed to switch providers.

```yaml
embedding:
  primary: gemini      # switch to "openai" to use text-embedding-3-large

llm:
  primary: openai      # switch to "gemini"

runtime:
  primary: ollama      # ollama | gemini | openai | adk
  available:
    ollama:
      class: OpenAIRuntime
      model: gemma3:12b
      base_url: http://localhost:11434/v1
      requires: null   # local — no API key
```

The factory picks the adapter from each entry's `class`. Any OpenAI-compatible endpoint (Ollama, Gemini's OpenAI endpoint, …) runs on `OpenAIRuntime` by setting `base_url`, so adding one is configuration only.

Factory functions read this file and return the correct implementation:

```python
from src.shared.factory import build_runtime, build_llm_provider, build_embedding_provider

runtime            = build_runtime(instruction="...", memory_provider=mp, user_id="u1")
llm_provider       = build_llm_provider()
embedding_provider = build_embedding_provider()
```

Both embedding providers use **3072-dim vectors** (Gemini `gemini-embedding-001` and OpenAI `text-embedding-3-large`), so switching embedding provider requires no re-indexing.

---

## Foundation Layer

### 1. Embedding Provider

**File:** `src/foundation/embeddings/embedding_provider.py`

#### Contract

```python
class EmbeddingProvider:
    def embed(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
```

#### Providers

- `GeminiEmbeddingProvider` ✅ — `gemini-embedding-001` (3072-dim)
- `OpenAIEmbeddingProvider` ✅ — `text-embedding-3-large` (3072-dim)

---

### 2. Vector Store

**Files:** `src/foundation/vector_store/`

#### Contract

```python
class VectorStore:
    def create_index(self, index_name: str, schema: dict): ...
    def insert(self, index_name: str, records: list[VectorRecord]): ...
    def search(self, index_name: str, query_vector: list[float], top_k: int) -> list[SearchResult]: ...
```

#### Harness Passed

```
Milvus → FAISS   ✅  Business logic unchanged.
```

#### Providers

- `FAISSVectorStore` ✅
- `MilvusVectorStore` ✅
- `VertexVectorStore` (planned)

---

### 3. LLM Provider

**File:** `src/foundation/llm/llm_provider.py`

#### Contract

```python
class LLMProvider:
    def generate(self, prompt: str, **kwargs) -> str: ...
    def structured_generate(self, prompt: str, schema: type[BaseModel], **kwargs) -> BaseModel: ...
    def stream(self, prompt: str, **kwargs) -> Iterator[str]: ...
```

#### Providers

- `GeminiLLMProvider` ✅ — `gemini-2.0-flash`
- `OpenAILLMProvider` ✅ — `gpt-4o-mini`
- `ClaudeProvider` (planned)

---

## Application Layer

### Candidate Retriever

**File:** `src/applications/retrieval/candidate_retriever.py`

```
query → EmbeddingProvider.embed() → VectorStore.search() → list[SearchResult]
```

No framework coupling. No tool coupling. Pure business logic.

### System Design (PM agent)

**Files:** `src/applications/system_design/`

```
ExerciseRepository.get(module, exercise=None)   ← docs/system_design/module_<n>/<nn>_<name>.md
    ↓
build_pm_instruction(exercise)                  ← CO-STAR prompt, without the trade-off questions
    ↓
build_runtime(instruction=...)                  ← any AgentRuntime from providers.yaml
    ↓
PMSession                                       ← conversation + recorded solution + trade-off answers
    ↓
run_console(session)  →  SessionReport.save()   ← reports/<date>_module<n>_<exercise>.md
```

`PMSession` depends only on the `AgentRuntime` contract. The LLM handles the conversation; details, solution recording, trade-off questions and the report are deterministic. See the [README](../README.md) for usage.

---

## Tool Layer

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

#### ToolSchema contract

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

#### Why schema() closes the portability gap

Without `schema()`:

```
ADKRuntime        — reads tool description from ADK-specific declaration
OpenAIRuntime     — reads tool description from OpenAI function definition
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

#### Tools

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

The same tools run in notebooks, ADK, OpenAI, and MCP without modification.

---

## Runtime Layer

Introduced after the Tool layer is validated.

#### Contract

```python
class AgentRuntime:
    def run(self, input: str, tools: list[Tool]) -> str: ...
    def stream(self, input: str, tools: list[Tool]) -> AsyncIterator[str]: ...
    def invoke_tool(self, tool: Tool, kwargs: dict) -> ToolResult: ...
    def reset(self) -> None: ...        # clears the conversation, starts a new session
```

Runtimes keep the conversation history of the current session (user and assistant turns), so multi-turn agents stay consistent. `reset()` starts over.

#### Adapter responsibility

Each adapter:
1. Calls `tool.schema()` to build the framework-specific tool declaration
2. Calls `tool.execute(**kwargs)` when the framework triggers a tool call
3. Translates framework output back to standard types

#### Providers

- `OpenAIRuntime` ✅ — streaming agentic loop with tool call reassembly; any OpenAI-compatible endpoint via `base_url` (OpenAI, Ollama, Gemini)
- `ADKRuntime` ✅ — Google ADK with event-stream tool detection

---

## Protocol Layer

Introduced after tools and agents are validated end-to-end.

### MCP

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

#### Rules

- Do not import MCP into retrievers or tools
- Do not expose vector stores directly via MCP
- Do not let MCP payloads leak into business logic

---

## Memory Layer

**Files:** `src/foundation/memory/`

Long-term memory is built on the same `VectorStore` + `EmbeddingProvider` contracts already in use — no new infrastructure.

#### Contract

```python
class MemoryProvider:
    def save(self, record: MemoryRecord) -> None: ...
    def search(self, query: str, user_id: str, top_k: int,
               session_id: str | None, sort_by_time: bool = False) -> list[MemoryRecord]: ...
    def get_session(self, session_id: str, user_id: str) -> list[MemoryRecord]: ...
```

#### MemoryRecord — the domain object

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

#### How VectorMemoryProvider.save() works

```
MemoryRecord.text
    ↓
EmbeddingProvider.embed(text)  →  vector
    ↓
VectorStore.insert(VectorRecord(id, vector, metadata={all MemoryRecord fields}))
```

The vector lives in the index. The domain record stays clean.

#### Scope and filtering

Memory is scoped by `user_id` + `session_id`. Search can filter by either or both.

FAISS has no native metadata filtering — `VectorMemoryProvider` over-fetches (top_k × 20) and filters in Python. For production scale, replace `FAISSVectorStore` with a store that supports predicate pushdown (Milvus, pgvector). Only the wiring changes.

`sort_by_time=True` returns results in chronological order (ascending timestamp) instead of semantic similarity order. Useful when the agent needs to reconstruct conversation history rather than find the most relevant records.

#### Auto-save

Both `OpenAIRuntime` and `ADKRuntime` save both turns automatically after each cycle:

```
user query  →  agent answer  →  save(user record) + save(agent record)
```

No `SaveMemoryTool`. No extra reasoning budget. The agent never knows saving is happening.

#### User isolation

Each user gets their own `AgentRuntime` and `SearchMemoryTool` instance via `get_user_context(user_id)`. The `memory_provider` is shared — all records go into the same FAISS index — but every search is filtered by `user_id`, so users never see each other's history.

```python
def get_user_context(user_id: str) -> dict:
    if user_id not in _user_contexts:
        _user_contexts[user_id] = {
            "runtime": build_runtime(memory_provider=memory_provider, user_id=user_id),
            "memory_tool": SearchMemoryTool(memory_provider=memory_provider, user_id=user_id),
        }
    return _user_contexts[user_id]
```

To switch users mid-session, change `active_user_id` and call `get_user_context()` again — each user's history is preserved in the shared index.

#### Providers

- `VectorMemoryProvider` ✅ (FAISS or any VectorStore)

#### POC vs Production

The contracts are production-grade. The providers are POC compromises.

| What | Current (POC) | Production replacement |
|---|---|---|
| Vector storage | `FAISSVectorStore` — in-memory, lost on restart | pgvector / Qdrant / Weaviate — persistent + native filtering |
| Metadata filtering | Over-fetch ×20, filter in Python | Predicate pushdown (`WHERE user_id = ?`) in the DB layer |
| Session management | `_user_contexts` dict in process memory | Redis / database — survives restarts, scales horizontally |
| Authorization | None — any caller can pass any `user_id` | Auth layer validates `user_id` matches the authenticated token |
| ADK sessions | `InMemorySessionService` — lost on restart | Persistent session service |

None of these replacements touch `MemoryProvider`, `MemoryRecord`, `VectorMemoryProvider`, `SearchMemoryTool`, `OpenAIRuntime`, or `ADKRuntime`. Only the wiring changes — which is exactly what the platform was designed for.

---

## Final Validation Rule

Every abstraction must pass:

> Only wiring changes. Never business logic.

If business logic changes: the abstraction failed.


<img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/1fd5aaf7-70d1-4485-8c6f-70310003035f" />
