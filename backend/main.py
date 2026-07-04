"""
AgenticOS — FastAPI Backend Server

Provides WebSocket for real-time agent orchestration streaming
and REST endpoints for health checks and configuration.

Updated:
  - Delegates WS handling to AgentWebSocketManager
  - CORS restricted to configurable origins (not wildcard)
  - Structured logging throughout
  - Fixed bare except → specific exception handling
  - RAG pipeline initialized on startup
  - Session IDs for MemorySaver conversation continuity
"""
import json
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from settings import settings
from orchestrator.graph import agent_graph
from orchestrator.state import AgentState
from langchain_core.messages import HumanMessage
from simulation import run_agentic_simulation
from services.websocket_manager import AgentWebSocketManager

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    logger.info("AgenticOS Backend Starting...")
    logger.info("Default Model: %s", settings.default_model)
    logger.info(
        "Groq API Key: %s",
        "Configured" if settings.groq_api_key else "Missing (DEMO mode active)",
    )

    # Initialize RAG pipeline on startup (embeds documents if needed)
    try:
        from rag.pipeline import rag_pipeline
        rag_pipeline.initialize(
            chroma_dir=settings.chroma_persist_dir,
            embedding_model=settings.embedding_model,
        )
    except Exception as e:
        logger.warning("RAG pipeline init failed: %s. Document search will use keyword fallback.", e)

    yield
    logger.info("AgenticOS Backend Shutting Down.")


app = FastAPI(
    title="AgenticOS",
    description="Multi-Agent Operations Intelligence Platform",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── WebSocket Manager singleton ────────────────────────────────────────────────
ws_manager = AgentWebSocketManager(agent_graph=agent_graph, settings=settings)


# ── Schemas ────────────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    model: str | None = None
    session_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    model: str
    api_key_configured: bool
    available_models: dict
    rag_initialized: bool


# ── REST Endpoints ─────────────────────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check — frontend uses this to fetch the live model name."""
    from rag.pipeline import rag_pipeline
    return HealthResponse(
        status="healthy",
        model=settings.default_model,
        api_key_configured=bool(settings.groq_api_key),
        available_models=settings.available_models,
        rag_initialized=rag_pipeline._initialized,
    )


@app.get("/api/models")
async def get_models():
    """Return available LLM models for the model selector."""
    return {"models": settings.available_models, "default": settings.default_model}


# ── WebSocket ──────────────────────────────────────────────────────────────────
@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent orchestration.
    Generates a session_id per connection for MemorySaver continuity.
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info("WebSocket connected — session %s", session_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            user_query = message.get("query", "").strip()
            # Allow client to override session_id for multi-turn continuity
            session_id = message.get("session_id", session_id)

            if not user_query:
                await websocket.send_json({"type": "error", "data": "Empty query"})
                continue

            await websocket.send_json({
                "type": "query_received",
                "data": {"query": user_query, "session_id": session_id},
            })

            # Demo mode: no API key configured
            if not settings.groq_api_key:
                await run_agentic_simulation(websocket, user_query)
                continue

            # Real mode: stream the LangGraph execution
            await ws_manager.handle_query(websocket, user_query, session_id)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected — session %s", session_id)
    except Exception as e:
        logger.error("WebSocket error in session %s: %s", session_id, e, exc_info=True)
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass  # Connection already closed


# ── REST Query (non-streaming, for testing) ────────────────────────────────────
@app.post("/api/query")
async def query_agent(request: QueryRequest):
    """Non-streaming query endpoint — useful for automated testing."""
    import time
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    initial_state: AgentState = {
        "messages": [HumanMessage(content=request.query)],
        "session_id": session_id,
        "user_query": request.query,
        "execution_plan": {},
        "agents_to_spawn": [],
        "agent_results": {},
        "reasoning_trace": [],
        "tool_invocations": [],
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_tool_calls": 0,
        "final_response": "",
        "verification_result": {},
    }

    config = {"configurable": {"thread_id": session_id}}
    result = await agent_graph.ainvoke(initial_state, config=config)
    total_time = (time.time() - start_time) * 1000

    return {
        "response": result.get("final_response", ""),
        "execution_plan": result.get("execution_plan", {}),
        "agents_spawned": result.get("agents_to_spawn", []),
        "reasoning_trace": result.get("reasoning_trace", []),
        "tool_invocations": result.get("tool_invocations", []),
        "verification_result": result.get("verification_result", {}),
        "token_usage": {
            "prompt_tokens": result.get("total_prompt_tokens", 0),
            "completion_tokens": result.get("total_completion_tokens", 0),
            "total_tokens": (
                result.get("total_prompt_tokens", 0)
                + result.get("total_completion_tokens", 0)
            ),
            "tool_calls": result.get("total_tool_calls", 0),
        },
        "total_execution_time_ms": round(total_time, 2),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
