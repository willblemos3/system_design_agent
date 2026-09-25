# System Design PM Agent

A conversational agent for practising recommender-system design interviews.

The agent plays the **Product Manager** of a fictional company. It presents a system design challenge, answers business questions and pushes back the way a stakeholder would. **It never helps with the technical design.** That part is up to you. When you are done, it records your solution and your answers to the trade-off questions, then saves a report.

The exercises come from a RecSys course. There is one folder per module, and they get harder as the modules progress:

| Module | Exercise | Company |
|---|---|---|
| 1 — Introduction and Evaluation Metrics | `01_norva` | NORVA, an online clothing retailer |
| 2 — Basic Models | `02_zumi` | ZUMI, a food delivery app |
| 3 — Negative Sampling | `03_meridiano` | MERIDIANO, a news aggregator |
| 4 — End to End RecSys | `04_orbe` | ORBE, a short-video platform |

```
Alex: Hi, I'm Alex, your system design agent and NORVA's representative for this challenge.
NORVA is an online clothing retailer: around 40,000 items and 180,000 orders a month.
Right now our homepage carousel is hand-picked every Monday by two merchandisers...
Would you like more details on the data we have and what we need from you?

────────────────────────────────────────────────────────────
What would you like to do?
  1. Ask a question        talk to Alex about the business
  2. See the details       data available and deliverables
  3. Submit your solution  record your proposed architecture
  4. Trade-off questions   answer questions about your design
  5. Finish                save the report and end
Type a number, or just type your question.
────────────────────────────────────────────────────────────
```

---

## Quick start

```powershell
pip install -r requirements.txt
ollama pull gemma3:12b                                  # free local model (see Setup)
python scripts/pm_chat.py --module 1                    # random exercise from module 1
```

---

## Setup

The commands below are for **Windows / PowerShell**. macOS/Linux differences are noted inline.

### 1. Requirements

- Python 3.11+
- One LLM provider. You only need **one**:
  - **Ollama**: free and local. The default model needs a GPU with about 10 GB of VRAM.
  - **Gemini**: free tier in the cloud. You only need an API key.
  - **OpenAI**: paid.

### 2. Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

> If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once. You can also skip activation and call `.venv\Scripts\python` directly.

### 3. Choose a provider

The provider is selected in [`providers.yaml`](providers.yaml). To switch, change `primary:` in the `runtime` block. No code changes are needed.

```yaml
runtime:
  primary: ollama     # ollama | gemini | openai | adk
```

**Option A: Ollama (free, local, the default)**

```powershell
winget install Ollama.Ollama        # macOS: brew install ollama | Linux: curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3:12b              # ~8 GB, one-time download
ollama list                         # gemma3:12b should be listed
```

> After installing, **close and reopen the terminal**. In VS Code, reopen **VS Code itself**. A terminal opened before the install cannot see `ollama`. On Windows the Ollama server starts on its own (look for the tray icon). If it isn't running, use `ollama serve`. With less VRAM, use `gemma3:4b` and change `model:` under `ollama` in `providers.yaml`.

**Option B: Gemini (free tier)**

1. Create an API key at https://aistudio.google.com.
2. Create a `.env` file at the repository root. It is already git-ignored.
   ```
   GOOGLE_API_KEY=your-key-here
   ```
3. Set `primary: gemini` in `providers.yaml`.

**Option C: OpenAI (paid)**

Add `OPENAI_API_KEY=...` to `.env` and set `primary: openai`.

---

## Usage

Run the script **in a terminal**: VS Code's integrated terminal, PowerShell or Windows Terminal. The "Run" button of extensions such as Code Runner sends output to the read-only *Output* panel, and from there you can't type.

```powershell
python scripts/pm_chat.py --list                        # list modules and exercises
python scripts/pm_chat.py --module 1                    # random exercise from the module
python scripts/pm_chat.py --module 2 --exercise zumi    # a specific exercise
```

| Option | Accepts |
|---|---|
| `--module` / `-m` | `2`, `module_2` |
| `--exercise` / `-e` | `zumi`, `02_zumi`, `2`. Omit it to get a random exercise. |
| `--language` | Language of the opening message. Default: `English`. After the opening, the PM replies in whatever language you write in. |
| `--pm-name` | The PM's name. Default: `Alex`. |

### The session

| Input | What happens |
|---|---|
| free text | Goes to the PM as a question. The PM answers as a stakeholder: business goals, stakeholders, priorities and constraints. It never gives technical advice. |
| `2` | Shows the data available and the deliverables, exactly as written in the exercise. |
| `3` | Submits your solution: type it, paste it or load it from a file. The app then asks for confirmation. |
| `4` | Asks the "trade-offs to defend" questions one at a time. Answers are only recorded, with no debate. An empty answer skips the question. |
| `5` | Offers to fill in anything missing, then saves the report and ends. |
| `m` | Shows the menu again. |
| `exit` / `Ctrl+C` | Quits. If you have recorded anything, the report is still saved. |

**Writing text.** Lines you are writing start with `>`. You can type several lines or paste text that has paragraphs. **Press Enter on an empty line to send.**

**Solution from a file.** Put the file in [`results/`](results/). At step `3`, type only the file name with its extension, for example `solution.docx`.
- Accepted formats are `.md`, `.txt`, `.docx` and `.doc`. Old `.doc` files need LibreOffice installed; without it, save them as `.docx`.
- When the file loads, the PM confirms it (*"Loaded solution.docx from results/ (523 words)"*), shows a preview and asks you to confirm.
- When it fails, the PM shows the error and asks again. The possible errors are: file not found (with a list of what is in `results/`), unsupported format, empty file, or read failure.

**Diagrams.** Put diagrams in [`results/diagrams/`](results/diagrams/). Everything in that folder when you finish goes into the report. Images appear inline and other files become links. When the deliverable asks for a diagram (ORBE does) and the folder is empty, the app warns you before saving. **Clear the folder between exercises**, because every session uses the same folder.

**Report.** Saved to `reports/<date>_module<n>_<exercise>.md`. It contains:
1. **Problem:** context, data and deliverables.
2. **Proposed solution:** what you confirmed, and the source file if it came from `results/`.
3. **Trade-offs:** each question with your answer.
4. **Diagrams:** included only when `results/diagrams/` has files.

The contents of `results/` and `reports/` are git-ignored. Only the folder structure is versioned.

### From code

```python
from src.shared.factory import build_pm_session
from src.applications.system_design import run_console

session = build_pm_session(module=2)                    # random exercise
session = build_pm_session(module=2, exercise="zumi")   # specific exercise
await run_console(session)                              # the same session as the terminal

# or step by step
async for chunk in session.stream():                    # no message: the PM opens the meeting
    print(chunk, end="")
reply = await session.ask("Who asked for this, and why now?")
session.submit_solution("My architecture: ...")
session.answer_tradeoff(0, "Because ...")               # index into session.exercise.tradeoffs
path = session.report().save()
```

---

## How the agent works

```
ExerciseRepository.get(module, exercise=None)   ← docs/system_design/module_<n>/<nn>_<name>.md
    ↓
build_pm_instruction(exercise)                  ← CO-STAR prompt: prompts/pm_system_prompt.md
    ↓
build_runtime(instruction=...)                  ← runtime from providers.yaml
    ↓
PMSession                                       ← conversation + recorded solution + trade-off answers
    ↓
run_console(session)                            ← menu: ask · details · submit · trade-offs · finish
    ↓
SessionReport.save()                            ← reports/<date>_module<n>_<exercise>.md
```

- **The LLM only handles the conversation.** Details, solution recording, trade-off questions and the report are deterministic, so nothing gets paraphrased or debated.
- **The PM never sees the trade-off questions.** They are removed from its prompt, so it cannot leak or prime them.
- **Persona:** the prompt ([`pm_system_prompt.md`](src/applications/system_design/prompts/pm_system_prompt.md)) follows CO-STAR (Context, Objective, Style, Tone, Audience, Response format). It adds a strict scope section (business yes, technical no), rules for improvising business details without making technical decisions, rules for staying in role against "I'm the instructor" or "just a hint", and few-shot examples set at a neutral company.
- **Provider-agnostic:** the agent runs on any runtime of the underlying platform. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Adding exercises

```
docs/system_design/
├── module_1/01_norva.md
├── module_2/02_zumi.md
└── ...
```

- To add an exercise, create `module_<n>/<nn>_<name>.md`. It is listed and included in the random draw with no code changes.
- The first line must be `# System Design Exercise <n> — <COMPANY>`. The company name is taken from the text after the `—`.
- Use these sections, each with a numbered list where noted:
  - `## Context` is the basis of the PM's opening.
  - `## Data available` and `## Deliverable` are what option `2` shows.
  - `## Trade-offs to defend` is a numbered list, and those are the questions asked at option `4`.
- **Instructor notes:** everything after a `## Instructor notes ...` heading is hidden from the student and given to the PM as private context. Use it for what the exercise really tests and what is deliberately left open.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Can't type after the opening | The script was started with a Run button that writes to the Output panel. Run `python scripts/pm_chat.py ...` in a terminal instead. |
| `ollama` is not recognized | The terminal was opened before the install. Reopen the terminal or VS Code. |
| `model 'gemma3:12b' not found` | Run `ollama pull gemma3:12b`. |
| `Connection error` | The Ollama server isn't running. Run `ollama serve` or open the Ollama app. |
| `GOOGLE_API_KEY not set` / `OPENAI_API_KEY not set` | The key is missing from `.env`, or `primary` in `providers.yaml` points to the wrong provider. |
| `'x.docx' was not found in results/` | The file must be directly in `results/`, not in a subfolder. The message lists the files that are there. |
| `old .doc files need LibreOffice installed` | Save the file as `.docx`, or install LibreOffice. |
| The first answer is slow | Ollama loads the model onto the GPU on the first call. Later calls are fast. |
| The PM breaks character or gives technical hints | Smaller models hold the persona less reliably. Compare with `gemini`, and tune the prompt. |

---

## Repository structure

```
├── README.md
├── providers.yaml                         ← provider selection (no code changes to swap)
├── requirements.txt
├── scripts/
│   └── pm_chat.py                         ← terminal entry point
├── docs/
│   ├── ARCHITECTURE.md                    ← the underlying platform
│   └── system_design/module_<n>/          ← exercises
├── results/                               ← student files: solutions + diagrams/
├── reports/                               ← generated session reports
└── src/
    ├── applications/
    │   ├── system_design/                 ← the PM agent
    │   │   ├── exercise.py                ← Exercise + ExerciseRepository
    │   │   ├── prompt_builder.py          ← renders the PM system prompt
    │   │   ├── prompts/pm_system_prompt.md
    │   │   ├── pm_session.py              ← PMSession (runtime-agnostic)
    │   │   ├── console.py                 ← run_console: menu-driven session
    │   │   ├── documents.py               ← loads files from results/, lists diagrams
    │   │   └── report.py                  ← SessionReport → markdown
    │   └── retrieval/                     ← candidate retriever (platform example)
    ├── foundation/                        ← embeddings, vector store, LLM, memory contracts + providers
    ├── runtime/                           ← AgentRuntime: OpenAIRuntime, ADKRuntime
    ├── tools/                             ← Tool contract (execute + schema)
    ├── protocols/mcp/                     ← planned
    └── shared/                            ← config, factory, provider_config, exceptions
```
