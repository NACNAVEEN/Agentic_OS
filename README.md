# 🤖 AgenticOS — Multi-Agent Operations Intelligence Platform

> A web-based **Agentic AI platform** that autonomously analyzes building operational data using coordinated, dynamically-spawned AI agents. Built with **LangGraph** for orchestration, **Groq API** for ultra-fast open-source LLM inference, **ChromaDB** for semantic RAG, and **React** for real-time visualization.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4-orange)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-19-blue)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## ✨ Key Features

- **🧠 Planner Agent** — Understands intent, decomposes tasks, selects which agents to spawn
- **🏗️ Asset Agent** — Equipment lookup, hierarchy, specifications, relationships
- **🚨 Alarm Agent** — Alarm investigation, correlation, root cause analysis with 2-round ReAct loop
- **⚡ Energy Agent** — Consumption analysis, trends, peak demand, cost estimation
- **📄 Documentation Agent** — **Real semantic RAG** with ChromaDB + sentence-transformers
- **👔 Supervisor Agent** — Synthesizes all results into a grounded, cited response
- **🔍 Verification Agent** — Deterministic hallucination prevention with confidence scoring
- **📊 Real-Time Agent Graph** — React Flow visualization of live agent orchestration
- **💭 Reasoning Transparency** — Every thought, tool call, and decision is visible
- **🔧 Tool Abstraction Layer** — Mock tools swap to real APIs (BACnet/SCADA/CMMS) with zero agent changes
- **📈 Gantt Timeline** — Execution time visualization across all agents
- **🧪 Test Suite** — 25+ unit and integration tests

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend | React 19 + Vite |
| Agent Graph | React Flow (@xyflow/react) |
| Markdown Rendering | react-markdown (XSS-safe) |
| Backend | FastAPI + WebSocket |
| Orchestration | LangGraph 0.4 |
| Memory | LangGraph MemorySaver (conversation continuity) |
| LLM | Groq API (Llama 3.3 70B default) |
| Vector DB | ChromaDB + sentence-transformers |
| Configuration | Pydantic BaseSettings |
| Testing | pytest + pytest-asyncio |

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/AgenticOS/AgenticOS.git
cd AgenticOS
echo "GROQ_API_KEY=gsk_your_key" > .env
docker-compose up --build
```

Open **http://localhost:5173** — backend starts at **http://localhost:8000**

### Option 2: Local Development

```bash
# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate         # Windows
# source venv/bin/activate      # Mac/Linux
pip install -r requirements.txt
echo "GROQ_API_KEY=gsk_your_key" > .env
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Demo Mode (No API Key)

If `GROQ_API_KEY` is not set, the system automatically enters **Demo Mode** with pre-authored realistic responses.

---

## 🧪 Running Tests

```bash
# Run the full test suite (no API key needed)
pytest tests/ -v
```

---

## 📁 Documentation

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System design, data flow, future API integration |
| [LLM Evaluation Report](docs/llm_evaluation_report.md) | Model comparison and methodology |
| [Setup Guide](docs/setup_guide.md) | Local development guide |
| [Deployment Guide](docs/deployment.md) | Docker and production deployment |

## video Walkthrough demo
**Presentation link**: https://www.loom.com/share/844ab5693e0340dab21b95f19f9ea9c4
**Demonstration link**: 
https://www.loom.com/share/73a24c2e2bef4f2299926635e4ad79b8 

---

## 🏗️ Project Structure

```
AgenticOS/
├── backend/
│   ├── agents/              # Planner, Supervisor, Verification, Specialized agents
│   ├── orchestrator/        # LangGraph state machine (graph.py, state.py)
│   ├── tools/               # BaseTool ABC + 10 mock tools (schema + cache)
│   ├── rag/                 # ChromaDB semantic search pipeline
│   ├── services/            # LLM factory (DI), WebSocket manager
│   ├── data/                # JSON fixtures + document corpus
│   └── main.py              # FastAPI app
├── frontend/
│   └── src/
│       ├── components/      # AgentGraph, ReasoningPanel, ExecutionPlanPanel, etc.
│       └── App.jsx
├── tests/                   # pytest test suite
├── docs/                    # Architecture, LLM eval, setup, deployment
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 📝 License

MIT © AgenticOS
