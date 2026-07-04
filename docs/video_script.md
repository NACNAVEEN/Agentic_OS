# 🎬 AgenticOS — Complete Step-by-Step Video Walkthrough Script

> **Target Length**: 8–12 minutes  
> **Resolution**: 1920×1080  
> **Format**: Screen Capture + Audio Narration  

---

## ⏱️ Step 1: System Overview & Problem Statement (0:00 – 1:15)

**💻 WHAT TO SHOW ON SCREEN:**
- Open browser to **http://localhost:5173** (Dark glassmorphic AgenticOS UI).

**🎙️ WHAT TO SAY:**
> *"Hello everyone! Welcome to the technical demonstration of **AgenticOS** — a multi-agent AI operations intelligence platform designed for smart building management.*
>
> *Building operations engineers deal with fragmented data streams daily — active alarms in building management systems, energy meter logs, equipment specifications, and technical SOP manuals. 
>
> AgenticOS solves this by deploying a coordinated team of specialized AI agents built on LangGraph. Instead of relying on a single monolithic chatbot, AgenticOS dynamically decomposes tasks, executes parallel specialist tools, synthesizes findings, and verifies grounding in real-time."*

---

## ⏱️ Step 2: Architecture & LangGraph State Machine (1:15 – 2:45)

**💻 WHAT TO SHOW ON SCREEN:**
- Switch to VS Code and show `docs/architecture.md` (System Architecture & Sequence Flow).

**🎙️ WHAT TO SAY:**
> *"Let’s examine the architectural workflow. AgenticOS uses a **LangGraph StateGraph** state machine operating across five distinct stages:*
>
> 1. ***Planner Node***: Receives user queries, decomposes intent into numbered steps, and selects which specialist agents to spawn.
> 2. ***Parallel Specialist Nodes***: Asset Agent, Alarm Agent, Energy Agent, and Documentation Agent execute in parallel.
> 3. ***State Reducers***: Parallel node outputs are combined safely into shared state using custom reducers (`_merge_dicts`, `_concat_lists`).
> 4. ***Supervisor Node***: Synthesizes specialist findings into a cohesive Markdown response with recommendations.
> 5. ***Verification Node***: A deterministic grounding engine checks all numerical claims and asset IDs against raw tool outputs, returning a confidence score.
>
> *Every agent event streams to the UI via an asynchronous FastAPI WebSocket connection (`/ws/agent`)."*

---

## ⏱️ Step 3: Live Demo — Alarm Investigation & Verification (2:45 – 5:30)

**💻 WHAT TO SHOW ON SCREEN:**
- Switch to `http://localhost:5173`.
- Click the suggestion button: **"Investigate the high temperature alarm on AHU-01"**.
- Watch the **Agent Execution Graph** nodes highlight in real-time (`Planner` → `Asset`, `Alarm`, `Docs` → `Supervisor`).
- After completion, click the **"Verification"** tab in the right-side Reasoning Console.

**🎙️ WHAT TO SAY:**
> *"Now let's run a live investigation: 'Investigate the high temperature alarm on AHU-01'.*
>
> *Notice how the Planner immediately generates a 4-step execution plan and spawns three specialist agents simultaneously. On the center canvas, you can see nodes move from Standby to Running to Completed.*
>
> *The Supervisor returns a detailed report: AHU-01 is experiencing a critical high supply air temperature alarm caused by a stuck chilled water valve.*
>
> *Now look at the **Verification Tab** on the right. In critical facility operations, AI hallucinations cannot be tolerated. Our Verification Agent automatically extracted 14 claims — including temperatures and asset identifiers — and cross-referenced every single claim against the raw tool output data. It scored **100% VERIFIED** with zero ungrounded claims, achieved at **zero extra LLM latency cost**!"*

---

## ⏱️ Step 4: Live Demo — Semantic Vector RAG Search (5:30 – 6:45)

**💻 WHAT TO SHOW ON SCREEN:**
- Type in the chat box: **"What is BACnet?"** and press Enter.
- Show that only the **Docs Agent** node spawns in the graph.

**🎙️ WHAT TO SAY:**
> *"Let's test our semantic RAG engine. I'll ask: 'What is BACnet?'.*
>
> *Notice that the Planner intelligently spawns **only** the Documentation Agent. Instead of simple keyword substring matching, the Documentation Agent queries a local **ChromaDB vector database** loaded with `sentence-transformers` embeddings (`all-MiniLM-L6-v2`) to retrieve exact technical manual excerpts."*

---

## ⏱️ Step 5: Code Tour & Future API Integration (6:45 – 8:45)

**💻 WHAT TO SHOW ON SCREEN:**
- Switch to VS Code and show `backend/tools/base_tool.py` and `backend/services/llm_factory.py`.

**🎙️ WHAT TO SAY:**
> *"Let me highlight the code architecture behind our tool abstractions and future enterprise integrations:*
>
> 1. ***Tool Abstraction Layer (`base_tool.py`)***: Every tool inherits from `BaseTool` with JSON schema parameter validation. If an LLM hallucinates extra parameter keys, `_validate_params()` automatically strips them before execution.
> 2. ***Future API Integration Code***: Because tools inherit from `BaseTool`, swapping our mock tools for live **BACnet/IP gateways**, **InfluxDB time-series databases**, or **Maximo CMMS ticketing APIs** requires **zero changes to agent code**. We simply create a `BACnetAssetTool` implementing `BaseTool`, update our tool list, and the entire agent graph runs seamlessly against live BMS hardware.
> 3. ***LLM Dependency Injection (`llm_factory.py`)***: Agent logic is completely decoupled from model providers via Pydantic `BaseSettings`."*

---

## ⏱️ Step 6: Test Suite, Assumptions & Conclusion (8:45 – 10:00)

**💻 WHAT TO SHOW ON SCREEN:**
- Open terminal and run: `pytest tests/ -v`.
- Show all 42 tests passing in ~2 seconds.

**🎙️ WHAT TO SAY:**
> *"Finally, automated testing and system quality. Our test suite includes **42 unit and integration tests** covering tool validation, planner parsing, verification grounding logic, and LangGraph routing.*
>
> *All 42 tests pass in under 2 seconds without requiring an API key.*
>
> ***Assumptions & Roadmap***:
> *Telemetry currently runs on structured JSON fixtures. For enterprise production, future milestones include multi-tenant checkpointer persistence, BACnet/IP REST adapters, and Human-in-the-Loop approval for write actions like valve adjustments.*
>
> *Thank you for reviewing AgenticOS!"*

---

## 📋 Pre-Recording Checklist
- [ ] Backend running at `http://localhost:8000/api/health`
- [ ] Frontend running at `http://localhost:5173`
- [ ] Screen resolution: 1920×1080
- [ ] Run test suite prior to recording: `pytest tests/ -v`
