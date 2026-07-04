# AgenticOS — Deployment Guide

## Quick Start: Docker (Recommended)

### Prerequisites
- Docker Desktop installed and running
- A Groq API key from [console.groq.com](https://console.groq.com)

### 1. Configure Environment

```bash
# Clone the repository
git clone https://github.com/AgenticOS/AgenticOS.git
cd AgenticOS

# Create your .env file
echo "GROQ_API_KEY=gsk_your_key_here" > .env
```

### 2. Start with Docker Compose

```bash
docker-compose up --build
```

**First run note**: The backend will download the `all-MiniLM-L6-v2` embedding model (~90MB) and embed the 3 documents into ChromaDB. This takes approximately 30–60 seconds on first startup. Subsequent startups load the persisted index instantly.

### 3. Access the Application

| Service | URL |
|---|---|
| Frontend UI | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Health | http://localhost:8000/api/health |

---

## Local Development (No Docker)

### Prerequisites
- Python 3.11+
- Node.js 20+
- A Groq API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# Start the backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**First-run note**: On the first startup, ChromaDB will embed 3 documents from `backend/data/documents/`. This prints:
```
INFO RAG: Embedding documents on first run (this takes ~10s)...
INFO RAG: Embedded N chunks into ChromaDB.
```

Subsequent startups will print:
```
INFO RAG: Loaded existing index with N chunks.
```

### Frontend Setup

```bash
cd frontend

# Install dependencies (includes react-markdown)
npm install

# Start development server
npm run dev
```

The frontend runs at http://localhost:5173.

---

## Demo Mode (No API Key)

If `GROQ_API_KEY` is not set in `.env`, AgenticOS automatically runs in **Demo Mode**.

In Demo Mode:
- The backend starts normally
- WebSocket connections work normally
- Queries trigger the simulation engine (`simulation.py`) instead of real LLM calls
- Pre-written responses demonstrate the full agent flow with realistic timing
- Token counts will show `0` — real metrics require a live API key

The health endpoint will indicate demo mode:
```json
{"status": "healthy", "api_key_configured": false, ...}
```

---

## Running Tests

```bash
cd AgenticOS

# Run the full test suite
pytest tests/ -v

# Run only tool tests (no API key needed)
pytest tests/test_tools.py -v

# Run agent tests (no API key needed)
pytest tests/test_agents.py -v

# Run graph tests (no API key needed)
pytest tests/test_graph.py -v
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | Yes (for real mode) | `""` | Your Groq API key |
| `DEFAULT_MODEL` | No | `llama-3.3-70b-versatile` | LLM model to use |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB storage directory |
| `HOST` | No | `0.0.0.0` | Backend bind host |
| `PORT` | No | `8000` | Backend bind port |
| `CORS_ORIGINS` | No | `["http://localhost:5173"]` | Allowed frontend origins |

---

## Troubleshooting

### ChromaDB fails to initialize

```
WARNING RAG pipeline init failed. Document search will use keyword fallback.
```

**Solution**: Install missing packages:
```bash
pip install chromadb sentence-transformers
```

### WebSocket connection refused

Ensure the backend is running on port 8000. Check for port conflicts:
```bash
# Windows
netstat -ano | findstr :8000

# Mac/Linux
lsof -i :8000
```

### CORS error in browser console

Add your frontend URL to `CORS_ORIGINS` in `.env`:
```
CORS_ORIGINS=["http://localhost:5173","http://your-frontend-url.com"]
```

### Frontend react-markdown not found

```bash
cd frontend && npm install
```

---

## Production Deployment Checklist

- [ ] Set `GROQ_API_KEY` in production secrets (not in a committed `.env`)
- [ ] Restrict `CORS_ORIGINS` to your production frontend domain
- [ ] Mount a persistent volume for `CHROMA_PERSIST_DIR`
- [ ] Add a reverse proxy (nginx/Caddy) in front of both services
- [ ] Enable HTTPS on the frontend and backend
- [ ] Set up process monitoring (systemd/PM2/supervisord)
