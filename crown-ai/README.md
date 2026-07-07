# 👑 Crown AI - Full-Stack Multi-Agent Command Dashboard

Crown AI is a high-fidelity, secure, and modular full-stack multi-agent system engineered around Google's **Agent Development Kit (ADK)** workflow design principles and the **Model Context Protocol (MCP)** server architecture.

The system features six collaborative, specialized agents coordinated by a central Orchestrator that decomposes, refines, researches, and schedules complex user queries (such as exam study planners, calendar allocations, and project task management) through a deterministic workflow graph.

---

## 🏛️ Core Concepts Applied

### 1. ADK Multi-Agent System
The engine models a graph-based multi-agent execution pipeline. Agents represent nodes connected by directed edges.
- **Orchestrator Agent**: Pre-processes inputs, initiates the pipeline, and aggregates the final outputs.
- **Planner Agent**: Decomposes the prompt into structured execution phases.
- **Task Optimization Agent**: Rewrites and polishes steps using SMART criteria.
- **Research Agent**: Scans database facts to inject context.
- **Exam/Study Agent**: Generates educational study flashcards and reviews.
- **Life Scheduler Agent**: Allocates calendar blocks and writes details to the scheduler registry.

```
START -> Orchestrator -> Planner -> TaskOptimization -> Research -> ExamStudy -> LifeScheduler -> Orchestrator (Final Output)
```

### 2. Model Context Protocol (MCP) Server
An integrated local MCP server exposes custom tools/skills to the agents:
- `search_knowledge`: Searches concepts and definitions.
- `optimize_task`: Standardizes raw subtasks to SMART targets.
- `schedule_event`: Books time slots into the calendar.
- `generate_study_deck`: Compiles study flashcards.

### 3. Security Features (Validation & Safe Execution)
- **Prompt Sanitization**: Blocks query requests containing OS injections (`rm -rf`, `format`, `powershell`, etc.).
- **Directory Boundaries**: Limits all file read/write operations strictly within the `crown-ai` project workspace.
- **MCP Schema Enforcement**: Sanitizes and structures arguments before tool execution.
- **Code Execution Safeguards**: Blocks code scripts attempting to import dangerous modules (`os`, `subprocess`, `sys`).

### 4. Agent Skills & CLI Tools
A comprehensive CLI utility `cli.py` allows command-line scheduling, tools query, and safety validations without launching the full web dashboard.

---

## 📂 Project Structure

```
crown-ai/
├── backend/
│   ├── adk_core.py       # Core ADK classes (Context, Agent, Workflow)
│   ├── agents.py         # Specialized agent behaviors & executions
│   ├── cli.py            # Terminal command runner & query validator
│   ├── config.py         # Port, allowed folders, and schema limits
│   ├── main.py           # FastAPI Web Server & WebSocket managers
│   ├── mcp_server.py     # MCP compliant tools and handlers
│   ├── security.py       # Security checks & sanitization libraries
│   └── requirements.txt  # Python packages requirements
├── frontend/
│   ├── index.html        # Premium dashboard html structure
│   ├── styles.css        # Sleek dark mode Obsidian-purple styles
│   └── app.js            # Client-side WS logs & API controllers
├── calendar.json         # Simulated calendar database (generated)
├── study_decks/          # Study deck json exports (generated)
└── README.md             # Setup guide and documentation
```

---

## 🚀 Getting Started

### 📋 Prerequisites
- Python 3.10 or higher installed.

### 🔧 Installation
1. Clone the repository into your workspace:
   ```bash
   cd c:/Users/hp/Desktop/crown-ai
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

### 💻 Running the CLI Tool
You can invoke the agent team directly from your terminal:
- **Execute a workflow task**:
  ```bash
  python -m backend.cli run "Create a daily study block schedule for my Machine Learning exam on Friday."
  ```
- **List registered MCP Tools**:
  ```bash
  python -m backend.cli tools
  ```
- **Validate prompt safety**:
  ```bash
  python -m backend.cli validate "rm -rf /"
  ```

### 🖥️ Running the Web Dashboard (Localhost:8000)
1. Start the FastAPI backend server:
   ```bash
   python -m backend.main
   ```
2. Access the premium dashboard at [http://localhost:8000](http://localhost:8000) in your web browser.

---

## 🎬 Antigravity Demo Walkthrough (End-to-End Workflow)

Here is exactly what happens when you input: *"Schedule deep study blocks for my Machine Learning exam on Friday and search ML topics"* in the Crown AI Dashboard:

1. **Security Guard Screening**:
   - The query undergoes validation in `backend/security.py`. Since no shell commands or traversals are found, it receives a green `[VALIDATED]` check.
2. **Orchestrator Booting**:
   - The Orchestrator initiates the workflow graph, logging the action to the WebSocket stream and lighting up its indicator on the UI.
3. **Task Decomposing**:
   - The Planner Agent intercepts the prompt, identifies it as an educational/exam context, and outputs a 4-phase execution plan.
4. **SMART Optimization**:
   - The Task Optimization Agent takes the 4 phases and calls the MCP `optimize_task` tool. Each phase is rewritten into a specific, measurable unit.
5. **Knowledge Injection**:
   - The Research Agent calls the MCP `search_knowledge` tool for "machine learning". It retrieves definitions of Supervised/Unsupervised structures and appends it to the context.
6. **Deck Synthesis**:
   - The Exam/Study Agent triggers the MCP `generate_study_deck` tool, creating four flashcards and exporting `machine_learning_deck.json` to the filesystem.
7. **Time Blocking**:
   - The Life Scheduler Agent processes the calendar commands, booking study sessions in `calendar.json` using the `schedule_event` tool.
8. **Orchestration Compilation**:
   - The Orchestrator collects all findings, formats them into a Markdown summary, and sends it to the UI report viewer, reverting all agent badges to `IDLE`.
